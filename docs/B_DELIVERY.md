# Member B delivery against PLAN.md v3.1

| Plan requirement | Implementation | Saved evidence |
|---|---|---|
| AMiner streaming parse and subfield extraction | `src/cs_data.py` | `data/processed/CIT/data_card.json` |
| M1/CIT: annual, cumulative and window aggregation | `src/growth.py`, `scripts/run_b.py` | `aggregation.csv`, `windows.csv`, `window_sensitivity.csv` |
| M2c-1: prior-year PA kernel and uncertainty | `src/growth.py` | `pa.json`, `pa_kernel.csv`, `pa_bootstrap.csv` |
| M2c-2: age exposure, cohorts and model selection | `src/growth.py` | `age_curve.csv`, `age_fits.json`, `age_cohorts.json` |
| M2c-3: densification and effective diameter | `src/growth.py` | `densification.json`, `diameter_real.csv`, `diameter_null.csv` |
| M2c-4: WSB fits, collapse and five-year forecasts | `src/growth.py`, `scripts/run_b.py` | `wsb_full_parameters.csv`, `wsb_collapse.csv`, `wsb_predictions.csv`, `wsb_summary.json` |
| P3a uniform / P3b conditional age-only nulls | `src/growth.py` | `p3_age_weights.csv`, `null_metrics.csv`, `null_fits.json` |
| Fixed seeds and known-answer tests | `tests/test_b.py` | Master seed 5253; 13 tests |
| Unified owner summary | `scripts/run_b.py --stage summary` | `results/b_summary.csv` |
| Figures from scripts | `scripts/plot_b.py`, `scripts/plot_b_report_diagnostics.py` | Nine PDF/PNG plot groups |
| Robustness | `scripts/run_b.py` | `robustness.json`, `core_venue_structural.csv`, `same_year_structural_sensitivity.csv`, `null_comparison.json` |
| Methods, Results, verdicts and limitations | `report/sections/*b*.tex` and integrated sections | `report/main.pdf`, `report/b_report.pdf`, `B_RESULTS.md` |
| Single invocation with serial stages | `scripts/reproduce_b.sh` | Download → parse → experiments → plots → audit |

Evidence files without a directory prefix in this table are in `results/b/`.

## Shared interfaces

Events use `u,v,t`, with integer years and directed edges. The summary columns are
exactly `dataset,metric,value,null_mean,null_std`. P3 needs publication years for all
nodes, including isolates. Adapt it to the shared `f(events, seed)` interface by
binding node context:

```python
# Run with PYTHONPATH=src, or add src to sys.path in a driver.
from growth import p3, age_rates
rates = age_rates(events, nodes)
P3a = lambda events, seed: p3(events, nodes, seed, "P3a")
P3b = lambda events, seed: p3(events, nodes, seed, "P3b", rates)
```

## Scope and provenance

B's five experiments are complete. The other fourteen planned method–dataset pairs
are not represented as completed work. Report PS/CM expectations remain labelled.

The numerical sources were copied without modification from the completed run.
`results/b/source_sha256_hpc_run.txt` identifies the historical HPC source snapshot;
later plotting helpers may differ. `pbs_completion.txt` and `environment.lock.txt`
record execution provenance. No HPC/PBS scripts are included, per the owner's request.

`notes/B_EXECUTION_HISTORY.md` records historical local and HPC paths; those paths
are provenance, not prerequisites. Checksums in `results/b/validation.json` describe
the archived full run; randomized edge lists must be regenerated before rechecking
them. This GitHub delivery is a selected code/results package, not a copy of the
large-data archival manifest.
