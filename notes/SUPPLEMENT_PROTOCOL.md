# Supplement protocol

Canonical source: this repository, branch `supplement-experiments`.
Manuscript: separate GitHub repository `Hibanaw/Temporal-Networks-Report`.
The abandoned Overleaf checkout is not the manuscript delivery target.

## Execution

All significant experiments use CBIS PBS `ais_cpu`; no GPU is required.
D primary: PS/CM, Real + 20 P1 + 20 P2, 200 event-start seeds, four SIR settings.
More-null comparison nests those same seeds within 60 P1/P2 networks.
The first/second observation periods split elapsed time, not event count.
The corrected SIR peak groups simultaneous infections/recoveries and selects
the earliest maximum; `checkpoints_v2` avoids reusing the earlier peak convention.
Numba acceleration preserves strict-time path rules and the supplied SIR draws.

## Data and definitions

`src/io.py` is imported as `src.io` because Python reserves top-level `io`.
`e_datasets.py` delegates to it for backward compatibility; D and E now read the
same processed events, nodes and cards as A. Existing E results use identical
cleaning. PS has 242 nodes/125,773 events; CM 1,899 nodes/59,798 events.

M1 includes empty windows and the trailing partial window, anchors at the first
event and retains all nodes observed in the selected period. CM clustering uses
an undirected projection; density/degree preserve direction. Width sensitivity
is range/mean across width-averaged metrics. CIT's original trailing-window
convention remains documented separately; these grid-dependent effects do not
constitute a universal ranking of network types.

C reconstructs the delivered report definitions: dyad-pooled gaps, PS contiguous
20-second records collapsed for B/M and repetition, uncollapsed records for
lifetime and Jaccard, memory pairs within dyads, null seeds 0--19 (and 0--59).
Observed B/M, episode repetition and default Jaccard agree with the historical
report. Canonical event ordering can change individual seeded null realizations;
new null means and SDs are regenerated rather than copied from rounded report values.
Coincident events produced by P1 remain present (raw duplicates are removed only
at ingestion). PS lifetime is
recomputed on canonical undirected pairs; the historical value is not copied.

H7 is a ratio of mean peak delays conditional on >=5% outbreaks in each network.
It compares different qualifying seed populations and cannot be read as an
unconditional causal effect on epidemic speed. No-major-outbreak peak values
are undefined. `null_mean=1` on ratio rows is the reference; `null_std` reports
spread of real/null ratios, not seed uncertainty or a confidence interval.

## Reproduction

1. Install `requirements-supplement.txt`; obtain source datasets with `scripts/download_e.py`.
2. `python scripts/prepare_a.py`
3. `python scripts/run_d.py --workers 10 --seeds 200 --nulls 20`
4. `python scripts/run_ac.py --nulls 60`
5. Repeat D with 60 nulls, save its summary as `results/d/summary_60.csv`, then
   rerun with 20 (cached) to restore the primary tables.
6. D halves: `--period first` / `--period second`, each 20 nulls.
7. `python scripts/run_e_robustness.py`; `python scripts/run_b_robustness.py`.
8. `python scripts/make_summary_table.py`; `python scripts/summarize_robustness.py`.
9. `python scripts/plot_supplement.py` and
   `python scripts/sync_report_results.py --report ../Temporal-Networks-Report`.

PBS deployment scripts remain local under `hpc/`, following the repository's
pre-existing exclusion rule. Checkpoints/raw data are not committed. Per-network
CSV outputs and source/environment hashes form the reproducible delivery.
