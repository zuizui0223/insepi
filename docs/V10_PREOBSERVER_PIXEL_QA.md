# V10 post-freeze pre-observer pixel QA

## Status

**Descriptive quality audit only. Not a preregistered V10 acceptance criterion and not a claim gate.**

This audit was added only after the V10 scientific protocol and canonical real-pixel bytes had already been frozen. It therefore cannot be used to alter the source-video set, frame cadence, perturbation families or tiers, panel assignment, score mappings, budgets, comparators, claim thresholds, or V6 weights.

No PolliPi or InsePi observer output is used here.

## Why this audit exists

Two implementation-independent failure modes could make a real-pixel stress test hard to interpret even before observer execution:

1. the fixed 182/182 disturbance assignment might accidentally concentrate disturbance truth in particular source videos or temporal strata; and
2. a transferred perturbation operator might be effectively a no-op on real pixels, or conversely saturate most of the image.

Because the artifact was already immutable, these checks can only document those properties; they cannot trigger retuning under the same V10 generation.

## Canonical artifact identity

The audit reads the already-frozen artifact from workflow run `32616509747` and requires:

- pixel NPZ SHA-256 `b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66`;
- condition-registry SHA-256 `1689f5ce102abfef722e3e8667e8c6e290a42fe1d4563c1655b7f14520cde393`;
- panel-registry SHA-256 `b1e59cda67977e5ab8d09e1ea28236b442d72c616c92df0c22adca89122cac8a`.

## Panel-assignment diagnostics

Across the 18 fixed family × tier panels:

- mean source-video TV between the disturbed half and the full 364-window panel: **0.05174**;
- maximum source-video TV: **0.09615**;
- mean source-video × temporal-quartile TV: **0.10653**;
- maximum source-video × temporal-quartile TV: **0.14011**;
- panels missing an entire source-video category from the disturbed half: **0/18**.

There is one small stratification gap that should remain visible rather than be repaired post hoc:

- panel `framing_drift:tier0` contains no disturbed window from **video 7, temporal quartile 3**;
- that stratum contains only six of the 364 base windows;
- all six therefore happen to be native in that one fixed panel.

This means the V10 panel assignment is correctly described as a deterministic hash-based balanced-half assignment, **not** as a video/time-stratified randomized design. The main V10 comparison remains paired because every policy is evaluated against the same fixed panel truth and the paired-uniform denominator uses the same assignment. The residual stratum imbalance should nevertheless be reported as a finite-realization limitation of the semi-empirical test.

## Pixel-level perturbation diagnostics

Every one of the 18 family × tier variants differs from its paired native frame for every base window at a nonzero mean absolute pixel level. The smallest observed per-window MAE over all 6,552 perturbed base-window variants is **0.1695**, occurring in the spatially local occlusion family; thus no preregistered variant is a byte-level no-op.

Median paired pixel MAE is nondecreasing across the three frozen intensity tiers for all six families:

| Family | Tier 0 | Tier 1 | Tier 2 |
|---|---:|---:|---:|
| shadow | 8.664 | 15.392 | 22.069 |
| occlusion | 0.253 | 0.455 | 0.650 |
| blur | 10.088 | 16.849 | 19.645 |
| sensor_banding | 5.740 | 10.198 | 14.653 |
| glare | 3.861 | 6.803 | 8.720 |
| framing_drift | 43.250 | 46.895 | 46.967 |

The largest saturation fraction in any single perturbed window is **0.03711** (3.71%). Therefore the stress test is not produced by globally clipping most pixels to 0/255. `framing_drift` has the largest pixel MAE because it relocates nearly the whole image; its tier-1 and tier-2 MAEs are close because the frozen operator uses integer pixel displacements. This is retained rather than smoothed or retuned.

## Interpretation boundary

These diagnostics support only the statement that the frozen real-pixel artifact is non-degenerate and that its panel assignment has modest but nonzero finite-sample stratum imbalance. They do **not** establish observer transfer, allocation benefit, ecological-event accuracy, or a V10 claim level.

The actual V10 scientific result still requires the exact frozen V5 observer commits and must be generated only by the fail-closed manual one-shot after V7 executes first.
