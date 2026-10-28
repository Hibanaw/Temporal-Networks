"""Result-independent schematic figures for the report."""
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

out = Path(sys.argv[1]); out.mkdir(exist_ok=True, parents=True)
plt.rcParams.update({"font.size": 8, "font.family": "serif", "pdf.fonttype": 42})
C = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]

# ---- Fig: framework -------------------------------------------------
fig, ax = plt.subplots(figsize=(6.9, 2.5)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 4)
parts = [("I  Representation", "What does aggregation\nlose?", "H1", "M1"),
         ("II  Activity", "Bursty, repeated,\npersistent?", "H2, H3", "M2a, M2b"),
         ("III  Evolution", "Growth, ageing,\nreorganisation?", "H4, H5", "M2c, M4"),
         ("IV  Function", "Reachability, centrality,\nspreading?", "H6, H7", "M3a--c")]
for i, (t, q, h, m) in enumerate(parts):
    x = 0.1 + i * 2.45
    ax.add_patch(FancyBboxPatch((x, 1.35), 2.25, 2.35, boxstyle="round,pad=0.03", fc=C[i], alpha=.18, ec=C[i]))
    ax.text(x + 1.125, 3.4, t, ha="center", weight="bold", color=C[i])
    ax.text(x + 1.125, 2.75, q, ha="center", va="center")
    ax.text(x + 1.125, 1.95, f"hypotheses {h}", ha="center", style="italic")
    ax.text(x + 1.125, 1.6, f"methods {m}", ha="center")
ax.add_patch(FancyBboxPatch((0.1, 0.1), 9.75, 0.9, boxstyle="round,pad=0.03", fc="#dddddd", ec="grey"))
ax.text(0.35, 0.55, "Data: contact (PS)  |  messaging (CM)  |  citation (CIT)", va="center")
ax.text(9.6, 0.55, "null models P1, P2", ha="right", va="center", style="italic")
for i in range(4):
    ax.annotate("", (0.1 + i * 2.45 + 1.125, 1.0), (0.1 + i * 2.45 + 1.125, 1.33),
                arrowprops=dict(arrowstyle="<-", color="grey"))
fig.savefig(out / "fig_framework.pdf", bbox_inches="tight"); plt.close(fig)

# ---- Fig: aggregation loses time order ------------------------------
fig, axs = plt.subplots(1, 3, figsize=(6.9, 1.9), gridspec_kw={"width_ratios": [1.1, 1.8, 1.1]})
pos = {"a": (0, 0), "b": (1, 0.6), "c": (2, 0), "d": (1, -0.7)}
def draw(ax, edges, title, col="k", lw=1.5):
    for u, v in edges:
        ax.plot(*zip(pos[u], pos[v]), color=col, lw=lw, zorder=1)
    for n, (x, y) in pos.items():
        ax.scatter(x, y, s=170, fc="white", ec="k", zorder=2); ax.text(x, y, n, ha="center", va="center", zorder=3)
    ax.set_title(title, fontsize=8); ax.axis("off"); ax.set_xlim(-.5, 2.5); ax.set_ylim(-1.1, 1.0)
draw(axs[0], [("a", "b"), ("b", "c"), ("c", "d")], "(a) static aggregate")
# timeline
ax = axs[1]
ev = [("c", "d", 1), ("a", "b", 2), ("b", "c", 3)]
ax.set_title("(b) event sequence", fontsize=8)
for i, (u, v, t) in enumerate(ev):
    ax.plot([t, t], [0, 1], color=C[i], lw=3); ax.text(t, 1.08, f"{u}–{v}", ha="center", color=C[i])
ax.annotate("", (3.6, -.1), (.4, -.1), arrowprops=dict(arrowstyle="->")); ax.text(3.6, -.35, "time", ha="right")
ax.text(2, -.75, "a→d: path a–b–c–d exists in (a),\nbut c–d precedes a–b: not time-respecting", ha="center", fontsize=7, color="#C44E52")
ax.set_xlim(.3, 3.7); ax.set_ylim(-1.1, 1.4); ax.axis("off")
draw(axs[2], [("a", "b"), ("b", "c")], "(c) reachable from a")
fig.savefig(out / "fig_aggregation_schematic.pdf", bbox_inches="tight"); plt.close(fig)

# ---- Fig: null models ----------------------------------------------
rng = np.random.default_rng(3)
pairs = [("1–2", 0), ("1–3", 1), ("2–3", 2), ("3–4", 3)]
T = 20
ev = []
for lab, k in pairs:  # bursty toy: events cluster in bursts
    c = rng.choice(T - 3, 2, replace=False)
    ts = np.concatenate([c[0] + rng.uniform(0, 2.5, 3), c[1] + rng.uniform(0, 2.5, 3)])
    ev += [(k, t) for t in ts]
ev = np.array(ev)
fig, axs = plt.subplots(3, 1, figsize=(6.9, 2.7), sharex=True)
def timeline(ax, rows, ts, title):
    for r, t in zip(rows, ts):
        ax.plot([t, t], [r - .35, r + .35], color=C[int(r)], lw=1.4)
    ax.set_yticks(range(4)); ax.set_yticklabels([p[0] for p in pairs]); ax.set_title(title, fontsize=8, loc="left")
    ax.set_xlim(0, T)
timeline(axs[0], ev[:, 0], ev[:, 1], "original: bursty, correlated in time")
perm = rng.permutation(len(ev))
timeline(axs[1], ev[:, 0], ev[perm, 1], "P1  shuffled timestamps: same static graph, temporal correlations destroyed")
perm_rows = np.array([2, 3, 0, 1])  # edge rewiring: whole contact sequences move to other node pairs
rows2 = perm_rows[ev[:, 0].astype(int)]
timeline(axs[2], rows2, ev[:, 1], "P2  rewired links: each pair's contact sequence kept, wiring diagram destroyed")
axs[2].set_xlabel("time")
fig.tight_layout(); fig.savefig(out / "fig_nullmodels.pdf", bbox_inches="tight"); plt.close(fig)
