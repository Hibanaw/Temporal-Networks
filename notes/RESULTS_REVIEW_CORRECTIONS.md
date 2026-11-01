# Results review corrections

This revision changes derived summary semantics and interpretation, using the
saved measurements. It does not rerun or alter the scientific experiment tables.

## Cross-network schema

The key is `(hypothesis, dataset, reference)`. Each finite `effect` is exactly
`value - null_mean` in the underlying metric's units. H1 has no null; its effect
is undefined and its value is descriptive. H2--H6 use null differences, including
PA alpha versus P3a for H4 and both P1/P2 for H6. H7 uses actual peak delays in
seconds for value/null_mean/effect, and exposes both P1/P2 comparisons in `ratio`.
A ratio must not be read as a seconds-valued difference, and a shared operator
does not create an overall scale across hypotheses.

Primary H3 effects: PS -0.147071, CM +0.026726; H5: PS -0.095900, CM +0.098244.
H6 effects vs P1: PS -0.133968, CM -0.120388; vs P2: -0.133967, -0.031426.
H7 primary ratios vs P1/P2: PS 1.160385/1.213588, CM 0.888071/0.995011.

## Observation-sensitive interpretation

- CM H3: full-period +0.026726 becomes -0.039/-0.022 in the halves.
  This does not establish generally more persistent real messaging ties.
- PS H2: excess B is +0.016252 over the full interval, +0.116293/+0.120447
  in the halves. Its absolute full-period magnitude is small, despite a narrow
  null distribution. The temporal scope must accompany the verdict.
- P1-invariant repeated-event fractions and CM repeated-tie fraction are
  descriptions/construction checks; near-zero null SD is not evidence for H3.
- H1 grids and definitions differ; density and total-degree sensitivity duplicate
  the same fixed-denominator effect. PS clustering sensitivity is 1.628100 full,
  0.920717/0.959174 in the halves. No cross-dataset sensitivity ranking follows.
- R includes remaining observation time after each start and timetable effects.
  It is not a pure topological effect or an observation-boundary-free timing effect.

## SIR interpretation

- PS peak slowing is conditional on beta/duration and the observation interval;
  the lowest beta has essentially no P1 peak effect. Lower final size is a
  separate result from a delayed peak and is not labelled statistically significant
  without a stated test. Primary real/P1 sizes are 0.629360/0.776409 and major
  outbreak probabilities 0.860/0.90825, so qualifying seed subsets differ.
- CM does not support a general slowdown: full-period peaks occur earlier than
  P1 and close to P2, and the half-size contrast can have the opposite sign.
  At beta=.5, peak/half-final-size ratios to P1 are 0.924/1.061. Half-size refers
  to each trajectory's own final size, not a common infected-count target.
- CM's primary second-half setting still has probability 0.360 of major outbreaks;
  undefined peak ratios occur in two weaker settings, not in every setting.
- PS full-period mean final fraction is 0.629360 versus 0.821398/0.787647 in the
  halves. Reselecting seeds from the first 70% of each interval's event stream
  changes seed populations and residual horizons. Schedule/censoring effects are
  plausible explanations but cannot be separately attributed from these CSVs.
- Twenty-versus-sixty-null stability is different from observation/parameter
  robustness. Dataset-specific SIR grids are intentional; WSB publication-cohort
  checks are not observation-half validation.

## Verification

Synthetic regression checks cover effect subtraction, no invented H1 null,
H7 reference separation/units and undefined peaks. The full suite passes 55 tests
in the prepared environment, including B's ijson-dependent tests. Summary values
are cross-checked against the source owner tables; manuscript generation and PDF
rendering are validated separately.
