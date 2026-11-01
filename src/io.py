"""A's canonical PS/CM readers, cleaning, processed data and period settings."""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
PS_DIR = RAW / "primaryschool"
CM_DIR = RAW / "collegemsg"


@dataclass
class Dataset:
    name: str
    events: pd.DataFrame
    labels: Optional[dict]  # ground-truth community labels, or None
    directed: bool
    closeness_starts: list  # start times for temporal closeness
    min_events: int         # snapshot windows with fewer events are dropped


def load_primaryschool(contacts_path, metadata_path):
    """Undirected 20-s contacts (u < v) and node labels (id, label).

    t counts seconds from midnight of the first day.
    """
    raw = pd.read_csv(contacts_path, sep="\t", header=None, names=["t", "i", "j", "ci", "cj"])
    raw = raw[raw["i"] != raw["j"]]
    # Store each pair as u < v so (i, j, t) and (j, i, t) dedupe.
    events = pd.DataFrame({
        "u": raw[["i", "j"]].min(axis=1),
        "v": raw[["i", "j"]].max(axis=1),
        "t": raw["t"],
    }).drop_duplicates().sort_values(["t", "u", "v"]).reset_index(drop=True)
    meta = pd.read_csv(metadata_path, sep="\t", header=None, names=["id", "label", "gender"])
    return events, meta[["id", "label"]]


def load_collegemsg(path):
    """Directed messages (u sends to v); t is a Unix timestamp in seconds."""
    events = pd.read_csv(path, sep=" ", header=None, names=["u", "v", "t"])
    events = events[events["u"] != events["v"]].drop_duplicates()
    return events.sort_values(["t", "u", "v"]).reset_index(drop=True)


def load_raw(name):
    if name == "PS":
        events, nodes = load_primaryschool(PS_DIR / "primaryschool.csv.gz", PS_DIR / "primaryschool_metadata.txt")
        students = {n: c for n, c in zip(nodes["id"], nodes["label"]) if c != "Teachers"}
        # Every full hour from 09:00 to 16:00 on both school days.
        starts = [d * 86400 + h * 3600 for d in (0, 1) for h in range(9, 17)]
        return Dataset("PS", events, students, False, starts, 100)
    if name == "CM":
        events = load_collegemsg(CM_DIR / "CollegeMsg.txt.gz")
        t0, t1 = int(events["t"].min()), int(events["t"].max())
        # 20 evenly spaced starts over the first 90% of the period, so late starts still have events ahead.
        starts = np.linspace(t0, t0 + 0.9 * (t1 - t0), 20).astype(int).tolist()
        return Dataset("CM", events, None, True, starts, 50)
    raise ValueError(f"unknown dataset {name}")


PROCESSED = RAW.parent / "processed"


def load(name, period="full"):
    """Read canonical processed data if available, otherwise clean raw input.

    Half periods use the midpoint in elapsed observation time, not event count.
    Starts retain PS clock-hour convention and CM's 20-point convention.
    """
    import json
    folder = PROCESSED / name
    if (folder / "events.csv").exists() and (folder / "data_card.json").exists():
        card = json.loads((folder / "data_card.json").read_text())
        events = pd.read_csv(folder / "events.csv")
        nodes = pd.read_csv(folder / "nodes.csv")
        labels = dict(zip(nodes.id, nodes.label)) if "label" in nodes else None
        if labels:
            labels = {n: c for n, c in labels.items() if c != "Teachers"}
        ds = Dataset(name, events, labels, card["directed"], card["closeness_starts"], card["min_events"])
    else:
        ds = load_raw(name)
    if period != "full":
        if period not in ("first", "second"):
            raise ValueError(period)
        lo, hi = int(ds.events.t.min()), int(ds.events.t.max())
        mid = lo + (hi - lo) / 2
        ds.events = ds.events[ds.events.t < mid if period == "first" else ds.events.t >= mid].copy()
        lo, hi = int(ds.events.t.min()), int(ds.events.t.max())
        if name == "PS":
            ds.closeness_starts = [t for t in ds.closeness_starts if lo - 3600 <= t < hi]
        else:
            ds.closeness_starts = np.linspace(lo, lo + .9 * (hi-lo), 20).astype(int).tolist()
    return ds


def prepare(name):
    """Write cleaned shared events, nodes, and provenance card; return the card."""
    import hashlib
    import json
    ds = load_raw(name)
    folder = PROCESSED / name
    folder.mkdir(parents=True, exist_ok=True)
    ds.events.to_csv(folder / "events.csv", index=False)
    ids = sorted(set(ds.events.u) | set(ds.events.v))
    nodes = pd.DataFrame({"id": ids})
    if name == "PS":
        _, meta = load_primaryschool(PS_DIR / "primaryschool.csv.gz", PS_DIR / "primaryschool_metadata.txt")
        nodes = nodes.merge(meta, on="id", how="left")
    nodes.to_csv(folder / "nodes.csv", index=False)
    inputs = list(PS_DIR.glob("*")) if name == "PS" else list(CM_DIR.glob("*"))
    card = dict(dataset=name, directed=ds.directed, n_nodes=len(nodes), n_events=len(ds.events),
                t_min=int(ds.events.t.min()), t_max=int(ds.events.t.max()), time_unit="second",
                resolution_s=20 if name == "PS" else 1, closeness_starts=ds.closeness_starts,
                min_events=ds.min_events, cleaning="remove self-loops and duplicate (u,v,t); canonical undirected pairs",
                source="https://www.sociopatterns.org/datasets/primary-school-temporal-network-data/" if name == "PS" else "https://snap.stanford.edu/data/CollegeMsg.html",
                license="CC BY-NC-SA" if name == "PS" else "See SNAP source terms",
                observation_boundary="untrimmed cleaned event interval; retain partial windows",
                sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
    (folder / "data_card.json").write_text(json.dumps(card, indent=2)+"\n")
    return card
