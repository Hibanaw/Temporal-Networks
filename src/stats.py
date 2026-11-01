"""M2a/M2b definitions. IETs are within dyads, never concatenated across ties.

PS contiguous 20-second contact records collapse to episode onsets for IETs;
M2b retains all records. Memory pools adjacent IET pairs within each dyad.
Empty windows participate in Jaccard; two empty edge sets give NaN.
"""
import numpy as np
from aggregate import windows
from nullmodels import prepare_events


def activity(events, directed=False, contact_step=None):
    ev = prepare_events(events, directed, contact_step)
    intervals, left, right = [], [], []
    for _, g in ev.groupby(["u", "v"]):
        gaps = np.diff(g.t.to_numpy(dtype=float))
        intervals.extend(gaps)
        left.extend(gaps[:-1]); right.extend(gaps[1:])
    gaps = np.asarray(intervals)
    if len(gaps):
        mu, sd = gaps.mean(), gaps.std()
        b = (sd-mu)/(sd+mu) if sd+mu else np.nan
    else:
        b = np.nan
    memory = np.corrcoef(left, right)[0, 1] if len(left)>1 and np.std(left)>0 and np.std(right)>0 else np.nan
    return dict(burstiness=b, memory=memory, n_intervals=len(gaps)), gaps


def persistence(events, width, directed=False, contact_step=None):
    ev = prepare_events(events, directed)
    ties = ev.groupby(["u", "v"]).t.agg(["size", "min", "max"])
    edge_sets = [set(g[["u", "v"]].itertuples(index=False, name=None)) for _, g in windows(ev, width)]
    jac = [len(a & b)/len(a | b) if a | b else np.nan for a,b in zip(edge_sets[:-1], edge_sets[1:])]
    finite = [x for x in jac if np.isfinite(x)]
    episode_counts = prepare_events(events, directed, contact_step).groupby(["u", "v"]).size()
    return dict(repeated_tie_fraction=float((episode_counts>1).mean()),
                repeated_event_fraction=1-len(ties)/len(ev),
                mean_lifetime_s=float((ties["max"]-ties["min"]).mean()),
                adjacent_jaccard=float(np.mean(finite)) if finite else np.nan), jac
