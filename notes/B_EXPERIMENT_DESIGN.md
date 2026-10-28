# B experiment design (fixed before observing outcomes, 2026-10-27)

Scope: PLAN.md v3.1, M1 + M2c-1/2/3/4, P3a/P3b. No modifications to other members' analyses.

## Data and graph

Official AMiner DBLP Citation V14 (2023-01-31), downloaded 2026-10-27. Stream the entire tar archive, select database venues using the explicit whitelist/patterns in src/cs_data.py. Select by venue only, never by citation outcome. Retain all selected publications in 1960--2020, including isolates. Analyze the induced graph: edges are observable citations within selected venues, not total/global citations. Version, archive checksum, record counts, filtering counts and venue counts must be saved. No redistributable licence is inferred from "research purpose only".

Primary edges: distinct u->v, t=publication year(u), year(v)<year(u). Exclude future references, self-loops and year ties; save ties separately for sensitivity. This avoids an arbitrary within-year order and guarantees a DAG. Older nodes and their observed edges initialize degree histories; primary inferential years are 1990--2020. Missing pre-1960 history and references outside the selected venues remain limitations.

## M1 / H1

For every year, compare current-year citation edges to cumulative citation edges on the SAME set of born nodes. Directed density E/[N(N-1)], mean total degree 2E/N; clustering and connected components on the weak undirected projection. Report denominator definitions and isolates. Plot metrics, activity, and 1/2/5/10-year trailing windows. Define window sensitivity (max-min)/mean over the window grid (for each metric, averaged over full-window endpoints).

## M2c-1 / H4a

Freeze in-degree at the start of each year. Count each degree class's at-risk nodes n_yk and incoming hits h_yk. Fit conditional target likelihood proportional to n_yk (k+1)^alpha, conditioning on yearly total references. The +1 permits zero-degree targets; test offset 0.5 and 2 as sensitivity. Save empirical relative kernel hits / uniform expected hits. Bootstrap complete citing-year blocks (400 draws); it is descriptive dependence-aware uncertainty, not independent paper sampling. P3a tests departure from uniform target selection; P3b retains empirical age preference but removes degree preference. Positive alpha alone is not a causal estimate of PA.

## M2c-2 / H4b

Ages 1--60 years, conditional-on-citing-year likelihood proportional to number of available targets at age a times f(a). Fit discrete-grid lognormal kernel, exponential decay, power-law decay and uniform baseline, compare AIC on the identical support and events. P3b weights use a nonparametric age-only conditional target likelihood with a separate normalization for each citing year. Pooled observed/exposure age rates initialize this fit; they are not used as the final weights because annual normalizers vary. It is calibrated from these data, not independent evidence for ageing. Cohort analyses: targets born 1970--1989, 1990--1999, 2000--2009; compare eligible support explicitly. Preferential attachment/fitness can still confound marginal ageing.

## M2c-3 / H4c

OLS descriptive log E vs log N over 1990--2020, all cumulative nodes including isolates. Repeat 1990--2004, 2005--2020 and cutoff 2015, and year bootstrap CI (descriptive, cumulative data are correlated). Diameter = 90th percentile of shortest paths in weak largest connected component, 128 uniformly sampled sources, fixed seeds; save component size and number sampled. Evaluate every 5 years and null counterparts. Directed distances would mean a different question. P3 fixes E(t), N(t), so exponent a is exactly invariant and cannot establish a significant PA/ageing mechanism. Diameter sampling sensitivity 64/256 sources.

## M2c-4 / H4d

WSB c(t)=m[exp(lambda Phi((ln t-mu)/sigma))-1], fix m to mean induced-graph references per paper in the historical training period (<=1989), not global reported citation counts. Bounded multistart log1p least squares; lambda in [0.0001,10], mu in [-3,5], sigma in [0.2,3]; record boundary hits and failed fits.

Full-history characterization: 1990--2005 cohort with >=10 observed citations through age 15, uniformly select up to 500 (seed 5253), fit ages 1--15. Report parameter distributions and in-sample collapse, which is not independent validation.

Forecasting: 1990--2005 publications with >=5 citations in years 1--5 (selection uses training data only), uniformly select up to 500; predict cumulative citations at age 15 and observed endpoint (<=2020). Fit ages 1--5 only. Compare (1) WSB, (2) no-ageing PA c(t)=m[exp(r*t)-1], r fit from the same 5 years, and (3) linear c5*t/5. Same papers and horizons, save individual predictions, MAE/RMSLE/median absolute error, paired bootstrap MAE differences (1000). Include all successful fits, even boundary fits, with a secondary interior-only check. No claim to predict unobserved lifetime totals; observed final is censored.

## Randomization and robustness

20 independent realizations per P3 kind, seeds 5253..5272 and 15253..15272. Distinct targets without replacement, no self loops, only strictly older targets; preserve exact source and event timestamps and per-source out-degree. Save each edge list compressed, seeds, and checksums. Report null mean / sample SD and empirical upper-tail p=(1+#null>=real)/(1+20); minimum resolution 1/21, do not overstate significance. Compare first 10 vs all 20 samples. Unit tests use hand-built DAGs and known synthetic WSB histories. Main claims conditional on this one database-venue induced network; venue selection sensitivity on a core subset (SIGMOD/VLDB/PVLDB/ICDE) and same-year edges for structural metrics.

## Source references

- AMiner official schema/download: https://www.aminer.cn/aboutus/en-US/articles/655db2202ab17a072284bc0c
- Jeong et al. (2003), https://www.barabasi.com/media/pub_imports/files/117.pdf
- Leskovec et al. (2005), https://www.cs.cmu.edu/~jure/pubs/powergrowth-kdd05.pdf
- Wang, Song & Barabasi (2013), Eq. 3, https://www.barabasi.com/media/pub_imports/files/434.pdf
- WSB caveats: https://arxiv.org/abs/1405.1574

### Pre-measurement refinement, 22:50 SGT

While the official archive was still downloading and before any formal graph measurements were available, P3b calibration was strengthened to maximize the nonparametric conditional age-only target likelihood with citing-year normalizers. Its fitted expected age totals are saved in `results/b/p3_age_weights.csv`. A regression test verifies improvement over pooled exposure-ratio initialization. The test suite now has 13 passing tests. WSB full-history collapse now includes RMSE and maximum-deviation diagnostics; these remain descriptive fitted-sample diagnostics, not universal-collapse significance tests.
