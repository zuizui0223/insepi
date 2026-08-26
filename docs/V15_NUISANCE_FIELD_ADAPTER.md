# V15-v2 nuisance field measurement baseline

## Current problem

The frozen V14b nuisance observer operates on truth-known synthetic `SpatiotemporalSignature` objects. That is sufficient for the closed-world phase experiment, but it is not a field adapter: a real camera clip does not arrive with Pi coordinates or a truth-known spatiotemporal signature.

V15-v2 therefore needs a primary-stream measurement layer before any field nuisance calibration can be attempted.

## What this adapter does

`src/interaction_sensing/nuisance_field_measurement_v15.py` measures an **uncalibrated continuous nuisance-process index** from grayscale primary-stream frames.

Its API receives only:

```text
frames
focal_zone
reference_layout
```

It cannot receive target scores, biological truth, coupling truth, nuisance truth, or observation-support labels.

This keeps the nuisance observer orthogonal to PolliPi and to the V15 truth ledgers.

## Positive process definition

The field baseline asks whether motion has the positive structure expected of an exogenous scene-level process:

1. motion exists in independently chosen reference regions;
2. focal and reference motion co-vary in time;
3. their amplitudes agree rather than only their standardized shapes;
4. the reference process shows quasi-stationary/restorative or spectrally concentrated temporal structure.

The final development index is

```text
(spatial coherence × temporal support × reference motion amplitude)^(1/3)
```

where spatial coherence itself is:

```text
positive correlation × RMS amplitude agreement
```

This explicitly avoids the V14a diagnostic problem in which Pearson correlation alone remained high despite amplitude-scale separation.

## Why localized focal movement is not nuisance

A target-driven flower response can be strongly localized in the focal zone. Under the positive nuisance definition, focal motion with no corresponding reference motion does not become exogenous nuisance merely because the pixels move.

The unit contract therefore requires a localized focal-only sequence to produce zero spatial nuisance coherence and zero final nuisance-process index when the reference region is static.

This does **not** prove that every real localized motion is target-driven. It only prevents the nuisance adapter from defining nuisance as the complement of target evidence or as generic movement.

## Reference-zone provenance

Reference regions must be selected independently of target-observer output. Their selection method is retained in every measurement.

The current adapter does not prescribe one universal field geometry. A later freeze must specify the actual reference-zone construction used for the empirical design and hash that rule before held-out scoring.

## What is deliberately not implemented yet

The continuous process index is **not**:

- a nuisance probability;
- a binary nuisance label;
- a false-event probability;
- a missed-event probability;
- an attribution-error probability;
- a field-calibrated replacement for the frozen V14b nuisance score.

The next development step requires independently labelled nuisance/effect truth from development data and must calibrate the mapping to the V15 `NuisanceEvidence` effects under a prefrozen false-certainty contract.

No threshold is selected here because there is no field calibration evidence yet.

## Readiness-gate consequence

Before this adapter, `nuisance_field_adapter` was `unset` in `benchmarks/v15_prefreeze_readiness_registry.json`.

With this baseline implemented it becomes `development_defined`. It remains a held-out blocker because it has not been calibrated and scientifically frozen with evidence SHA-256.

The overall V15-v2 state therefore remains `BLOCKED_SAFE`.

## Claim boundary

This is software/measurement development only. It supports the statement that V15 can extract nuisance-oriented primary-stream process measurements without target evidence. It does not support field nuisance accuracy or any performance claim.
