"""M4 (H5): do communities reorganise over time, and does a static partition hide it?

For each snapshot window: Leiden partition, then NMI with the previous window,
with the static partition, and with the ground-truth labels if the dataset has
them (PS classes, teachers excluded). The same is done on P1 null samples
(C's timestamp_shuffle). A second Leiden run with another seed gives the
algorithm's noise floor; the multislice partition (Mucha 2010) gives labels
that can be tracked across windows. Both are computed on the real data only.

Outputs (tag = w<width>_g<gamma>)
  results/e/m4_<dataset>_series_<tag>.csv       per-window metrics: real, null mean, null std
  results/e/m4_<dataset>_multislice_<tag>.csv   tracked community of every node (--multislice-out)
  results/e_summary.csv                         rows for this dataset and tag (replaced on rerun)

Usage
  python scripts/m4_communities.py --dataset PS --width 15min
  python scripts/m4_communities.py --dataset CM --width 7D
"""
import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import e_datasets  # noqa: E402
from community import (adjacent_nmi, multislice_partitions, n_communities, nmi,  # noqa: E402
                       nmi_to_reference, self_consistency, snapshot_partitions,
                       snapshot_windows, static_partition)
from nullmodels import timestamp_shuffle  # noqa: E402
from summary import upsert_summary  # noqa: E402

SERIES_COLS = ["n_nodes", "n_comms", "adj_nmi", "static_nmi", "class_nmi", "self_nmi", "ms_adj_nmi"]
OUT = ROOT / "results" / "e"


def analyse(events, labels, width, gamma, omega, seed, min_events, t0, full=True):
    """Per-window series and scalar summaries.

    full=False skips the self-consistency and multislice runs (used for null samples).
    """
    windows = snapshot_windows(events, width, t0=t0, min_events=min_events)
    starts = [s for s, _ in windows]
    static = static_partition(events, gamma, seed)
    snaps = snapshot_partitions(windows, gamma, seed)
    nan = [np.nan] * len(windows)
    ms = multislice_partitions(windows, gamma, omega, seed) if full else None
    series = pd.DataFrame({
        "start": starts,
        "n_nodes": [len(p) for p in snaps],
        "n_comms": [n_communities(p) for p in snaps],
        "adj_nmi": adjacent_nmi(snaps, starts, width),
        "static_nmi": nmi_to_reference(snaps, static),
        "class_nmi": nmi_to_reference(snaps, labels) if labels else nan,
        "self_nmi": self_consistency(windows, gamma, (seed, seed + 1)) if full else nan,
        "ms_adj_nmi": adjacent_nmi(ms, starts, width) if full else nan,
    })
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        scalars = {f"m4_{c}_mean": np.nanmean(series[c]) for c in SERIES_COLS}
    scalars["m4_static_class_nmi"] = nmi(static, labels) if labels else np.nan
    scalars["m4_static_n_comms"] = n_communities(static)
    scalars["m4_n_snapshots"] = len(windows)
    return series, scalars, ms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=["PS", "CM"], default="PS")
    ap.add_argument("--width", default=None, help="window width, e.g. 15min, 1h, 7D")
    ap.add_argument("--gamma", type=float, default=1.0, help="Leiden resolution parameter")
    ap.add_argument("--omega", type=float, default=1.0, help="interslice weight for multislice partition")
    ap.add_argument("--n-null", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--multislice-out", action="store_true", help="also save the tracked multislice labels")
    args = ap.parse_args()

    ds = e_datasets.load(args.dataset)
    width_label = args.width or {"PS": "15min", "CM": "7D"}[ds.name]
    width = int(pd.Timedelta(width_label).total_seconds())
    t0 = int(ds.events["t"].min())
    run = dict(labels=ds.labels, width=width, gamma=args.gamma, omega=args.omega,
               min_events=ds.min_events, t0=t0)

    series, real, ms = analyse(ds.events, seed=args.seed, **run)
    null_series, null_scalars = [], []
    for k in range(args.n_null):
        s, sc, _ = analyse(timestamp_shuffle(ds.events, seed=args.seed + 1000 + k), seed=args.seed, full=False,
                           **run)
        # P1 keeps the multiset of timestamps, so the windows must be the same.
        assert s["start"].tolist() == series["start"].tolist()
        null_series.append(s[SERIES_COLS].to_numpy(dtype=float))
        null_scalars.append(sc)

    stack = np.stack(null_series)
    with warnings.catch_warnings():
        # Columns that are NaN in every sample (first window, window after a gap, labels absent).
        warnings.simplefilter("ignore", RuntimeWarning)
        for i, c in enumerate(SERIES_COLS):
            series[f"{c}_null_mean"] = np.nanmean(stack[:, :, i], axis=0)
            series[f"{c}_null_std"] = np.nanstd(stack[:, :, i], axis=0)

    tag = f"w{width_label}_g{args.gamma:g}"
    OUT.mkdir(parents=True, exist_ok=True)
    series.to_csv(OUT / f"m4_{ds.name}_series_{tag}.csv", index=False)
    if args.multislice_out:
        pd.DataFrame([(s, n, c) for s, p in zip(series["start"], ms) for n, c in p.items()],
                     columns=["start", "node", "community"]).to_csv(
            OUT / f"m4_{ds.name}_multislice_{tag}.csv", index=False)

    null_df = pd.DataFrame(null_scalars)
    rows = [(ds.name, f"{m}_{tag}", v, null_df[m].mean(), null_df[m].std()) for m, v in real.items()]
    upsert_summary(ROOT / "results" / "e_summary.csv", rows)
    print(pd.DataFrame(rows, columns=["dataset", "metric", "value", "null_mean", "null_std"])
          .to_string(index=False, float_format="%.3f"))


if __name__ == "__main__":
    main()
