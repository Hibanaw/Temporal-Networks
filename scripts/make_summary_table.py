"""Build hypothesis-specific summaries with one definition of effect.

Every finite effect is value - null_mean in the underlying metric's units.
H1 has no null: its effect is undefined and its value is descriptive only.
H7 stores actual peak delays (seconds) and exposes real/null ratios separately.
Different metrics, grids and conditioning still prevent a universal ranking.
"""
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]


def build_cross_table(allrows):
    rows = []
    for h in range(1, 8):
        hypothesis = f'H{h}'
        references = ['P1', 'P2'] if h in (6, 7) else [{1: 'none', 4: 'P3a'}.get(h, 'P1')]
        for reference in references:
            for ds in ['PS', 'CM', 'CIT']:
                applicable = h in (1, 4) if ds == 'CIT' else h != 4
                metrics = {
                    1: 'H1_window_sensitivity_density' + ('_directed' if ds == 'CIT' else ''),
                    2: 'm2_burstiness', 3: 'm2_adjacent_jaccard', 4: 'pa_alpha__P3a',
                    5: 'm4_adj_nmi_mean_' + ('w15min_g1' if ds == 'PS' else 'w7D_g1'),
                    6: f'm3a_R_vs{reference}',
                    7: 'm3c_' + ('b0.05_D4h' if ds == 'PS' else 'b0.2_D336h') + f'_peak_time_s_vs{reference}',
                }
                metric = metrics[h]
                found = allrows[(allrows.dataset == ds) & (allrows.metric == metric)]
                row = dict(hypothesis=hypothesis, dataset=ds, reference=reference, metric=metric,
                           status='missing' if applicable else 'inapplicable',
                           value=np.nan, null_mean=np.nan, null_std=np.nan, effect=np.nan, ratio=np.nan,
                           effect_definition='value_minus_null_mean',
                           value_unit='seconds' if h == 7 else 'dimensionless',
                           estimate_type='descriptive_no_null' if h == 1 else
                                         ('conditional_major_outbreak_peak' if h == 7 else 'null_contrast'),
                           source='')
                if applicable and len(found):
                    f = found.iloc[-1]
                    value, mean = float(f.value), float(f.null_mean)
                    effect = value - mean if np.isfinite(value) and np.isfinite(mean) else np.nan
                    ratio = value / mean if h == 7 and np.isfinite(value) and np.isfinite(mean) and mean > 0 else np.nan
                    row.update(status='measured' if np.isfinite(value) else 'undefined', value=value,
                               null_mean=mean, null_std=f.null_std, effect=effect, ratio=ratio, source=f.source)
                rows.append(row)
    return pd.DataFrame(rows)


def main():
    frames = []
    for owner in 'abcde':
        path = ROOT / f'results/{owner}_summary.csv'
        if path.exists():
            g = pd.read_csv(path); g['source'] = str(path.relative_to(ROOT)); frames.append(g)
    allrows = pd.concat(frames, ignore_index=True)
    allrows.to_csv(ROOT / 'results/all_summary.csv', index=False)
    out = build_cross_table(allrows)
    out.to_csv(ROOT / 'results/cross_network_summary.csv', index=False)
    displays = []
    for title, part, column in [
        ('Descriptive H1 (different grids/definitions; do not rank)', out[out.hypothesis == 'H1'], 'value'),
        ('Null contrasts: effect = value - null_mean (hypothesis-specific units)', out[out.hypothesis.isin(['H2','H3','H4','H5','H6'])], 'effect'),
        ('H7 conditional peak ratios (distinct from the seconds-valued effect column)', out[out.hypothesis == 'H7'], 'ratio')]:
        table = part.pivot(index=['hypothesis','reference'], columns='dataset', values=column).reindex(columns=['PS','CM','CIT'])
        displays.append(title + '\n\n' + table.fillna('--').to_markdown())
    (ROOT / 'results/cross_network_summary.md').write_text('\n\n'.join(displays) +
        '\n\nH1 effect is undefined because there is no null. H7 value/null_mean/effect are peak delays in seconds; ratio is separate.\n'
        'H7 compares network-specific seed populations conditional on at least 5% infected. No common overall sensitivity scale is implied.\n')
    print(out.to_string(index=False))

if __name__ == '__main__': main()
