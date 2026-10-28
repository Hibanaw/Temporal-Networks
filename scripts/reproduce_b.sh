#!/usr/bin/env bash
# Portable sequential entry point. On HPC, run through an allocated compute job.
set -euo pipefail
cd "$(dirname "$0")/.."
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg
task_python=${PYTHON:-python3}
mkdir -p results/b figures data/raw
"$task_python" -m unittest discover -s tests -v
"$task_python" scripts/download_b.py
"$task_python" src/cs_data.py --archive data/raw/dblp_v14.tar.gz --out data/processed/CIT
"$task_python" scripts/run_b.py --workers 4
"$task_python" scripts/plot_b.py
"$task_python" scripts/plot_b_report_diagnostics.py
"$task_python" scripts/verify_b.py
