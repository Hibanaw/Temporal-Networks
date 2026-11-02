"""Run M1 on processed PS/CM. No randomisation/null model is required.

Default: full observation, fixed node set, complete-window means.
Use --robustness to add first/second halves (same global node set).
Use --active-nodes for a separately named active-node diagnostic run.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import pandas as pd
import networkx as nx
from src.io import load_processed
from src.m1_aggregate import aggregate, graph_metrics, window_metrics

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = {
    'PS': [300, 900, 1800, 3600, 7200, 14400, 28800, 86400],
    'CM': [3600, 10800, 21600, 43200, 86400, 259200, 604800, 2592000],
}
METRICS = ['density', 'mean_degree', 'mean_in_degree', 'mean_out_degree',
           'clustering', 'n_components', 'component_fraction',
           'largest_component_fraction', 'active_fraction']


def summarise(windows):
    rows = []
    keys = ['dataset', 'period', 'node_basis', 'delta_seconds']
    for key, group in windows.groupby(keys, sort=False):
        for policy in ['complete_only', 'include_partial']:
            selected = group.loc[group.complete] if policy == 'complete_only' else group
            for metric in METRICS:
                valid = selected[metric].dropna()
                rows.append(dict(zip(keys, key)) | {
                    'window_policy': policy, 'metric': metric,
                    'n_windows': len(selected), 'n_defined': len(valid),
                    'n_empty': int((selected.event_count == 0).sum()),
                    'n_partial': int((~selected.complete).sum()),
                    'mean': valid.mean(), 'std': valid.std(ddof=1),
                    'median': valid.median(), 'min': valid.min(), 'max': valid.max(),
                })
    return pd.DataFrame(rows)


def sensitivity(summary):
    """Dimensionless range / mean of window-scale means, NOT significance.
    Undefined when fewer than 2 valid scales; all-zero curves return zero.
    """
    rows = []
    chosen = summary.loc[summary.window_policy == 'complete_only']
    for key, group in chosen.groupby(['dataset', 'period', 'node_basis', 'metric'], sort=False):
        valid = group.dropna(subset=['mean'])
        values = valid['mean']
        value = float('nan')
        if len(values) >= 2:
            denom = float(values.abs().mean())
            value = float((values.max()-values.min())/denom) if denom else 0.0
        rows.append(dict(zip(['dataset','period','node_basis','metric'],key)) | {
            'sensitivity': value, 'n_scales': len(values),
            'min_windows_per_scale': int(valid.n_windows.min()) if len(valid) else 0,
        })
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', choices=['PS', 'CM', 'both'], default='both')
    parser.add_argument('--robustness', action='store_true')
    parser.add_argument('--active-nodes', action='store_true')
    args = parser.parse_args()
    basis = 'active' if args.active_nodes else 'fixed'
    run_name = 'robustness' if args.robustness else 'main'
    output = ROOT / 'results/m1' / f'{run_name}_{basis}'
    output.mkdir(parents=True, exist_ok=True)
    datasets = ['PS', 'CM'] if args.dataset == 'both' else [args.dataset]
    started = time.monotonic()
    all_windows, all_static, inputs = [], [], {}
    for dataset in datasets:
        source = ROOT / 'data/processed' / dataset
        events, nodes = load_processed(source)
        directed = dataset == 'CM'
        resolution = 20 if dataset == 'PS' else 1
        start = int(events.t.min())
        stop = int(events.t.max()) + resolution
        midpoint = start + ((stop-start)//(2*resolution))*resolution
        periods = {'full': (start, stop)}
        if args.robustness:
            periods.update({'first_half': (start, midpoint), 'second_half': (midpoint, stop)})
        inputs[dataset] = {'start': start, 'stop_exclusive': stop,
                           'resolution_seconds': resolution,
                           'events_sha256': hashlib.sha256((source/'events.csv').read_bytes()).hexdigest(),
                           'nodes_sha256': hashlib.sha256((source/'nodes.csv').read_bytes()).hexdigest()}
        frames, static_rows = [], []
        for period, (left, right) in periods.items():
            part = events.loc[(events.t >= left) & (events.t < right)]
            graph = aggregate(part, nodes.id, directed=directed)
            static_rows.append({'dataset': dataset, 'period': period, 'node_basis': basis,
                                'event_count': len(part), **graph_metrics(graph, basis)})
            for width in WINDOWS[dataset]:
                frame = window_metrics(part, nodes.id, width, left, right, directed, basis)
                frame.insert(0, 'period', period)
                frame.insert(0, 'dataset', dataset)
                frames.append(frame)
                print(f'{dataset} | {period} | {width}s | '
                      f'{int(frame.complete.sum())} complete + '
                      f'{int((~frame.complete).sum())} partial windows', flush=True)
        frame = pd.concat(frames, ignore_index=True)
        # Dataset-specific files allow PS and CM to be run separately safely.
        frame.to_csv(output / f'{dataset}_windows.csv', index=False)
        summary = summarise(frame)
        summary.to_csv(output / f'{dataset}_summary.csv', index=False)
        sensitivity(summary).to_csv(output / f'{dataset}_sensitivity.csv', index=False)
        pd.DataFrame(static_rows).to_csv(output / f'{dataset}_full_aggregate.csv', index=False)
        all_windows.append(frame)
        all_static.extend(static_rows)
    config = {'generated_utc': datetime.now(timezone.utc).isoformat(),
              'datasets': datasets, 'windows_seconds': WINDOWS, 'inputs': inputs,
              'node_basis': basis, 'robustness': args.robustness,
              'window_alignment': 'first timestamp of each period',
              'observation_stop': 'last timestamp + one source resolution step',
              'primary_summary': 'unweighted mean across complete non-overlapping windows, including empty windows',
              'partial_tail': 'saved; excluded from primary means; include_partial diagnostic also saved',
              'PS_gaps': 'chronological gaps retained; absence of events is not proof of observed absence of contact',
              'CM_components': 'weak; these are not temporally reachable components',
              'CM_clustering': 'NetworkX unweighted directed (Fagiolo)',
              'mean_degree': 'PS ordinary degree; CM in+out degree; isolates included for fixed basis',
              'null_model': 'not applicable to M1 under PLAN v3',
              'python': platform.python_version(), 'networkx': nx.__version__,
              'numpy': np.__version__, 'pandas': pd.__version__,
              'elapsed_seconds': time.monotonic()-started}
    label = 'both' if args.dataset == 'both' else args.dataset
    (output / f'run_{label}.json').write_text(json.dumps(config, indent=2))
    if args.dataset == 'both':
        combined = summarise(pd.concat(all_windows, ignore_index=True))
        effects = sensitivity(combined)
        if not args.robustness and basis == 'fixed':
            chosen = effects.loc[(effects.period == 'full') & effects.metric.isin(
                ['density', 'mean_degree', 'clustering', 'component_fraction',
                 'largest_component_fraction'])].copy()
            chosen['metric'] = 'H1_window_sensitivity_' + chosen.metric
            chosen = chosen.rename(columns={'sensitivity':'value'})
            chosen['null_mean'], chosen['null_std'] = np.nan, np.nan
            chosen[['dataset','metric','value','null_mean','null_std']].to_csv(
                ROOT / 'results/m1/A_summary.csv', index=False)
    print(f'Finished in {time.monotonic()-started:.1f}s. Results: {output}', flush=True)


if __name__ == '__main__':
    main()
