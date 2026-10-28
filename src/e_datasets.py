"""Datasets for member E's experiments (M4, M3b): PS and CM.

Reads the raw files downloaded by scripts/download_e.py. To be switched to A's
io.py and data/processed/ once those are delivered; the output already follows
the shared interface: events with columns u, v, t (integer seconds).
"""
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


def load(name):
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
