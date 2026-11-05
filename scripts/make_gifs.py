"""Animated GIFs for the presentation (primary-school data and the toy example).

  python scripts/make_gifs.py            # all GIFs into figures/gifs/
  python scripts/make_gifs.py sir day    # only some of them

GIFs: warmup (slide 2/4), window (Lesson 1), day (Lesson 4), sir (Lesson 5),
cm_sir (Lesson 5, messages), cm_reach (Lesson 3), cit (Lesson 6).
Uses data/processed/PS, data/processed/CM, ../final_project/data/processed/CIT and results/e/m4_PS_series_w15min_g1.csv; the SIR setting
(beta 0.05, 4 h) and the P1 shuffle are the ones used in run_d.py.
"""
import shutil
import sys
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.nullmodels import timestamp_shuffle  # noqa: E402
from src.spreading import simulate_sir  # noqa: E402

OUT = ROOT / "figures" / "gifs"
REAL, NULL, THIRD = "#173F5F", "#C36A2B", "#2C8A78"
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "DejaVu Sans"})
DPI = 90


def hhmm(t):
    day = int(t // 86400) + 1
    s = int(t % 86400)
    return f"Day {day}  {s // 3600:02d}:{(s % 3600) // 60:02d}"


def save(anim, name, fps):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.gif"
    # Render locally first: writing many small chunks into a synced folder can time out.
    with tempfile.TemporaryDirectory() as tmp:
        anim.save(Path(tmp) / path.name, writer=PillowWriter(fps=fps), dpi=DPI)
        shutil.copyfile(Path(tmp) / path.name, path)
    plt.close(anim._fig)
    print(f"wrote {path.relative_to(ROOT)}  ({path.stat().st_size / 1e6:.1f} MB)")


# ---------------------------------------------------------------- data

def load_ps():
    ev = pd.read_csv(ROOT / "data/processed/PS/events.csv")
    nodes = pd.read_csv(ROOT / "data/processed/PS/nodes.csv")
    return ev, nodes


def class_layout(nodes, seed=1):
    """Class clusters on a ring (1A ... 5B), teachers in the middle."""
    rng = np.random.default_rng(seed)
    classes = sorted(c for c in nodes["label"].unique() if c != "Teachers")
    centres = {c: (np.cos(a), np.sin(a)) for c, a in
               zip(classes, np.pi / 2 - 2 * np.pi * np.arange(len(classes)) / len(classes))}
    centres["Teachers"] = (0.0, 0.0)
    pos = np.zeros((len(nodes), 2))
    for i, lab in enumerate(nodes["label"]):
        r = 0.17 * np.sqrt(rng.random())
        a = 2 * np.pi * rng.random()
        pos[i] = np.add(centres[lab], (r * np.cos(a), r * np.sin(a)))
    cmap = plt.get_cmap("tab10")
    colour = {c: cmap(k) for k, c in enumerate(classes)}
    colour["Teachers"] = (0.35, 0.35, 0.35, 1)
    return pos, centres, colour


def draw_class_labels(ax, centres):
    for c, (x, y) in centres.items():
        if c != "Teachers":
            ax.text(1.27 * x, 1.27 * y, c, ha="center", va="center", fontsize=10, color="#444")


# ---------------------------------------------------------------- 1. warm-up toy

def gif_warmup():
    pos = {"A": (0, 0), "B": (1, 0), "C": (2, 0), "D": (3, 0)}
    edges = [("C", "D", 1), ("B", "C", 2), ("A", "B", 3)]
    fig, axs = plt.subplots(2, 1, figsize=(7, 4.6))
    fig.subplots_adjust(left=.03, right=.97, top=.86, bottom=.03, hspace=.45)
    times = [0, 1, 2, 3, 3.6]

    def reached(src, now):
        got = {src: 0}
        for a, b, t in sorted(edges, key=lambda e: e[2]):
            if t > now:
                break
            for x, y in ((a, b), (b, a)):
                if x in got and got[x] < t and y not in got:
                    got[y] = t
        return got

    def frame(k):
        now = times[k]
        fig.suptitle(f"Rumour spreading along timed contacts      t = {min(now, 3):g}",
                     fontsize=13, weight="bold")
        for ax, src in zip(axs, ("A", "D")):
            ax.clear()
            ax.set_xlim(-.4, 3.4)
            ax.set_ylim(-.55, .6)
            ax.axis("off")
            got = reached(src, now)
            for a, b, t in edges:
                (x0, y0), (x1, y1) = pos[a], pos[b]
                active = t <= now
                used = a in got and b in got and max(got[a], got[b]) == t
                col = "#d62728" if used else (REAL if active else "#bbbbbb")
                ax.plot([x0, x1], [y0, y1], color=col, lw=4 if used else 2, zorder=1,
                        ls="-" if active else "--")
                ax.text((x0 + x1) / 2, .17, f"t = {t}", ha="center", fontsize=11,
                        color=col, weight="bold" if t == int(now) else "normal")
            for n, (x, y) in pos.items():
                fc = "#d62728" if n in got else "white"
                ax.scatter([x], [y], s=900, c=[fc], edgecolors=REAL, linewidths=2, zorder=2)
                ax.text(x, y, n, ha="center", va="center", fontsize=14, weight="bold",
                        color="white" if n in got else REAL, zorder=3)
            ok = "D" in got if src == "A" else "A" in got
            target = "D" if src == "A" else "A"
            msg = f"Start at {src}"
            if now >= 3:
                msg += f"  ->  reaches {target}? " + ("YES" if ok else "NO")
            ax.text(-.35, -.45, msg, fontsize=12, weight="bold",
                    color=("#2C8A78" if ok else "#d62728") if now >= 3 else "#333")
        return []

    save(FuncAnimation(fig, frame, frames=len(times)), "gif_warmup", fps=1)


# ---------------------------------------------------------------- 2. window width sweep

def components(n, u, v):
    parent = np.arange(n)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in zip(u, v):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(n)])
    return roots


def gif_window():
    ev, nodes = load_ps()
    idx = {n: i for i, n in enumerate(nodes["id"])}
    pos, centres, colour = class_layout(nodes)
    n = len(nodes)
    t0 = 10 * 3600  # Day 1, 10:00
    widths = np.unique(np.round(np.geomspace(60, 7.2 * 3600, 36) / 20) * 20)
    stats = []
    for w in widths:
        sub = ev[(ev.t >= t0) & (ev.t < t0 + w)].drop_duplicates(["u", "v"])
        u, v = sub.u.map(idx).to_numpy(), sub.v.map(idx).to_numpy()
        roots = components(n, u, v)
        active = np.zeros(n, bool)
        active[u] = active[v] = True
        lcc = np.bincount(roots[active]).max() / n if active.any() else 0
        stats.append((w, u, v, lcc, 2 * len(u) / (n * (n - 1)), roots, active))

    fig = plt.figure(figsize=(10, 5.2))
    ax = fig.add_axes([0.0, 0.02, 0.5, 0.86])
    a1 = fig.add_axes([0.6, 0.56, 0.36, 0.3])
    a2 = fig.add_axes([0.6, 0.12, 0.36, 0.3])
    ws = np.array([s[0] for s in stats]) / 60
    for a, k, lab in ((a1, 3, "largest component\n(fraction of nodes)"), (a2, 4, "edge density")):
        a.plot(ws, [s[k] for s in stats], color="#cccccc", lw=1.5)
        a.set_xscale("log")
        a.set_ylabel(lab)
        a.set_xticks([1, 5, 15, 60, 240])
        a.set_xticklabels(["1m", "5m", "15m", "1h", "4h"])
    a2.set_xlabel("window width Δt (from Day 1 10:00)")
    l1, = a1.plot([], [], color=REAL, lw=2.2)
    l2, = a2.plot([], [], color=REAL, lw=2.2)
    d1, = a1.plot([], [], "o", color="#d62728")
    d2, = a2.plot([], [], "o", color="#d62728")
    fig.text(.25, .015, "black ring = in largest component", ha="center", fontsize=9, color="#555")
    fig.suptitle("Lesson 1: the window width decides what network you see",
                 fontsize=14, weight="bold")

    def frame(k):
        w, u, v, lcc, dens, roots, active = stats[k]
        ax.clear()
        ax.set_xlim(-1.45, 1.45)
        ax.set_ylim(-1.45, 1.45)
        ax.set_aspect("equal")
        ax.axis("off")
        draw_class_labels(ax, centres)
        segs = np.stack([pos[u], pos[v]], axis=1)
        alpha = max(.04, min(.5, 40 / max(len(u), 1)))
        ax.add_collection(LineCollection(segs, colors=[(0.09, 0.25, 0.37, alpha)], lw=.7))
        big = np.bincount(roots[active]).argmax() if active.any() else -1
        in_lcc = roots == big
        cols = [colour[l] for l in nodes["label"]]
        ax.scatter(pos[:, 0], pos[:, 1], s=np.where(in_lcc, 26, 10), c=cols,
                   edgecolors=np.where(in_lcc, "k", "none"), linewidths=.4,
                   alpha=np.where(active, 1, .25))
        lab = f"{w / 60:.0f} min" if w < 3600 else f"{w / 3600:.1f} h"
        ax.text(0, 1.52, f"Δt = {lab}", ha="center", fontsize=14, weight="bold", color="#d62728")
        l1.set_data(ws[:k + 1], [s[3] for s in stats[:k + 1]])
        l2.set_data(ws[:k + 1], [s[4] for s in stats[:k + 1]])
        d1.set_data([ws[k]], [lcc])
        d2.set_data([ws[k]], [dens])
        return []

    frames = list(range(len(stats))) + [len(stats) - 1] * 8
    save(FuncAnimation(fig, frame, frames=frames), "gif_window", fps=5)


# ---------------------------------------------------------------- 3. school day

def gif_day():
    ev, nodes = load_ps()
    idx = {n: i for i, n in enumerate(nodes["id"])}
    lab = nodes["label"].to_numpy()
    pos, centres, colour = class_layout(nodes)
    series = pd.read_csv(ROOT / "results/e/m4_PS_series_w15min_g1.csv")
    series = series[series.start < 86400]
    width, step = 900, 300
    starts = np.arange(31200, 61800, step)

    fig = plt.figure(figsize=(11, 5.4))
    ax = fig.add_axes([0.0, 0.02, 0.48, 0.86])
    a1 = fig.add_axes([0.57, 0.56, 0.4, 0.3])
    a2 = fig.add_axes([0.57, 0.12, 0.4, 0.3])
    mid = (series.start + 450) / 3600
    a1.plot(mid, series.class_nmi, color=REAL, lw=2, label="real")
    a1.plot(mid, series.class_nmi_null_mean, color=NULL, lw=2, label="shuffled (P1)")
    a1.set_ylabel("NMI(communities, classes)")
    a1.set_ylim(.35, 1.02)
    a1.legend(loc="lower right", fontsize=9, frameon=False)
    for a in (a1, a2):
        a.axvspan(12, 14, color="#f3e3c3", zorder=0)
        a.set_xlim(8.5, 17.3)
    a1.text(13, 1.0, "lunch", ha="center", fontsize=9, color="#8a6d2b")

    frac = []
    for s in starts:
        sub = ev[(ev.t >= s) & (ev.t < s + width)]
        lu, lv = lab[sub.u.map(idx)], lab[sub.v.map(idx)]
        frac.append(np.mean(lu != lv) if len(sub) else np.nan)
    hrs = (starts + width / 2) / 3600
    a2.plot(hrs, frac, color="#cccccc", lw=1.5)
    a2.set_ylabel("contacts between\ndifferent classes")
    a2.set_xlabel("time of day (Day 1, 15-min window)")
    a2.set_ylim(0, 1)
    l2, = a2.plot([], [], color=THIRD, lw=2.2)
    cur = a1.axvline(np.nan, color="#d62728", lw=1.5)
    cur2 = a2.axvline(np.nan, color="#d62728", lw=1.5)
    fig.text(.24, .015, "grey: contact within a class    red: contact between classes", ha="center",
             fontsize=9, color="#555")
    fig.suptitle("Lesson 4: classes dissolve at lunch (primary school, Day 1)",
                 fontsize=14, weight="bold")
    cols = [colour[l] for l in lab]

    def frame(k):
        s = starts[k]
        sub = ev[(ev.t >= s) & (ev.t < s + width)]
        pairs = sub.groupby(["u", "v"]).size().reset_index(name="w")
        u, v = pairs.u.map(idx).to_numpy(), pairs.v.map(idx).to_numpy()
        cross = lab[u] != lab[v]
        ax.clear()
        ax.set_xlim(-1.45, 1.45)
        ax.set_ylim(-1.45, 1.45)
        ax.set_aspect("equal")
        ax.axis("off")
        draw_class_labels(ax, centres)
        segs = np.stack([pos[u], pos[v]], axis=1)
        ax.add_collection(LineCollection(segs[~cross], colors=[(0.3, 0.3, 0.3, .35)], lw=.8))
        ax.add_collection(LineCollection(segs[cross], colors=[(0.84, 0.15, 0.16, .55)], lw=.9))
        active = np.zeros(len(lab), bool)
        active[u] = active[v] = True
        ax.scatter(pos[:, 0], pos[:, 1], s=22, c=cols, alpha=np.where(active, 1, .2),
                   edgecolors="none")
        ax.text(0, 1.52, hhmm(s) + f" – {int((s + width) % 86400) // 3600:02d}:"
                f"{int((s + width) % 3600) // 60:02d}", ha="center", fontsize=13, weight="bold")
        h = (s + width / 2) / 3600
        cur.set_xdata([h, h])
        cur2.set_xdata([h, h])
        l2.set_data(hrs[:k + 1], frac[:k + 1])
        return []

    save(FuncAnimation(fig, frame, frames=len(starts)), "gif_day", fps=6)


# ---------------------------------------------------------------- 4. SIR real vs shuffled

def prevalence(inf, grid, duration):
    return ((inf[None, :] <= grid[:, None]) & (grid[:, None] < inf[None, :] + duration)).mean(1)


def sir_animation(name, title, ev, nodes, pos, beta, duration, directed, horizon, step, unit,
                  unit_name, clock, n_runs=200, size=18, ms=None):
    """Real vs P1 SIR: one representative outbreak on the layout plus mean prevalence curves."""
    idx = {n: i for i, n in enumerate(nodes["id"])}
    n = len(nodes)

    def arrays(df):
        df = df.sort_values("t", kind="stable")
        return (df.u.map(idx).to_numpy(), df.v.map(idx).to_numpy(), df.t.to_numpy().astype(float))

    real = arrays(ev)
    shuf = arrays(timestamp_shuffle(ev, seed=0))
    rng = np.random.default_rng(5253)
    # Seeds as in run_d.py: the sender of a random real event, started at its time.
    pos_ev = rng.integers(0, int(0.7 * len(ev)), size=n_runs)
    t_starts = real[2][pos_ev]
    sources = real[0][pos_ev]
    rel = np.arange(0, horizon, step / 2)
    curves = {"real": [], "shuf": []}
    runs = {"real": [], "shuf": []}
    for k in range(n_runs):
        for key, (u, v, t) in (("real", real), ("shuf", shuf)):
            inf = simulate_sir(u, v, t, n, sources[k], t_starts[k], beta, duration, directed,
                               np.random.default_rng([5253, k]))
            runs[key].append(inf - t_starts[k])
            if np.isfinite(inf).mean() >= .05:
                curves[key].append(prevalence(inf - t_starts[k], rel, duration))
    mean = {k: np.mean(v, axis=0) for k, v in curves.items()}
    big = {k: np.mean([np.isfinite(r).mean() for r in runs[k] if np.isfinite(r).mean() >= .05])
           for k in runs}

    # Show one run that is a major outbreak in both and close to the average behaviour.
    def score(k):
        a, b = runs["real"][k], runs["shuf"][k]
        if np.isfinite(a).mean() < .6 * big["real"] or np.isfinite(b).mean() < .6 * big["shuf"]:
            return np.inf
        pa, pb = prevalence(a, rel, duration), prevalence(b, rel, duration)
        return np.abs(pa - mean["real"]).sum() + np.abs(pb - mean["shuf"]).sum()
    best = int(np.argmin([score(k) for k in range(n_runs)]))
    shown = {k: runs[k][best] for k in runs}
    peaks = {k: rel[np.argmax(mean[k])] for k in mean}
    print(f"{name}: {len(curves['real'])}/{len(curves['shuf'])} major outbreaks, showing run {best}"
          f" ({clock(t_starts[best])}); mean-curve peak ratio real/P1 = "
          f"{peaks['real'] / peaks['shuf']:.2f}")

    fig = plt.figure(figsize=(11, 6.6))
    axr = fig.add_axes([0.01, 0.36, 0.33, 0.52])
    axs = fig.add_axes([0.34, 0.36, 0.33, 0.52])
    leg = fig.add_axes([0.69, 0.42, 0.29, 0.42])
    ac = fig.add_axes([0.08, 0.08, 0.88, 0.22])
    leg.axis("off")
    leg.set_xlim(0, 1)
    leg.set_ylim(0, 1)
    dur = f"{duration / 3600:g} h" if duration < 86400 else f"{duration / 86400:g} days"
    leg.text(0, .95, f"One outbreak, same seed node and\nstart time, β = {beta:g}, {dur} infectious",
             fontsize=10, va="top")
    for k, (c, t) in enumerate((("white", "susceptible"), ("#d62728", "infectious"),
                                ("#999999", "recovered"))):
        leg.scatter([.04], [.6 - .13 * k], s=80, c=c, edgecolors="#333")
        leg.text(.1, .6 - .13 * k, t, va="center", fontsize=10)
    leg.text(0, .12, "Curves: mean over all major\noutbreaks (≥5 %), " f"{n_runs} seeds",
             fontsize=9, color="#555", va="top")

    x = rel / unit
    ac.plot(x, mean["real"], color=REAL, lw=1, alpha=.35)
    ac.plot(x, mean["shuf"], color=NULL, lw=1, alpha=.35)
    lr, = ac.plot([], [], color=REAL, lw=2.4, label="real timing")
    ls, = ac.plot([], [], color=NULL, lw=2.4, label="shuffled timestamps (P1)")
    ac.set_xlim(0, horizon / unit)
    ac.set_ylim(0, max(mean["real"].max(), mean["shuf"].max()) * 1.15)
    ac.set_xlabel(f"{unit_name} since the first infection")
    ac.set_ylabel("infectious\nfraction")
    ac.legend(loc="upper right", frameon=False, fontsize=9)
    for key, col in (("real", REAL), ("shuf", NULL)):
        ac.axvline(peaks[key] / unit, color=col, ls=":", lw=1)
    cur = ac.axvline(0, color="#d62728", lw=1.2)
    fig.suptitle(title, fontsize=14, weight="bold")
    lim = np.abs(pos).max() * 1.08

    def draw(ax, inf, now, label, col):
        ax.clear()
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.axis("off")
        infd = inf <= now
        ill = infd & (now < inf + duration)
        rec = infd & ~ill
        order = np.argsort(infd.astype(int) + ill)  # infectious nodes drawn on top
        fc = np.where(ill, "#d62728", np.where(rec, "#999999", "white"))[order]
        ax.scatter(pos[order, 0], pos[order, 1], s=size, c=list(fc), edgecolors="#555",
                   linewidths=.3 if ms is None else ms)
        ax.set_title(f"{label}\ninfected so far: {infd.mean():.0%}", color=col, fontsize=11,
                     weight="bold")

    frame_t = np.arange(0, horizon + 1, step)
    clock_text = fig.text(.83, .37, "", fontsize=12, ha="center", weight="bold")

    def frame(k):
        now = frame_t[k]
        draw(axr, shown["real"], now, "Real timing", REAL)
        draw(axs, shown["shuf"], now, "Shuffled timing (P1)", NULL)
        m = rel <= now
        lr.set_data(x[m], mean["real"][m])
        ls.set_data(x[m], mean["shuf"][m])
        cur.set_xdata([now / unit] * 2)
        clock_text.set_text(f"{clock(t_starts[best] + now)}\n(+{now / unit:.1f} {unit_name})")
        return []

    frames = list(range(len(frame_t))) + [len(frame_t) - 1] * 10
    save(FuncAnimation(fig, frame, frames=frames), name, fps=8)


def gif_sir():
    ev, nodes = load_ps()
    pos, _, _ = class_layout(nodes)
    sir_animation("gif_sir", "Lesson 5: the same epidemic on real vs shuffled timing (primary school)",
                  ev, nodes, pos, beta=0.05, duration=4 * 3600, directed=False,
                  horizon=12 * 3600, step=600, unit=3600, unit_name="hours", clock=hhmm)


# ---------------------------------------------------------------- CollegeMsg

def load_cm():
    ev = pd.read_csv(ROOT / "data/processed/CM/events.csv")
    nodes = pd.read_csv(ROOT / "data/processed/CM/nodes.csv")
    return ev, nodes


def cm_date(t):
    return pd.Timestamp(int(t), unit="s").strftime("%d %b %Y")


def normalise(p):
    """Centre on the median and scale so 97 % of nodes fit in the unit disc; stragglers
    (small components) are pulled onto a thin outer ring instead of shrinking the picture."""
    p = p - np.median(p, axis=0)
    r = np.linalg.norm(p, axis=1)
    p = p / np.quantile(r, .97)
    r = np.linalg.norm(p, axis=1, keepdims=True)
    far = r[:, 0] > 1
    p[far] = p[far] / r[far] * (1 + .06 * np.tanh(r[far] - 1))
    return p


def cm_layout(ev, nodes, seed=1):
    """Force layout of the aggregated message graph; cached because it takes a while."""
    import networkx as nx
    cache = OUT / ".cm_layout_v2.npy"
    if cache.exists():
        return np.load(cache)
    g = nx.Graph()
    g.add_nodes_from(nodes["id"])
    g.add_edges_from(ev[["u", "v"]].drop_duplicates().itertuples(index=False, name=None))
    p = nx.spring_layout(g, seed=seed, iterations=80, k=1.6 / np.sqrt(len(nodes)))
    pos = normalise(np.array([p[i] for i in nodes["id"]]))
    OUT.mkdir(parents=True, exist_ok=True)
    np.save(cache, pos)
    return pos


def gif_cm_sir():
    ev, nodes = load_cm()
    pos = cm_layout(ev, nodes)
    sir_animation("gif_cm_sir", "Lesson 5: the same epidemic on real vs shuffled timing (messages)",
                  ev, nodes, pos, beta=0.2, duration=14 * 86400, directed=True,
                  horizon=90 * 86400, step=86400, unit=86400, unit_name="days", clock=cm_date,
                  size=6, ms=.15)


def arrival_from(us, vs, ts, n, t_start, directed):
    """All-source earliest arrival, vectorised over sources (same rule as src/paths.py).
    Returns arr[v, s]."""
    arr = np.full((n, n), np.inf)
    np.fill_diagonal(arr, t_start)
    keep = ts > t_start
    for u, v, t in zip(us[keep], vs[keep], ts[keep]):
        au, av = arr[u], arr[v]
        hit = (au < t) & (av > t)
        if not directed:
            back = (av < t) & (au > t)
            au[back] = t
        av[hit] = t
    return arr


def gif_cm_reach():
    """R for every start time used in run_d.py (20 starts); the slide's R is their mean."""
    import json
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import shortest_path
    ev, nodes = load_cm()
    pos = cm_layout(ev, nodes)
    starts = json.load(open(ROOT / "data/processed/CM/data_card.json"))["closeness_starts"]
    idx = {n: i for i, n in enumerate(nodes["id"])}
    n = len(nodes)

    def arrays(df):
        df = df.sort_values("t", kind="stable")
        return (df.u.map(idx).to_numpy(), df.v.map(idx).to_numpy(), df.t.to_numpy().astype(float))
    real = arrays(ev)
    shuf = arrays(timestamp_shuffle(ev, seed=0))
    u, v, _ = real
    adj = coo_matrix((np.ones(len(u)), (u, v)), shape=(n, n)).tocsr()
    dist = shortest_path(adj, method="D", directed=True, unweighted=True)  # dist[s, v]
    pairs = n * (n - 1)
    static_n = np.isfinite(dist).sum(1) - 1          # per source
    static_frac = static_n.sum() / pairs
    R, Rs, per_node = [], [], []
    for t0 in starts:
        ar = arrival_from(*real, n, t0, True)
        a_s = arrival_from(*shuf, n, t0, True)
        got = np.isfinite(ar).sum(0) - 1             # per source
        R.append(got.sum() / pairs / static_frac)
        Rs.append((np.isfinite(a_s).sum() - n) / pairs / static_frac)
        per_node.append(np.where(static_n > 0, got / np.maximum(static_n, 1), np.nan))
    R, Rs = np.array(R), np.array(Rs)
    print(f"gif_cm_reach: mean R over {len(starts)} starts = {R.mean():.3f} (real), "
          f"{Rs.mean():.3f} (P1)")

    t_min, t_max = ev.t.min(), ev.t.max()
    sday = (np.array(starts) - t_min) / 86400
    fig = plt.figure(figsize=(11, 5.6))
    ax = fig.add_axes([0.0, 0.03, 0.47, 0.8])
    a1 = fig.add_axes([0.57, 0.14, 0.4, 0.66])
    a1.set_xlim(-5, (t_max - t_min) / 86400 + 5)
    a1.set_ylim(0, 1.05)
    a1.axhline(1, color="#888", ls="--", lw=1.2)
    a1.text(a1.get_xlim()[1], 1.015, "static graph (R = 1)", ha="right", fontsize=9, color="#555")
    a1.set_xlabel("start time (days since the first message)")
    a1.set_ylabel("R = time-respecting ÷ static\nreachable pairs, from this start")
    mr, = a1.plot([], [], "o-", color=REAL, lw=2, ms=5, label="real time order")
    ms_, = a1.plot([], [], "o-", color=NULL, lw=2, ms=5, label="shuffled timestamps (P1)")
    hr = a1.axhline(np.nan, color=REAL, ls=":", lw=1.4)
    hs = a1.axhline(np.nan, color=NULL, ls=":", lw=1.4)
    a1.legend(loc="upper right", bbox_to_anchor=(1, .95), frameon=False, fontsize=9)
    rtxt = a1.text(.02, .1, "", transform=a1.transAxes, fontsize=11, weight="bold")
    fig.suptitle("Lesson 3: a message path must follow the clock (CollegeMsg)", fontsize=14,
                 weight="bold")
    cmap = plt.get_cmap("viridis")
    fig.text(.235, .02, "node colour: share of its static reach it still reaches in time order",
             ha="center", fontsize=9, color="#555")
    cax = fig.add_axes([0.44, 0.2, 0.012, 0.45])
    cb = fig.colorbar(plt.cm.ScalarMappable(cmap=cmap), cax=cax)
    cb.set_ticks([0, .5, 1])
    cb.set_ticklabels(["0%", "50%", "100%"])
    cb.ax.tick_params(labelsize=8)
    lim = 1.1
    has = static_n > 0
    hold = 4

    def frame(f):
        k = min(f // hold, len(starts) - 1)
        val = per_node[k]
        ax.clear()
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.axis("off")
        order = np.argsort(np.nan_to_num(val[has], nan=-1))
        ph, vh = pos[has][order], val[has][order]
        ax.scatter(pos[~has, 0], pos[~has, 1], s=3, c="#e6e6e6", linewidths=0)
        ax.scatter(ph[:, 0], ph[:, 1], s=7, c=cmap(vh), linewidths=0)
        ax.set_title(f"Start: {cm_date(starts[k])} (day {sday[k]:.0f})\n"
                     f"R from this start = {R[k]:.0%}", fontsize=11)
        mr.set_data(sday[:k + 1], R[:k + 1])
        ms_.set_data(sday[:k + 1], Rs[:k + 1])
        hr.set_ydata([R[:k + 1].mean()] * 2)
        hs.set_ydata([Rs[:k + 1].mean()] * 2)
        rtxt.set_text(f"mean so far:  R = {R[:k + 1].mean():.0%} (real)   "
                      f"{Rs[:k + 1].mean():.0%} (P1)")
        return []

    frames = list(range(len(starts) * hold)) + [len(starts) * hold - 1] * 10
    save(FuncAnimation(fig, frame, frames=frames), "gif_cm_reach", fps=6)


# ---------------------------------------------------------------- citations

CIT = ROOT.parent / "final_project" / "data" / "processed" / "CIT"


def gif_cit():
    import networkx as nx
    ev = pd.read_csv(CIT / "events.csv")  # u cites v, t = year of u
    nodes = pd.read_csv(CIT / "nodes.csv", usecols=["id", "year"])
    year = nodes.set_index("id")["year"]
    indeg = ev.v.value_counts()
    top = indeg.index[:1500]                       # most-cited papers by 2020
    keep = set(top)
    sub = ev[ev.u.isin(keep) & ev.v.isin(keep)]
    cache = OUT / ".cit_layout_v2.npy"
    if cache.exists():
        p = np.load(cache)
    else:
        g = nx.Graph()
        g.add_nodes_from(top)
        g.add_edges_from(sub[["u", "v"]].itertuples(index=False, name=None))
        d = nx.spring_layout(g, seed=1, iterations=80, k=1.8 / np.sqrt(len(top)))
        p = normalise(np.array([d[i] for i in top]))
        OUT.mkdir(parents=True, exist_ok=True)
        np.save(cache, p)
    pos = dict(zip(top, p))
    top_year = year.loc[top].to_numpy()
    tid = {k: i for i, k in enumerate(top)}

    years = np.arange(1975, 2021)
    n_cum = np.array([(year <= y).sum() for y in years])
    e_cum = np.array([(ev.t <= y).sum() for y in years])
    ok = (n_cum > 0) & (e_cum > 0)
    slope = np.polyfit(np.log(n_cum[ok & (years >= 1985)]), np.log(e_cum[ok & (years >= 1985)]), 1)[0]
    age = (ev.t - ev.v.map(year)).to_numpy()
    ev_t = ev.t.to_numpy()
    cited_top = ev.v.map(tid)
    print(f"gif_cit: densification exponent E ~ N^{slope:.2f} (from 1985)")

    fig = plt.figure(figsize=(11, 6))
    ax = fig.add_axes([0.0, 0.03, 0.47, 0.84])
    a1 = fig.add_axes([0.57, 0.58, 0.4, 0.3])
    a2 = fig.add_axes([0.57, 0.1, 0.4, 0.3])
    a1.loglog(n_cum[ok], e_cum[ok], color="#cccccc", lw=1.5)
    a1.set_xlabel("papers so far, N")
    a1.set_ylabel("citations so far, E")
    a1.text(.03, .92, f"E ∝ N^{slope:.2f}  (>1: densifies)", transform=a1.transAxes, fontsize=10)
    l1, = a1.loglog([], [], color=REAL, lw=2.4)
    d1, = a1.loglog([], [], "o", color="#d62728")
    bins = np.arange(-.5, 31, 1)
    a2.set_xlim(-.5, 30)
    a2.set_ylim(0, .2)
    a2.set_xlabel("age of the cited paper (years)")
    a2.set_ylabel("share of this year's\ncitations")
    fig.suptitle("Lesson 6: the citation network grows, densifies and favours recent work",
                 fontsize=14, weight="bold")
    fig.text(.235, .02, "1,500 most-cited papers by 2020 · size = citations received so far",
             ha="center", fontsize=9, color="#555")

    def frame(k):
        y = years[k]
        ax.clear()
        ax.set_xlim(-1.08, 1.08)
        ax.set_ylim(-1.08, 1.08)
        ax.set_aspect("equal")
        ax.axis("off")
        old = sub[sub.t < y]
        new = sub[sub.t == y]
        for part, col, lw in ((old, (0.09, 0.25, 0.37, .05), .4), (new, (0.84, 0.15, 0.16, .5), .6)):
            if len(part):
                segs = np.stack([np.array([pos[a] for a in part.u]), np.array([pos[b] for b in part.v])], 1)
                ax.add_collection(LineCollection(segs, colors=[col], lw=lw))
        alive = top_year <= y
        cites = np.bincount(cited_top[(ev_t <= y) & cited_top.notna()].astype(int),
                            minlength=len(top))
        ax.scatter(p[alive, 0], p[alive, 1], s=2 + cites[alive] * .25,
                   c=np.where(top_year[alive] == y, "#d62728", REAL), alpha=.75, linewidths=0)
        ax.text(0, 1.1, str(y), ha="center", fontsize=18, weight="bold")
        l1.set_data(n_cum[:k + 1][ok[:k + 1]], e_cum[:k + 1][ok[:k + 1]])
        d1.set_data([n_cum[k]], [e_cum[k]])
        a2.cla()
        h, _ = np.histogram(age[ev_t == y], bins=bins)
        a2.bar(np.arange(31), h / max(h.sum(), 1), width=.85, color=THIRD)
        a2.set_xlim(-.5, 30)
        a2.set_ylim(0, .2)
        a2.set_xlabel("age of the cited paper (years)")
        a2.set_ylabel("share of this year's\ncitations")
        a2.set_title(f"citations made in {y}: {h.sum():,}", fontsize=10)
        return []

    frames = list(range(len(years))) + [len(years) - 1] * 8
    save(FuncAnimation(fig, frame, frames=frames), "gif_cit", fps=4)


if __name__ == "__main__":
    jobs = {"warmup": gif_warmup, "window": gif_window, "day": gif_day, "sir": gif_sir,
            "cm_sir": gif_cm_sir, "cm_reach": gif_cm_reach, "cit": gif_cit}
    for name in sys.argv[1:] or jobs:
        jobs[name]()
