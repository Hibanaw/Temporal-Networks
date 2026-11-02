"""C sensitivity checks promised in Methods (full period, P1 seeds 0-19).

  1. H3: adjacent-window Jaccard for several window widths, real vs P1.
  2. H2: burstiness and memory on raw 20-s PS records vs merged contact episodes.
  3. H2: inter-event time distribution: quantiles and an exponential/lognormal AIC
     comparison, real vs one P1 realization (seed 0) for the CCDF figure.

Outputs go to results/ac/c_*.csv. Uses the same stats/null functions as run_ac.py.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from e_datasets import load  # noqa: E402
from stats import activity, persistence  # noqa: E402
from nullmodels import timestamp_shuffle  # noqa: E402

NULLS = 20
WIDTHS = {'PS': [900, 1800, 3600, 7200], 'CM': [86400, 3*86400, 7*86400, 14*86400]}
STEP = {'PS': 20, 'CM': None}


def aic_fits(x):
    """Exponential vs lognormal (both with loc=0) by maximum likelihood and AIC."""
    x = x[x > 0]
    lam = 1 / x.mean()
    ll_exp = np.sum(st.expon.logpdf(x, scale=1/lam))
    s, _, scale = st.lognorm.fit(x, floc=0)
    ll_ln = np.sum(st.lognorm.logpdf(x, s, 0, scale))
    return dict(n=len(x), aic_exponential=2 - 2*ll_exp, aic_lognormal=4 - 2*ll_ln,
                lognormal_sigma=s, lognormal_median_s=scale)


def main():
    out = ROOT / 'results' / 'ac'
    widths, defs, dist = [], [], []
    for name in ('PS', 'CM'):
        ds = load(name, 'full')
        nulls = [timestamp_shuffle(ds.events, seed=i) for i in range(NULLS)]
        for width in WIDTHS[name]:
            real = persistence(ds.events, width, ds.directed, STEP[name])[0]['adjacent_jaccard']
            null = [persistence(ev, width, ds.directed, STEP[name])[0]['adjacent_jaccard'] for ev in nulls]
            widths.append(dict(dataset=name, width_s=width, real=real, null_mean=np.mean(null),
                               null_std=np.std(null, ddof=1), delta=real - np.mean(null)))
            print(name, width, round(real, 4), round(np.mean(null), 4), flush=True)
        # Event definition: raw records (no merging) vs contact episodes. CM has no episodes.
        for label, step in ([('raw records', None), ('episodes', 20)] if name == 'PS' else [('messages', None)]):
            r = activity(ds.events, ds.directed, step)[0]
            n = [activity(ev, ds.directed, step)[0] for ev in nulls]
            for key in ('burstiness', 'memory'):
                vals = [x[key] for x in n]
                defs.append(dict(dataset=name, events=label, metric=key, real=r[key],
                                 null_mean=np.mean(vals), null_std=np.std(vals, ddof=1),
                                 delta=r[key] - np.mean(vals)))
        for kind, ev in (('real', ds.events), ('P1', nulls[0])):
            x = activity(ev, ds.directed, STEP[name])[1]
            pd.DataFrame({'iet_s': x}).to_csv(out / f'c_iet_{name}_{kind}.csv', index=False)
            q = np.quantile(x, [.5, .9, .99])
            dist.append(dict(dataset=name, kind=kind, mean_s=x.mean(), median_s=q[0], p90_s=q[1],
                             p99_s=q[2], cv=x.std()/x.mean(), **aic_fits(x)))
    pd.DataFrame(widths).to_csv(out / 'c_jaccard_widths.csv', index=False)
    pd.DataFrame(defs).to_csv(out / 'c_event_definition.csv', index=False)
    pd.DataFrame(dist).to_csv(out / 'c_iet_distribution.csv', index=False)
    print(pd.DataFrame(widths).to_string(index=False))
    print(pd.DataFrame(defs).to_string(index=False))
    print(pd.DataFrame(dist).to_string(index=False))


if __name__ == '__main__':
    main()
