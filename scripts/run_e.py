"""Reproduce all of member E's results (M4 and M3b on PS and CM), then the figures.

Runs sequentially because every experiment writes into results/e_summary.csv.
Takes about 45 minutes on a laptop; most of it is the 5-min PS windows.

Usage
  python scripts/download_e.py
  python scripts/run_e.py
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N_NULL = "20"

MAIN = {"PS": "15min", "CM": "7D"}
WIDTHS = {"PS": ["5min", "15min", "60min"], "CM": ["1D", "7D", "30D"]}
GAMMAS = ["0.5", "1", "2"]

jobs = []
for ds in ["PS", "CM"]:
    jobs.append(["m3b_closeness.py", "--dataset", ds, "--n-null", N_NULL])
    for w in WIDTHS[ds]:
        for g in GAMMAS:
            job = ["m4_communities.py", "--dataset", ds, "--width", w, "--gamma", g, "--n-null", N_NULL]
            if w == MAIN[ds] and g == "1":
                job.append("--multislice-out")
            jobs.append(job)
jobs.append(["plot_e.py"])

for k, job in enumerate(jobs, 1):
    t = time.time()
    print(f"[{k}/{len(jobs)}] {' '.join(job)}", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / job[0]), *job[1:]], check=True,
                   stdout=subprocess.DEVNULL)
    print(f"    done in {time.time() - t:.0f} s", flush=True)
