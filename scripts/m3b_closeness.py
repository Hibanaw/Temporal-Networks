"""M3b (H6b): does the static closeness ranking agree with the temporal one?

Static: harmonic closeness on the aggregated graph (outgoing distances for
directed data), unweighted and weighted (distance = 1 / number of events).
Temporal: harmonic temporal closeness averaged over several start times
(see temporal_paths_placeholder). Agreement is Kendall tau-b and the overlap of
the top 10% nodes. P1 null samples keep the static graph and so the static
ranking, and only change the temporal one.

Outputs
  results/e/m3b_<dataset>_nodes.csv   per-node static and temporal closeness (real)
  results/e_summary.csv               rows for this dataset (replaced on rerun)

Usage
  python scripts/m3b_closeness.py --dataset PS --n-null 20
"""
import argparse
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.stats import kendalltau

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import e_datasets  # noqa: E402
from nullmodels import timestamp_shuffle  # noqa: E402
from summary import upsert_summary  # noqa: E402
from temporal_paths_placeholder import temporal_closeness  # noqa: E402


def static_closeness(events, nodes, directed):
    w = events.groupby(["u", "v"]).size()
    g = nx.DiGraph() if directed else nx.Graph()
    g.add_nodes_from(nodes)
    for (u, v), c in w.items():
        if g.has_edge(u, v):  # undirected: (u, v) and (v, u) rows add up
            g[u][v]["weight"] += c
        else:
            g.add_edge(u, v, weight=c)
    for _, _, d in g.edges(data=True):
        d["dist"] = 1.0 / d["weight"]
    # networkx harmonic centrality sums distances *to* a node; reverse for outgoing.
    h = g.reverse(copy=False) if directed else g
    unweighted = nx.harmonic_centrality(h)
    weighted = nx.harmonic_centrality(h, distance="dist")
    return (np.array([unweighted[n] for n in nodes]), np.array([weighted[n] for n in nodes]))


def top_overlap(a, b, frac=0.1):
    k = max(1, int(round(frac * len(a))))
    ta = set(np.argsort(-a, kind="stable")[:k])
    tb = set(np.argsort(-b, kind="stable")[:k])
    return len(ta & tb) / k


def compare(static_u, static_w, temporal):
    return {
        "m3b_tau_unweighted": kendalltau(static_u, temporal).statistic,
        "m3b_tau_weighted": kendalltau(static_w, temporal).statistic,
        "m3b_top10_overlap_unweighted": top_overlap(static_u, temporal),
        "m3b_top10_overlap_weighted": top_overlap(static_w, temporal),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=["PS", "CM"], default="PS")
    ap.add_argument("--n-null", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    ds = e_datasets.load(args.dataset)
    ev = ds.events
    nodes = sorted(set(ev["u"]) | set(ev["v"]))
    static_u, static_w = static_closeness(ev, nodes, ds.directed)
    temporal = temporal_closeness(ev, nodes, ds.closeness_starts, ds.directed)
    real = compare(static_u, static_w, temporal)
    real["m3b_n_nodes"] = len(nodes)
    real["m3b_n_starts"] = len(ds.closeness_starts)

    null = []
    for k in range(args.n_null):
        nev = timestamp_shuffle(ev, seed=args.seed + 2000 + k)
        null.append(compare(static_u, static_w,
                            temporal_closeness(nev, nodes, ds.closeness_starts, ds.directed)))
        print(f"null {k + 1}/{args.n_null}", flush=True)
    null_df = pd.DataFrame(null)

    (ROOT / "results" / "e").mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"node": nodes, "static_unweighted": static_u, "static_weighted": static_w,
                  "temporal": temporal}).to_csv(ROOT / "results" / "e" / f"m3b_{ds.name}_nodes.csv", index=False)
    rows = [(ds.name, m, v,
             null_df[m].mean() if m in null_df else np.nan,
             null_df[m].std() if m in null_df else np.nan) for m, v in real.items()]
    upsert_summary(ROOT / "results" / "e_summary.csv", rows)
    print(pd.DataFrame(rows, columns=["dataset", "metric", "value", "null_mean", "null_std"])
          .to_string(index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()
