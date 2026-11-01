"""Shared figure style for every manuscript figure.

Figures are drawn at their printed size (one column 3.28125 in, text width 6.875 in)
with the base sizes below; `save` scales all text to 80 % so that it prints at about
6.4 pt, and writes the PDF to figures/ and report/figures/.
"""
import shutil
from pathlib import Path

import matplotlib
from matplotlib.text import Text

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

COLUMN = 3.28125
WIDTH = 6.875
# One palette for all figures: observed / primary, null or comparison, third series.
REAL, NULL, THIRD = "#173F5F", "#C36A2B", "#2C8A78"
SERIES = [REAL, NULL, THIRD]
GRID = "#d9d9d9"

RC = {
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.linewidth": .6, "lines.linewidth": 1.1, "lines.markersize": 3,
    "axes.labelpad": 2, "axes.titlepad": 3, "xtick.major.pad": 2, "ytick.major.pad": 2,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "grid.color": GRID, "grid.linewidth": .5,
    "pdf.fonttype": 42, "savefig.dpi": 220,
}


def apply():
    plt.rcParams.update(RC)


def grid(fig, rows, cols, width, height, **kw):
    """Constrained-layout subplot grid with tight pads."""
    fig, axs = plt.subplots(rows, cols, figsize=(width, height), layout="constrained", squeeze=False, **kw)
    fig.set_constrained_layout_pads(w_pad=.004, h_pad=.008, wspace=.025, hspace=.04)
    return fig, axs


def save(fig, name, root):
    root = Path(root)
    for text in fig.findobj(Text):
        text.set_fontsize(text.get_fontsize() * .80)
    fig.canvas.draw()
    (root / "figures").mkdir(exist_ok=True)
    (root / "report" / "figures").mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(root / "figures" / f"{name}.{ext}")
    shutil.copy2(root / "figures" / f"{name}.pdf", root / "report" / "figures" / f"{name}.pdf")
    plt.close(fig)
