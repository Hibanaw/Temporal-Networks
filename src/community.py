"""Community detection on static and snapshot networks (M4, H5).

A partition is a dict {node: community}. Community ids are arbitrary within
each call, so every comparison goes through NMI, which ignores labels.
Snapshot NMIs are computed on the nodes the two partitions share, because
the set of active nodes changes from one snapshot to the next.
"""
import igraph as ig
import leidenalg as la
import numpy as np
import pandas as pd
from sklearn.metrics import normalized_mutual_info_score


def to_igraph(events):
    """Weighted undirected graph; edge weight = number of events between u and v.

    Only nodes with at least one event appear. Vertex attribute "id" holds the
    original node id.
    """
    ev = events[events["u"] != events["v"]]
    u = ev["u"].to_numpy()
    v = ev["v"].to_numpy()
    pairs = pd.DataFrame({"a": np.minimum(u, v), "b": np.maximum(u, v)})
    w = pairs.value_counts().reset_index(name="weight")
    nodes = np.unique(np.concatenate([w["a"].to_numpy(), w["b"].to_numpy()]))
    index = {n: i for i, n in enumerate(nodes.tolist())}
    edges = [(index[a], index[b]) for a, b in zip(w["a"].tolist(), w["b"].tolist())]
    g = ig.Graph(n=len(nodes), edges=edges, directed=False)
    g.vs["id"] = nodes.tolist()
    g.es["weight"] = w["weight"].astype(float).tolist()
    return g


def leiden(g, resolution=1.0, seed=0):
    """Leiden on weighted modularity with resolution gamma (RB configuration model)."""
    if g.vcount() == 0:
        return {}
    p = la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight",
                          resolution_parameter=resolution, n_iterations=-1, seed=seed)
    return dict(zip(g.vs["id"], p.membership))


def static_partition(events, resolution=1.0, seed=0):
    """Partition of the fully aggregated network."""
    return leiden(to_igraph(events), resolution, seed)


def snapshot_windows(events, width, t0=None, min_events=1):
    """Split events into windows [t0 + k*width, t0 + (k+1)*width).

    Windows with fewer than `min_events` events (nights, edges of the
    observation period) are dropped. Returns a list of (window_start, events).
    """
    t0 = int(events["t"].min()) if t0 is None else t0
    k = (events["t"] - t0) // width
    return [(t0 + int(key) * width, grp) for key, grp in events.groupby(k, sort=True)
            if len(grp) >= min_events]


def snapshot_partitions(windows, resolution=1.0, seed=0):
    """Independent Leiden partition of each window."""
    return [leiden(to_igraph(ev), resolution, seed) for _, ev in windows]


def multislice_partitions(windows, resolution=1.0, interslice_weight=1.0, seed=0):
    """Multislice modularity (Mucha et al. 2010) via leidenalg.

    Copies of a node in consecutive windows are joined with weight
    `interslice_weight`, so community labels are consistent across windows
    and can be tracked directly.
    """
    graphs = [to_igraph(ev) for _, ev in windows]
    memberships, _ = la.find_partition_temporal(
        graphs, la.RBConfigurationVertexPartition, interslice_weight=interslice_weight,
        vertex_id_attr="id", weight_attr="weight", n_iterations=-1, seed=seed,
        resolution_parameter=resolution)
    return [dict(zip(g.vs["id"], m)) for g, m in zip(graphs, memberships)]


def nmi(p, q, min_common=2):
    """NMI between two partitions on their common nodes; NaN if too few."""
    common = [n for n in p if n in q]
    if len(common) < min_common:
        return np.nan
    return normalized_mutual_info_score([p[n] for n in common], [q[n] for n in common])


def adjacent_nmi(partitions, starts=None, width=None):
    """NMI between consecutive snapshots.

    Element k compares snapshot k with snapshot k-1, so element 0 is NaN.
    If `starts` and `width` are given, pairs that are not back-to-back in time
    (e.g. across a night) are NaN too.
    """
    out = [np.nan]
    for k in range(1, len(partitions)):
        if starts is not None and starts[k] - starts[k - 1] != width:
            out.append(np.nan)
        else:
            out.append(nmi(partitions[k - 1], partitions[k]))
    return out


def nmi_to_reference(partitions, reference):
    """NMI of each snapshot partition against one fixed partition (static or ground truth)."""
    return [nmi(p, reference) for p in partitions]


def self_consistency(windows, resolution=1.0, seeds=(0, 1)):
    """NMI between two Leiden runs with different seeds on each window.

    This is the noise floor of the algorithm: snapshot-to-snapshot NMI can
    only be read as reorganisation if it is clearly below this.
    """
    a = snapshot_partitions(windows, resolution, seeds[0])
    b = snapshot_partitions(windows, resolution, seeds[1])
    return [nmi(p, q) for p, q in zip(a, b)]


def n_communities(partition):
    return len(set(partition.values()))
