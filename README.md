# Temporal Networks — PC5253 Final Project

**How Much Does Time Matter?** A comparative study of aggregation, temporal patterns,
structural evolution, and dynamics in real-world temporal networks.

This repository follows [PLAN.md](PLAN.md), version 3.1. The completed implementation
is member **B's five citation-network experiments**. PS (primary-school contacts)
and CM (CollegeMsg) work remains pending; report placeholders are not measurements.

## Project layout

| Path | Contents |
|---|---|
| `src/cs_data.py` | Streaming AMiner parser, frozen database-venue selection, graph cleaning |
| `src/growth.py` | Aggregation, preferential attachment, ageing, densification, diameter, WSB, P3 |
| `scripts/` | Download, experiment runner, plots, formal verification |
| `tests/test_b.py` | 13 synthetic known-answer and null-preservation tests |
| `data/processed/CIT/data_card.json` | Dataset metadata, selection, filtering, and counts |
| `results/b_summary.csv` | Shared `dataset,metric,value,null_mean,null_std` interface |
| `results/b/` | Measured metric tables, fitted parameters, robustness, and provenance |
| `figures/` | Reproducible measured PDF/PNG plots |
| `report/` | Self-contained LaTeX sources and compiled reports; snapshot from Overleaf |
| `notes/` | Experimental design, source notes, historical execution record |

See [B_RESULTS.md](B_RESULTS.md) for findings and [docs/B_DELIVERY.md](docs/B_DELIVERY.md)
for the requirement-to-artifact map. Modules assigned to other members are not stubbed
out as completed implementations.

## Setup and checks

Run commands from the repository root. Python 3.9 or newer is required; the original
HPC execution used Python 3.9. Exact installed packages are recorded in
`results/b/environment.lock.txt`.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-b.txt
python -m unittest discover -s tests -v
```

## Reproduce B's experiments

```sh
bash scripts/reproduce_b.sh
```

This downloads and SHA-256 verifies the approximately 6.08 GB official AMiner V14
archive, streams the full corpus, runs the five analyses, generates plots, and audits
all 40 randomized graphs. Allow space for both the assembled archive and resumable
download parts. Scientific stages run sequentially, with up to four CPU workers
within a stage. There is no GPU requirement.

To run only a particular step:

```sh
python scripts/download_b.py
python src/cs_data.py --archive data/raw/dblp_v14.tar.gz --out data/processed/CIT
python scripts/run_b.py --workers 4
python scripts/plot_b.py
python scripts/plot_b_report_diagnostics.py
python scripts/verify_b.py
```

`scripts/run_b.py --stage real|wsb|null|summary` reruns an individual stage. The
summary stage requires the real, WSB, and null outputs first. The fixed master seed
is 5253; each P3 family has 20 independently seeded samples.

On a cluster, execute the workflow on an allocated compute node through its
scheduler. Scheduler/HPC scripts are intentionally excluded from this repository.
The saved job records describe the historical run, not a deployment interface.

## Rebuild figures or report from saved results

Most plots use the committed tables. `b_activity` additionally requires the processed
graph, which is rebuilt from the original archive.

```sh
python scripts/plot_b.py
python scripts/plot_b_report_diagnostics.py
cd report
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

LaTeX requires the CVPR dependencies, including `placeins`. The report folder has its
own figure copies. Its GitHub history is separate from the existing Overleaf history;
this repository contains no nested `.git` directory.

## Data and interpretation

Raw and processed edge/node datasets, randomized edge lists, caches, local backups,
and HPC scripts are excluded. Read [data/README.md](data/README.md) before downloading
or redistributing AMiner data. No dataset redistribution rights are inferred.

The selected graph has 19,150 papers and 73,269 citations to strictly older papers.
Year ties are structural sensitivity data only. Citation counts are within-subgraph
counts. The results support sublinear degree preference and age dependence, with
densification but no detected effective-diameter shrinkage. WSB's compact in-sample
fit does not establish a forecast MAE advantage over linear extrapolation.

P3 preserves each year's node and edge totals, so densification invariance is a
construction property. Forecast selection uses only the training window; the
15-year and 2020 targets are observed citation totals, not lifetime citations.

No project code licence has been chosen; third-party report style files retain their
original notices.
