"""Member A: simple binary aggregation and non-overlapping time windows.

All event selections use [start, stop). PS interval-end timestamps are kept
as supplied; aggregation does not infer the order of simultaneous events.
"""
from dataclasses import dataclass
from numbers import Integral
import numpy as np
import networkx as nx
import pandas as pd


@dataclass(frozen=True)
class Window:
    index: int
    start: int
    stop: int
    nominal_stop: int
    complete: bool
    events: pd.DataFrame


def aggregate(events, nodes, directed=False):
    """Return an unweighted Graph/DiGraph containing every supplied node.

    Repeated interactions become one edge. Does not modify input data.
    `nodes` is an iterable of IDs, e.g. nodes_frame['id'].
    """
    ids = list(nodes)
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate node IDs')
    if not {'u', 'v', 't'}.issubset(events.columns):
        raise ValueError('Missing event columns')
    if not set(events.u).union(events.v) <= set(ids):
        raise ValueError('Event endpoint missing from supplied node set')
    if (events.u == events.v).any():
        raise ValueError('Remove self-loops before aggregation')
    graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_nodes_from(ids)
    graph.add_edges_from(events[['u', 'v']].itertuples(index=False, name=None))
    return graph


def snapshots(events, delta_seconds, start, stop):
    """Yield all non-overlapping windows, including empty and partial tail.

    Bounds must be explicit, so halves of an observation use the intended
    boundaries rather than moving them to the first/last surviving event.
    A partial tail is flagged, never silently treated as a full window.
    """
    for value in [delta_seconds, start, stop]:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError('Window width and bounds must be integers')
    if delta_seconds <= 0 or start >= stop:
        raise ValueError('Require delta_seconds > 0 and start < stop')
    if not events.t.is_monotonic_increasing:
        raise ValueError('Events must be sorted by timestamp')
    timestamps = events.t.to_numpy()
    for index, left in enumerate(range(start, stop, delta_seconds)):
        nominal_right = left + delta_seconds
        right = min(nominal_right, stop)
        i, j = np.searchsorted(timestamps, [left, right], side='left')
        yield Window(index, left, right, nominal_right, nominal_right <= stop,
                     events.iloc[i:j])


def graph_metrics(graph, node_basis='fixed'):
    """Binary structural metrics; directed graphs use Fagiolo clustering
    and weak connected components. Mean directed degree is IN + OUT.

    Fixed basis includes isolated nodes in averages and component counts.
    Active basis is the induced graph of non-isolated nodes. An empty active
    graph has undefined averages/density/fractions (NaN), not invented zeros.
    """
    if node_basis not in {'fixed', 'active'}:
        raise ValueError('node_basis must be fixed or active')
    if graph.is_multigraph() or nx.number_of_selfloops(graph):
        raise ValueError('Expected simple graph without self-loops')
    if node_basis == 'active':
        graph = graph.subgraph([u for u, k in graph.degree() if k > 0])
    n, m = graph.number_of_nodes(), graph.number_of_edges()
    active = sum(k > 0 for _, k in graph.degree())
    components = (nx.weakly_connected_components(graph) if graph.is_directed()
                  else nx.connected_components(graph))
    sizes = [len(c) for c in components]
    nan = float('nan')
    return {
        'n_nodes': n, 'n_active': active, 'n_edges': m,
        'density': nx.density(graph) if n else nan,
        'mean_degree': sum(k for _, k in graph.degree()) / n if n else nan,
        'mean_in_degree': m / n if n and graph.is_directed() else nan,
        'mean_out_degree': m / n if n and graph.is_directed() else nan,
        'clustering': nx.average_clustering(graph, weight=None, count_zeros=True) if n else nan,
        'n_components': len(sizes),
        'component_fraction': len(sizes) / n if n else nan,
        'largest_component_size': max(sizes, default=0),
        'largest_component_fraction': max(sizes, default=0) / n if n else nan,
        'active_fraction': active / n if n else nan,
    }


def window_metrics(events, nodes, delta_seconds, start, stop, directed=False,
                   node_basis='fixed'):
    ids = list(nodes)
    rows = []
    for window in snapshots(events, delta_seconds, start, stop):
        graph = aggregate(window.events, ids, directed=directed)
        rows.append({
            'delta_seconds': delta_seconds, 'window_index': window.index,
            'start': window.start, 'stop': window.stop,
            'complete': window.complete,
            'coverage_fraction': (window.stop-window.start)/delta_seconds,
            'event_count': len(window.events), 'node_basis': node_basis,
            **graph_metrics(graph, node_basis=node_basis),
        })
    return pd.DataFrame(rows)
