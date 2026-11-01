"""Member D: time-respecting reachability (M3a).

Convention (shared with E's temporal_paths_placeholder.py): the source is active
at t_start; an event (u, v, t) is usable only if u was reached strictly before t,
and v is then reached at t. Two hops within one timestamp are therefore
impossible and the result does not depend on the order of simultaneous events.
Undirected data: every event works in both directions.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import shortest_path


def earliest_arrival(events, nodes, t_start, directed):
    """All-source earliest arrival times.

    Returns A of shape (N, N), A[v, s] = arrival time at v from source s
    (inf if unreachable, t_start for v = s). Events at t <= t_start are ignored.
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


def reachability(events, nodes, t_start, directed):
    """Fraction of ordered pairs (s, v), s != v, with a time-respecting path from
    t_start, and the mean latency (arrival - t_start) over reachable pairs."""
    n = len(nodes)
    latency = earliest_arrival(events, nodes, t_start, directed) - t_start
    np.fill_diagonal(latency, np.inf)
    reached = np.isfinite(latency)
    count = int(reached.sum())
    mean_latency = float(latency[reached].mean()) if count else float("nan")
    return count / (n * (n - 1)), mean_latency


def static_reachability(events, nodes, directed):
    """Fraction of ordered pairs connected in the aggregated static graph."""
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    u = events["u"].map(index).to_numpy()
    v = events["v"].map(index).to_numpy()
    adj = coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n)).tocsr()
    dist = shortest_path(adj, method="D", directed=directed, unweighted=True)
    np.fill_diagonal(dist, np.inf)
    return float(np.isfinite(dist).sum()) / (n * (n - 1))
