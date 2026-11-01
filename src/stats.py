"""M2a/M2b definitions. IETs are within dyads, never concatenated across ties.

PS contiguous 20-second contact records collapse to episode onsets for IETs;
M2b retains all records. Memory pools adjacent IET pairs within each dyad.
Empty windows participate in Jaccard; two empty edge sets give NaN.
"""
import numpy as np
from aggregate import windows


def records(events, directed=False, contact_step=None):
    """Canonicalize without deleting coincident events created by a null model.

    Raw duplicates were removed by src.io. P1 can create coincident events;
    retaining them preserves its exact per-dyad event counts.
    """
    ev=events[["u", "v", "t"]].copy()
    if not directed:
        u=np.minimum(ev.u,ev.v);v=np.maximum(ev.u,ev.v)
        ev["u"],ev["v"]=u,v
    ev=ev.sort_values(["u", "v", "t"]).reset_index(drop=True)
    if contact_step is not None:
        gaps=ev.groupby(["u", "v"]).t.diff()
        ev=ev[gaps.isna() | (gaps>contact_step)]
    return ev


def activity(events, directed=False, contact_step=None):
    ev = records(events, directed, contact_step)
    gaps = ev.groupby(["u", "v"]).t.diff()
    previous = gaps.groupby([ev.u, ev.v]).shift(1)
    paired = gaps.notna() & previous.notna()
    left, right = previous[paired].to_numpy(), gaps[paired].to_numpy()
    intervals = gaps.dropna().to_numpy()
    if len(intervals):
        mu, sd = intervals.mean(), intervals.std()
        b = (sd-mu)/(sd+mu) if sd+mu else np.nan
    else:
        b = np.nan
    memory = np.corrcoef(left, right)[0, 1] if len(left)>1 and np.std(left)>0 and np.std(right)>0 else np.nan
    return dict(burstiness=b, memory=memory, n_intervals=len(intervals)), intervals


def persistence(events, width, directed=False, contact_step=None):
    ev = records(events, directed)
    ties = ev.groupby(["u", "v"]).t.agg(["size", "min", "max"])
    edge_sets = [set(g[["u", "v"]].itertuples(index=False, name=None)) for _, g in windows(ev, width)]
    jac = [len(a & b)/len(a | b) if a | b else np.nan for a,b in zip(edge_sets[:-1], edge_sets[1:])]
    finite = [x for x in jac if np.isfinite(x)]
    episode_counts = records(events, directed, contact_step).groupby(["u", "v"]).size()
    return dict(repeated_tie_fraction=float((episode_counts>1).mean()),
                repeated_event_fraction=1-len(ties)/len(ev),
                mean_lifetime_s=float((ties["max"]-ties["min"]).mean()),
                adjacent_jaccard=float(np.mean(finite)) if finite else np.nan), jac
