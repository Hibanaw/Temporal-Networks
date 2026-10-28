"""Earliest-arrival and temporal closeness, using D's path convention.

Convention (same as D's earliest_arrival in run.py):
- The source is active at t_start. An event (u, v, t) can be used only if u
  was reached strictly before t; v is then reached at time t. So a path
  cannot take two hops within one timestamp, and the result does not depend
  on the order of events that share a timestamp. Events at exactly t_start
  cannot be used.
- Undirected data: each event can be used in both directions.
- Latency of v from source s with start time t_start = arrival(v) - t_start.

This version computes all sources in one pass over the events; to be merged
into D's paths.py.
"""
import numpy as np


def earliest_arrival(events, nodes, t_start, directed):
    """Earliest arrival times from every node as source, starting at t_start.

    Returns an array A of shape (len(nodes), len(nodes)) with A[v, s] the
    arrival time at v from source s (inf if unreachable, t_start for v = s).
    Rows are targets so the per-event update reads contiguous memory.
    """
    index = {n: i for i, n in enumerate(nodes)}
    ev = events[events["t"] > t_start].sort_values("t", kind="stable")
    us = ev["u"].map(index).to_numpy()
    vs = ev["v"].map(index).to_numpy()
    ts = ev["t"].to_numpy()
    arr = np.full((len(nodes), len(nodes)), np.inf)
    np.fill_diagonal(arr, t_start)
    for u, v, t in zip(us, vs, ts):
        from_u = arr[u] < t
        if not directed:
            from_v = arr[v] < t
            np.minimum(arr[u], np.where(from_v, t, np.inf), out=arr[u])
        np.minimum(arr[v], np.where(from_u, t, np.inf), out=arr[v])
    return arr


def temporal_closeness(events, nodes, starts, directed):
    """Harmonic temporal closeness of every node as a source, averaged over start times.

    C(s) = mean over t_start of 1/(N-1) * sum_{v != s} 1 / latency(s -> v),
    with unreachable targets contributing 0.
    """
    n = len(nodes)
    total = np.zeros(n)
    for t_start in starts:
        latency = earliest_arrival(events, nodes, t_start, directed) - t_start
        np.fill_diagonal(latency, np.inf)
        total += (1.0 / latency).sum(axis=0) / (n - 1)
    return total / len(starts)
