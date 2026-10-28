"""Member E's figures, drawn from the saved tables in results/ (no recomputation).

  e_m4_ps_timeseries   PS snapshot NMIs over both days (main setting), real vs P1
  e_m4_cm_timeseries   CM snapshot NMIs over the observation period (main setting)
  e_m4_sensitivity     real minus P1-null NMI against gamma, one line per window width
  e_m3b_rank_scatter   static vs temporal closeness rank, PS and CM

Each figure is written to figures/ as PDF and PNG, and the PDF is copied to
report/figures/.

Usage: python scripts/plot_e.py
"""
import re
import shutil
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
REPORT_FIG = ROOT / "report" / "figures"
MAIN = {"PS": "w15min_g1", "CM": "w7D_g1"}
NAMES = {"PS": "Primary School", "CM": "CollegeMsg"}

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # categorical slots 1-3, in fixed order
COLOR_REAL, COLOR_NULL, COLOR_SELF = SERIES
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
TAG = re.compile(r"^(m4_\w+?)_w(.+)_g([\d.]+)$")

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "savefig.bbox": "tight", "pdf.fonttype": 42})


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=180)
    plt.close(fig)
    REPORT_FIG.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIG / f"{name}.pdf", REPORT_FIG / f"{name}.pdf")


def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.spines[["left", "bottom"]].set_color(INK_SECONDARY)
    ax.tick_params(colors=INK_SECONDARY)


def timeseries(ds, width_s, figsize):
    series = pd.read_csv(RES / "e" / f"m4_{ds}_series_{MAIN[ds]}.csv")
    panels = [("adj_nmi", "NMI with\nprevious window"), ("static_nmi", "NMI with\nstatic partition")]
    if ds == "PS":
        panels.insert(0, ("class_nmi", "NMI with\nclasses"))
        x = ((series["start"] + width_s / 2) % 86400) / 3600
        group = (series["start"] // 86400).to_numpy()
        xlabel = "Time of day (h)"
    else:
        x = (series["start"] + width_s / 2 - series["start"].min()) / 86400
        group = np.zeros(len(series), dtype=int)
        xlabel = "Days since first message"
    groups = sorted(set(group))
    fig, axes = plt.subplots(len(panels), len(groups), figsize=figsize, sharex="col", sharey="row",
                             squeeze=False, constrained_layout=True)
    for col, gval in enumerate(groups):
        m = group == gval
        for row, (key, ylabel) in enumerate(panels):
            ax = axes[row, col]
            mean, std = series[f"{key}_null_mean"][m], series[f"{key}_null_std"][m]
            ax.fill_between(x[m], mean - std, mean + std, color=COLOR_NULL, alpha=0.18, linewidth=0)
            ax.plot(x[m], mean, color=COLOR_NULL, lw=1.6, ls="--", label="P1 null (mean ± sd)")
            if key == "adj_nmi":
                ax.plot(x[m], series["self_nmi"][m], color=COLOR_SELF, lw=1.6, ls=":",
                        label="same window, other seed")
            ax.plot(x[m], series[key][m], color=COLOR_REAL, lw=1.6, marker="o", ms=2.5, label="real")
            ax.set_ylim(0, 1.02)
            style(ax)
            if col == 0:
                ax.set_ylabel(ylabel)
            if row == 0 and len(groups) > 1:
                ax.set_title(f"Day {col + 1}")
            if row == len(panels) - 1:
                ax.set_xlabel(xlabel)
    adj_row = [k for k, _ in panels].index("adj_nmi")
    handles, labels = axes[adj_row, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside upper center", ncol=3 if len(groups) > 1 else 2, frameon=False,
               fontsize=8)
    save(fig, f"e_m4_{ds.lower()}_timeseries")


def width_seconds(label):
    return pd.Timedelta(label).total_seconds()


def sensitivity(summary):
    rows = []
    for r in summary.itertuples():
        m = TAG.match(r.metric)
        if m:
            rows.append((r.dataset, m.group(1), m.group(2), float(m.group(3)), r.value, r.null_mean))
    df = pd.DataFrame(rows, columns=["dataset", "metric", "width", "gamma", "value", "null_mean"])
    df["gap"] = df["value"] - df["null_mean"]
    panels = [("m4_static_nmi_mean", "Δ NMI with static\n(real − null)"),
              ("m4_adj_nmi_mean", "Δ NMI with previous\nwindow (real − null)"),
              ("m4_n_comms_mean", "Communities per\nsnapshot (real)")]
    fig, axes = plt.subplots(len(panels), 2, figsize=(7.2, 5.2), sharex=True, squeeze=False,
                             constrained_layout=True)
    for col, ds in enumerate(["PS", "CM"]):
        d = df[df["dataset"] == ds]
        widths = sorted(d["width"].unique(), key=width_seconds)
        for row, (metric, ylabel) in enumerate(panels):
            ax = axes[row, col]
            for color, w in zip(SERIES, widths):
                s = d[(d["metric"] == metric) & (d["width"] == w)].sort_values("gamma")
                y = s["value"] if metric == "m4_n_comms_mean" else s["gap"]
                ax.plot(s["gamma"], y, color=color, lw=1.6, marker="o", ms=4, label=w)
            if metric != "m4_n_comms_mean":
                ax.axhline(0, color=INK_SECONDARY, lw=0.8)
            ax.set_xscale("log", base=2)
            ax.set_xticks([0.5, 1, 2], ["0.5", "1", "2"])
            style(ax)
            if col == 0:
                ax.set_ylabel(ylabel)
            if row == 0:
                ax.set_title(NAMES[ds])
                ax.legend(title="window", frameon=False, fontsize=7, title_fontsize=7)
            if row == len(panels) - 1:
                ax.set_xlabel("Resolution γ")
    save(fig, "e_m4_sensitivity")


def rank_scatter(summary):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), constrained_layout=True)
    indexed = summary.set_index(["dataset", "metric"])
    for ax, ds in zip(axes, ["PS", "CM"]):
        nodes = pd.read_csv(RES / "e" / f"m3b_{ds}_nodes.csv")
        rs = nodes["static_unweighted"].rank(pct=True)
        rt = nodes["temporal"].rank(pct=True)
        ax.scatter(rs, rt, s=8 if ds == "PS" else 4, color=COLOR_REAL, alpha=0.6, linewidths=0)
        ax.plot([0, 1], [0, 1], color=INK_SECONDARY, lw=0.8, ls="--")
        tau = indexed.loc[(ds, "m3b_tau_unweighted")]
        ax.set_title(f"{NAMES[ds]}  (τ = {tau['value']:.2f}; P1 null {tau['null_mean']:.2f})")
        ax.set_xlabel("Static closeness rank (percentile)")
        ax.set_aspect("equal")
        style(ax)
    axes[0].set_ylabel("Temporal closeness rank (percentile)")
    save(fig, "e_m3b_rank_scatter")


def main():
    summary = pd.read_csv(RES / "e_summary.csv")
    timeseries("PS", 15 * 60, (7.2, 5.4))
    timeseries("CM", 7 * 86400, (3.4, 3.6))
    sensitivity(summary)
    rank_scatter(summary)


if __name__ == "__main__":
    main()
