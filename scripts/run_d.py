"""Member D: M3a (time-respecting reachability) and M3c (event-driven SIR) on PS and CM,
against P1 (timestamp shuffle) and P2 (edge randomisation), 20 samples each.

  python scripts/run_d.py [--datasets PS CM] [--workers 8] [--seeds 200]

Writes results/d/m3a_<DS>.csv, results/d/m3c_<DS>.csv and results/d_summary.csv.
"""
import argparse
import itertools
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from e_datasets import load  # noqa: E402
from nullmodels import edge_shuffle, timestamp_shuffle  # noqa: E402
from paths import reachability, static_reachability  # noqa: E402
from spreading import outbreak_summary, simulate_sir  # noqa: E402

OUT = ROOT / "results" / "d"
N_NULL = 20
MASTER_SEED = 5253
OUTBREAK = 0.05  # a "major outbreak" infects at least 5% of the nodes

# (beta per contact record / message, infectious duration in seconds); first entry is the primary setting.
SIR_GRID = {
    "PS": [(0.05, 4 * 3600), (0.02, 4 * 3600), (0.10, 4 * 3600), (0.05, 3600)],
    "CM": [(0.20, 14 * 86400), (0.05, 14 * 86400), (0.50, 14 * 86400), (0.20, 3 * 86400)],
}


def label(beta, duration):
    return f"b{beta:g}_D{duration // 3600}h"


def build(events, mode, iteration, directed):
    if mode == "Real":
        return events
    seed = iteration
    if mode == "P1":
        return timestamp_shuffle(events, seed=seed)
    return edge_shuffle(events, seed=seed, directed=directed)


def work(task):
    name, mode, iteration = task
    ds = load(name)
    events = build(ds.events, mode, iteration, ds.directed)
    events = events.sort_values("t", kind="stable").reset_index(drop=True)
    nodes = sorted(set(ds.events["u"]) | set(ds.events["v"]))
    index = {n: i for i, n in enumerate(nodes)}
    m3a = []
    static = static_reachability(events, nodes, ds.directed)
    for t_start in ds.closeness_starts:
        frac, latency = reachability(events, nodes, t_start, ds.directed)
        m3a.append(dict(dataset=name, mode=mode, iteration=iteration, t_start=t_start,
                        reach=frac, mean_latency=latency, static_reach=static))
    u = events["u"].map(index).to_numpy()
    v = events["v"].map(index).to_numpy()
    t = events["t"].to_numpy()
    n_events = len(t)
    # The same random positions are used in every network: seed k starts at the sender of the
    # event at a random position in the first 70% of that network's own event stream.
    rng = np.random.default_rng(MASTER_SEED)
    positions = rng.integers(0, int(0.7 * n_events), size=ARGS.seeds)
    flips = rng.random(ARGS.seeds) < 0.5
    m3c = []
    for beta, duration in SIR_GRID[name]:
        for k, pos in enumerate(positions):
            source = v[pos] if (flips[k] and not ds.directed) else u[pos]
            sim_rng = np.random.default_rng([MASTER_SEED, k])
            inf = simulate_sir(u, v, t, len(nodes), source, t[pos], beta, duration, ds.directed, sim_rng)
            size, peak, half = outbreak_summary(inf, t[pos], duration)
            m3c.append(dict(dataset=name, mode=mode, iteration=iteration, setting=label(beta, duration),
                            seed=k, final_size=size, peak_time=peak, half_time=half))
    return m3a, m3c


def summarise(m3a, m3c, name):
    rows = []

    def add(metric, real, p1, p2):
        for nul, vals in (("P1", p1), ("P2", p2)):
            rows.append(dict(dataset=name, metric=f"{metric}_vs{nul}", value=real,
                             null_mean=np.mean(vals), null_std=np.std(vals, ddof=1)))

    a = m3a.groupby(["mode", "iteration"]).agg(reach=("reach", "mean"), lat=("mean_latency", "mean"),
                                               static=("static_reach", "first")).reset_index()
    a["R"] = a["reach"] / a["static"]
    for col, metric in (("reach", "m3a_reach"), ("static", "m3a_static_reach"), ("R", "m3a_R"),
                        ("lat", "m3a_mean_latency_s")):
        add(metric, float(a[a["mode"] == "Real"][col].iloc[0]),
            a[a["mode"] == "P1"][col].to_numpy(), a[a["mode"] == "P2"][col].to_numpy())
    for setting, part in m3c.groupby("setting"):
        major = part["final_size"] >= OUTBREAK
        part = part.assign(major=major.astype(float))
        # peak and half-time are averaged over major outbreaks only (NaN if none occurred)
        per_net = part.groupby(["mode", "iteration"]).apply(
            lambda g: pd.Series(dict(
                size=g["final_size"].mean(), p_major=g["major"].mean(),
                peak=g.loc[g["major"] == 1, "peak_time"].mean(),
                half=g.loc[g["major"] == 1, "half_time"].mean())), include_groups=False).reset_index()
        for col, metric in (("size", "final_size"), ("p_major", "p_major"), ("peak", "peak_time_s"),
                            ("half", "half_time_s")):
            add(f"m3c_{setting}_{metric}", float(per_net[per_net["mode"] == "Real"][col].iloc[0]),
                per_net[per_net["mode"] == "P1"][col].to_numpy(), per_net[per_net["mode"] == "P2"][col].to_numpy())
    return pd.DataFrame(rows)


ARGS = None


def main():
    global ARGS
    p = argparse.ArgumentParser()
    p.add_argument("--datasets", nargs="+", default=["PS", "CM"])
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--seeds", type=int, default=200)
    p.add_argument("--nulls", type=int, default=N_NULL)
    ARGS = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    summaries = []
    for name in ARGS.datasets:
        tasks = [(name, "Real", 0)] + [(name, m, i) for m in ("P1", "P2") for i in range(ARGS.nulls)]
        # a fork-based pool inherits ARGS; heavy tasks first
        with Pool(ARGS.workers) as pool:
            results = pool.map(work, tasks, chunksize=1)
        m3a = pd.DataFrame(list(itertools.chain.from_iterable(r[0] for r in results)))
        m3c = pd.DataFrame(list(itertools.chain.from_iterable(r[1] for r in results)))
        m3a.to_csv(OUT / f"m3a_{name}.csv", index=False)
        m3c.to_csv(OUT / f"m3c_{name}.csv", index=False)
        summaries.append(summarise(m3a, m3c, name))
        print(name, "done", flush=True)
    pd.concat(summaries).to_csv(ROOT / "results" / "d_summary.csv", index=False)


if __name__ == "__main__":
    main()
