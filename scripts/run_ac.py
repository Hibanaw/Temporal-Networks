"""Run A M1 and C M2a/M2b; full and elapsed-time half periods; nested P1 20/60.

These are explicitly reconstructed C definitions, not the unavailable original code.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from e_datasets import load
from aggregate import analyse, graph_metrics, GRIDS
from stats import activity, persistence
from nullmodels import timestamp_shuffle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nulls', type=int, default=60)
    args = ap.parse_args()
    out = ROOT/'results'/'ac'; out.mkdir(parents=True, exist_ok=True)
    arows, crows, raw = [], [], []
    for name in ('PS', 'CM'):
        for period in ('full', 'first', 'second'):
            ds = load(name, period)
            series, means, sens = analyse(ds.events, GRIDS[name], ds.directed)
            series.to_csv(out/f'm1_{name}_{period}_windows.csv', index=False)
            means.to_csv(out/f'm1_{name}_{period}_means.csv')
            nodes=sorted(set(ds.events.u)|set(ds.events.v))
            static=graph_metrics(ds.events,nodes,ds.directed)
            pd.DataFrame([static]).to_csv(out/f'm1_{name}_{period}_static.csv',index=False)
            for key, val in static.items():
                arows.append(dict(dataset=name,period=period,metric='m1_static_'+key,value=val,
                                  null_mean=np.nan,null_std=np.nan))
            for key, val in sens.items():
                arows.append(dict(dataset=name, period=period, metric='H1_window_sensitivity_'+key,
                                  value=val, null_mean=np.nan, null_std=np.nan))
            width = 3600 if name == 'PS' else 7*86400
            for iteration in range(-1, args.nulls):
                ev = ds.events if iteration == -1 else timestamp_shuffle(ds.events, seed=iteration)
                act, gaps = activity(ev, ds.directed, 20 if name == 'PS' else None)
                per, jac = persistence(ev, width, ds.directed, 20 if name == "PS" else None)
                raw.append(dict(dataset=name, period=period, iteration=iteration, **act, **per))
                if iteration == -1:
                    pd.DataFrame({'iet_s': gaps}).to_csv(out/f'm2a_{name}_{period}_iets.csv', index=False)
                    pd.DataFrame({'jaccard': jac}).to_csv(out/f'm2b_{name}_{period}_jaccard.csv', index=False)
            print(name, period, 'complete', flush=True)
    raw = pd.DataFrame(raw)
    raw.to_csv(out/'m2_per_network.csv', index=False)
    for (name, period), group in raw.groupby(['dataset', 'period']):
        for n in sorted(set([20, args.nulls])):
            null = group[(group.iteration>=0)&(group.iteration<n)]
            real = group[group.iteration==-1].iloc[0]
            for key in ('burstiness', 'memory', 'repeated_tie_fraction', 'repeated_event_fraction', 'mean_lifetime_s', 'adjacent_jaccard'):
                crows.append(dict(dataset=name, period=period, nulls=n, metric='m2_'+key,
                                  value=real[key], null_mean=null[key].mean(), null_std=null[key].std()))
    aa, cc = pd.DataFrame(arows), pd.DataFrame(crows)
    aa.to_csv(out/'a_robustness.csv', index=False); cc.to_csv(out/'c_robustness.csv', index=False)
    cols = ['dataset', 'metric', 'value', 'null_mean', 'null_std']
    aa[aa.period=='full'][cols].to_csv(ROOT/'results/a_summary.csv', index=False)
    cc[(cc.period=='full')&(cc.nulls==20)][cols].to_csv(ROOT/'results/c_summary.csv', index=False)
    (out/'protocol.json').write_text(json.dumps(dict(null_seed_base=0, nulls=args.nulls,
        split='elapsed-time midpoint', iet='dyad; PS 20s contact episodes collapsed',
        m1='fixed period node universe; empty and trailing windows included',
        C_status='reconstructed implementation; historical report numbers require comparison'), indent=2))

if __name__ == '__main__':
    main()
