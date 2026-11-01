"""M1 fixed-universe snapshots, including empty windows and trailing windows.

All nodes seen in the selected observation period remain in every snapshot.
CM clustering uses the undirected projection; degree/density retain direction.
Sensitivity is (max - min) / mean of window-averaged metrics across widths.
"""
import networkx as nx
import numpy as np
import pandas as pd

GRIDS = {"PS": [300, 900, 1800, 3600, 7200, 14400, 28800, 86400],
         "CM": [3600, 21600, 43200, 86400, 3*86400, 7*86400, 14*86400, 30*86400]}
METRICS = ["density", "mean_total_degree", "clustering", "components", "lcc_fraction"]


def windows(events, width, t0=None, t1=None):
    t0 = int(events.t.min()) if t0 is None else int(t0)
    t1 = int(events.t.max()) if t1 is None else int(t1)
    groups = {int(k): g for k, g in events.groupby((events.t-t0)//width)}
    for k in range((t1-t0)//width+1):
        yield t0+k*width, groups.get(k, events.iloc[:0])


def graph_metrics(events, nodes, directed=False):
    g = nx.DiGraph() if directed else nx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(events[["u", "v"]].itertuples(index=False, name=None))
    und = g.to_undirected() if directed else g
    comps = list(nx.connected_components(und))
    return dict(density=nx.density(g), mean_total_degree=sum(dict(g.degree()).values())/len(nodes),
                clustering=nx.average_clustering(und), components=len(comps),
                lcc_fraction=max(map(len, comps), default=0)/len(nodes))


def analyse(events, widths, directed=False):
    nodes = sorted(set(events.u) | set(events.v))
    rows = []
    for width in widths:
        for start, ev in windows(events, width):
            rows.append(dict(width_s=width, start=start, n_events=len(ev),
                             **graph_metrics(ev, nodes, directed)))
    series = pd.DataFrame(rows)
    means = series.groupby("width_s")[METRICS].mean()
    sensitivity = (means.max()-means.min())/means.mean().replace(0, np.nan)
    return series, means, sensitivity
