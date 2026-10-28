# B execution status

Started 2026-10-27 (Asia/Singapore). Latest plan: v3.1, five B experiments.

- Host: Vanda, personal-tianqi.hu, CPU only.
- Work directory: /scratch/tianqi.hu/runs/pc5253-b-20261027
- Prepare PBS: 1500299.stdct-mgmt-02 (replaces earlier download attempts; existing bytes retained).
- Raw source: official AMiner V14, 6,079,589,707 bytes, resumable validated HTTP Range download.
- Main job: dependent on successful preparation; 1500300.stdct-mgmt-02 (afterok:1500299), also recorded in hpc/submissions.txt.
- Local known-answer unit tests: 13 passed.
- Synthetic end-to-end smoke: /private/tmp/pc5253-b-smoke (never a source of reported scientific results).
- Formal measurements: pending source download / preprocessing. No expected values have been labeled as measurements.

Design: notes/B_EXPERIMENT_DESIGN.md. All scientific workloads use PBS compute nodes.
Important code/results will be copied to the local OneDrive-backed project and persistent HPC home; scratch is not archival storage.

## Checkpoint 22:45 SGT

- Prepare now uses 8 MB ranges and reuses original 64 MB partial segments; current logs show steady forward progress past segment 226 (~2 GB of 6.08 GB downloaded at 22:41).
- Main experiment job 1500300 depends on 1500299; the PBS dependency hold is expected, not a scheduling failure.
- All 12 known-answer unit tests passed (saved in local_tests.log); synthetic complete pipeline and all seven plot groups passed.
- Shared report methods updated from 16 to 19 experiment pairs, H4 row uses M2c-1--4/P3. B methods added via sections/methods_b.tex. Other members' Results placeholders are untouched.
- Shared main.tex compiled to /private/tmp/pc5253-report-check/main.pdf; B methods visually inspected, no overfull boxes in B text. Existing other-member placeholder figures cause separate 6.8 pt overfull boxes; not altered.
- New scripts/verify_b.py audits all formal artifacts and all 40 null graphs once ready. scripts/inspect_b.py prints measured results for interpretation. Run these after main job finishes.
- IMPORTANT: scientific RESULTS and b_report.pdf are NOT READY yet. Do not mark goal complete until data parsed, five experiments / 40 nulls run, actual graphs inspected, report B Results filled, B standalone report compiled/rendered and important outputs archived locally + persistent HPC home.
- Remaining work: wait/check preparation; troubleshoot actual-data failures if any; await main job; rsync processed data/results/figures locally; inspect outputs, write results_b_detail.tex and B portions of results_aggregation.tex/results_evolution.tex + actual CIT data card; create B_RESULTS.md with measured conclusions; compile/render B report and shared report; run verify_b.py; back up raw + processed + outputs to home and local OneDrive-backed project with checksum verification. Raw archive 6.08 GB fits local currently ~23 GB free, HPC home currently 2.1 GB used of known 20 GB quota. Do not treat scratch alone as backup.

## Pre-result method audit

P3b now uses a nonparametric conditional age-only likelihood with year-specific normalizers. 13 known-answer tests pass; the complete 40-null synthetic test passes under the new calibration. WSB full-history collapse includes numerical RMSE / maximum-deviation diagnostics, labeled fitted-sample only. Forecast audit reconstructs selection, c5 and targets directly from raw edges to guard against leakage. Current main job is still 1500300, dependent on live prepare 1500299. Download reached segments above 530 of 725 by 22:59; scientific results remain pending.

## User steering: single serial deployment

User requested one-shot serial deployment of all experiments. Current main is **1500361.stdct-mgmt-02**, afterok:1500299. Previous main 1500300 and separate archive 1500358 were confirmed dependency-held, then replaced/cancelled; no scientific experiment was interrupted. The new main includes all five experiment stages, plots, scripts/verify_b.py, then hpc/b_archive_raw.pbs and persistent results/figures backup. Within-stage computation can use four CPUs, as explained to the user. Future one-shot deployment is `bash hpc/submit_b.sh`. Local raw transfer is active as exec session **78877**; do not restart while live. Full raw archive is assembled, checksum recorded, and AMiner streaming extraction has reached >1.75 million records. Final-report completion remains outstanding.
