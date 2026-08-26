# V15-v2 coupled field baseline

## Current purpose

The V15-v2 target side has two distinct positive routes:

1. direct actor/insect evidence;
2. target-coupled local response evidence.

The direct route is already bound to the PolliPi ordinal interface. This document defines a development baseline for the second route without pretending that arbitrary flower motion is evidence of a visit.

## Two separate quantities

The field bridge emits:

- `coupled_response_score`: an uncalibrated continuous measurement of local focal-target motion relative to neighbouring reference regions;
- `target_link_confidence`: independent evidence that the response is attributable to the focal actor/interaction.

The usable route remains

```text
coupled_target_score = coupled_response_score * target_link_confidence
```

These quantities are not complements of nuisance and neither is copied from PolliPi.

## Local-response baseline

`measure_field_coupled_response()` measures frame-to-frame grayscale motion in a focal zone and one or more predeclared neighbouring reference zones.

The reference trace is the median reference motion. The local excess is

```text
max(0, focal_rms - reference_rms) / (focal_rms + reference_rms)
```

with zero when both are static.

The development response index is

```text
sqrt(local_response_excess * focal_rms)
```

It is not a probability and currently has no field decision threshold.

Shared scene motion in focal and reference regions therefore does not become a local coupled response merely because both move.

## Attribution is fail-closed

A local response by itself cannot establish the focal biological interaction.

The only allowed non-zero `target_link_confidence` input is an `IndependentAttributionCue` with:

- the same window ID;
- an allowed independent source class;
- retained evidence SHA-256;
- retained calibration SHA-256.

Allowed source classes are deliberately limited to:

- independent contact geometry;
- an independent secondary sensor;
- a prevalidated independent link model.

There is no PolliPi/direct-target or nuisance-derived attribution source in the enum.

Without a valid cue:

```text
target_link_confidence = 0
usable_coupled_target_score = 0
```

This preserves the V14b/V14c boundary: indirect-only local response can remain unattributable rather than being forced into a target-positive decision.

## Why this core item remains development-defined

The local-response measurement implementation now exists, but V15-v2 still lacks a concrete independently validated field attribution source and its calibration. Therefore `coupled_field_adapter` remains a held-out blocker.

It may become FROZEN only after development-only work predeclares and hashes:

1. the concrete attribution sensor/model;
2. its calibration rule;
3. the focal/reference geometry and attribution evidence binding in the realised manifest;
4. leakage checks proving that PolliPi target output, nuisance output and held-out truth are not runtime inputs.

No field indirect-rescue claim is authorized by this baseline alone.
