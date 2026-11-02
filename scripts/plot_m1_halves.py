"""Prepare the PS and CM split-period M1 figure and tables from the saved CSVs."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd

from scripts.run_m1 import ROOT, WINDOWS, sensitivity

METRICS = ["density", "mean_degree", "clustering", "n_components",
           "component_fraction", "largest_component_fraction"]
PERIODS = ["first_half", "second_half"]


def width_label(seconds):
    for divisor, unit in [(86400, "d"), (3600, "h"), (60, "m")]:
        if seconds % divisor == 0:
            return f"{seconds // divisor}{unit}"
    return f"{seconds}s"


def main():
    source = ROOT / "results/m1/robustness_fixed"
    tables = ROOT / "results/m1/plot_tables"
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    plot_values, effects = [], []
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 12, "pdf.fonttype": 42}):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.3), sharey=True)
        for ax, dataset, panel_title in zip(axes, ("PS", "CM"),
                ("Primary School · connected component", "CollegeMsg · weakly connected component")):
            summary = pd.read_csv(source / f"{dataset}_summary.csv")
            main_rows = summary.loc[(summary.window_policy == "complete_only") &
                                    (summary.node_basis == "fixed") & summary.metric.isin(METRICS)]
            halves = main_rows.loc[main_rows.period.isin(PERIODS)].copy()
            counts = halves.loc[halves.metric == "density"].pivot(
                index="delta_seconds", columns="period", values="n_windows").loc[WINDOWS[dataset], PERIODS]
            common = counts.index[counts.gt(0).all(axis=1)]
            if len(common) < 2:
                raise ValueError(f"{dataset} has fewer than two widths with complete windows in both halves")
            plot_values.append(halves[["dataset", "period", "delta_seconds", "metric",
                                      "n_windows", "n_empty", "mean"]])
            effects.append(sensitivity(main_rows.loc[main_rows.delta_seconds.isin(common)]))
            lcc = halves.loc[halves.metric == "largest_component_fraction"].pivot(
                index="delta_seconds", columns="period", values="mean").loc[common]
            for period, label, style, color in zip(PERIODS, ["First half", "Second half"],
                    ["o-", "s--"], ["#14687a", "#b54d26"]):
                ax.plot(common, lcc[period], style, color=color, label=label,
                        markersize=6, linewidth=2, markerfacecolor="white" if period == "second_half" else color)
            ax.set_title(panel_title, fontsize=13, loc="left", fontweight="bold")
            ax.set_xscale("log")
            ax.set_xticks(common, [width_label(width) for width in common])
            ax.minorticks_off()
            ax.tick_params(axis="x", labelsize=10)
            ax.set_xlabel("Aggregation window")
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
            ax.set_ylim(0, 1)
            ax.grid(axis="y", alpha=0.2)
            ax.spines[["top", "right"]].set_visible(False)
        axes[0].set_ylabel("Mean share of nodes in largest component")
        fig.suptitle("Does the window effect persist in both halves?", x=0.065, y=0.98,
                     ha="left", fontsize=20, fontweight="bold")
        fig.legend(*axes[0].get_legend_handles_labels(), ncol=2, frameon=False,
                   loc="upper left", bbox_to_anchor=(0.055, 0.915))
        fig.subplots_adjust(left=0.085, right=0.985, bottom=0.24, top=0.74, wspace=0.14)
        fig.text(0.065, 0.093, "Each point averages complete windows, including empty ones. Each half uses the full dataset’s node set.", fontsize=10)
        fig.text(0.065, 0.044, "Per half: PS has 2 complete 8h windows and no complete 24h window. CM has 3 complete 30d windows.", fontsize=10)
        for extension in ["png", "pdf"]:
            fig.savefig(figures / f"M1_halves_connectivity.{extension}", dpi=180, facecolor="white")
        plt.close(fig)
    pd.concat(plot_values).to_csv(tables / "M1_half_means.csv", index=False)
    pd.concat(effects).to_csv(tables / "M1_common_grid_sensitivity.csv", index=False)
    print("Saved figures/M1_halves_connectivity.png and .pdf; tables in results/m1/plot_tables/")


if __name__ == "__main__":
    main()
