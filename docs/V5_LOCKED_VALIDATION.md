# V5 locked validation: no-peek final test

## Purpose

V4 is a development holdout. Its test results have been inspected while improving the independent InsePi observability observer, so V4 must **not** be presented as the final untouched validation in a methods paper.

V5 is reserved for a single final falsification test after the PolliPi and InsePi algorithms are frozen.

## Seed commitment

No V5 random seed is chosen manually. After both method branches are frozen, derive the V5 seed registry from the immutable source commits:

```text
material = (
  "pollipi-insepi-v5-locked-validation\n"
  + pollipi_commit_sha + "\n"
  + insepi_commit_sha + "\n"
  + factorial_v4_world_fingerprint
)
digest = SHA256(material)
```

Successive 8-byte chunks of the digest (and SHA256 counter extensions when more entropy is required) become the V5 seeds. The commits therefore determine the validation worlds; the developer cannot choose favourable seeds after seeing outcomes.

## Freeze rule

Before V5 is generated:

1. PolliPi biological-evidence logic is frozen.
2. InsePi observability logic and all calibration procedures are frozen.
3. Disagreement allocation logic is frozen.
4. Equal-budget endpoints and ablations are frozen.
5. V5 renderer rules are frozen.
6. Both commit SHAs are recorded in the manuscript ledger.

After V5 is run, **no method parameter may be changed in response to V5**. A failure narrows or falsifies the manuscript claim; it does not trigger another V5 tuning cycle.

## Renderer shift relative to V4

V5 must not merely resample V4. It should use a distinct but mechanistically related image generator:

- non-sinusoidal background texture and multiple spatial scales;
- non-Gaussian local events with varied size, contrast and trajectory;
- non-periodic coherent vegetation motion;
- subpixel-like or irregular camera displacement approximated without exposing latent motion to either observer;
- spatially heterogeneous illumination and moving shadow;
- partial and off-centre occlusion;
- anisotropic blur / smear rather than only symmetric smoothing;
- variable clutter number, size and overlap;
- lens droplets / contamination at locations not seen in V4;
- mixed disturbances at strengths outside the V4 calibration grid;
- altered event prevalence.

The two repositories may share V5 rendered pixels and truth manifests, but they must not share decision logic.

## Pre-registered V5 comparisons

At minimum, compare these equal-budget policies:

- uniform;
- PolliPi candidate-priority;
- InsePi audit-priority;
- candidate OR risky;
- candidate AND risky;
- structured disagreement-priority.

Budgets: 10%, 25%, and 50%.

Primary endpoints:

- hidden observation-error recall;
- true-event recovery;
- missed-event audit yield;
- false-event audit yield;
- attribution-error audit yield;
- captures per recovered hidden error;
- disturbance-distribution total-variation distortion.

## Pass condition for the strong methods claim

The strong claim is supported only if structured disagreement lies on a useful Pareto frontier across the locked V5 tests and provides information not reproduced by either single observer or the simple OR/AND ablations.

It does **not** need to maximise every endpoint. A credible result can trade some raw event recovery for substantially better hidden-error discovery at the same resource budget, provided the trade-off is stable across prevalence and disturbance shifts.

## Failure condition

The strong claim is narrowed or rejected if:

- disagreement is dominated by a single observer across V5 budgets;
- any gain is reproduced by simple OR;
- gains disappear under shifted event prevalence;
- clean-scene false-audit cost eliminates the hidden-error benefit;
- the result depends on a single disturbance family;
- either repository fails pixel/world provenance checks.

V5 is intentionally one-shot. Its scientific value comes from being able to reject the architecture after development, not from being another tuning benchmark.
