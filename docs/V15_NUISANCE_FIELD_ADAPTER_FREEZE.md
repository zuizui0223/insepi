# V15-v2 nuisance field adapter freeze

## What is frozen

V15-v2 now fixes the **measurement layer** that extracts exogenous nuisance-process structure from primary-stream frames. This does not freeze the later risk calibration or nuisance decision threshold.

The frozen measurement code is:

`src/interaction_sensing/nuisance_field_measurement_v15.py`

Git blob SHA-1 recorded in the freeze artifact:

`1e0498e853d79c1c9b3ee0b100e190e54e65ba7b`

## Measurement semantics

For each predeclared focal/reference geometry:

1. frame-to-frame mean absolute grayscale change is normalized by 255;
2. focal and median-reference RMS motion are retained;
3. spatial process support requires both positive temporal correlation and RMS amplitude agreement;
4. reference temporal support is the maximum of a half-window stationarity score and non-DC spectral concentration;
5. absolute reference-motion magnitude remains in the index;
6. the final process index is the cube root of spatial coherence × temporal support × reference motion fraction.

This preserves the V14a diagnosis that Pearson correlation alone is not sufficient because it ignores amplitude scale.

## Reference-zone selection is part of the freeze

A formula freeze is not enough if reference regions can be moved after seeing results. V15-v2 therefore adds:

`src/interaction_sensing/nuisance_reference_manifest_v15.py`

Every realised window must bind, before model scoring:

- `window_id`;
- primary clip SHA-256;
- focal geometry;
- one or more spatially disjoint reference geometries;
- reference-selection method.

Reference selection cannot consume target output, nuisance output, biological truth, or nuisance truth. The actual per-window coordinates belong to the realised dataset/split manifest, so `split_blinding_protocol` remains a separate blocker until the field manifest exists.

## What remains unfrozen

The process index is still **not**:

- a nuisance probability;
- `false_event_risk`;
- `missed_event_risk`;
- `attribution_risk`;
- a binary nuisance decision.

Those are explicitly assigned to the separate `target_nuisance_decision_calibration` gate. This prevents a convenient `[0,1]` process index from being silently reused as all three biological/measurement effect risks.

## Readiness effect

After this freeze, the 14-item V15-v2 registry is expected to contain:

```text
8 frozen
6 development_defined
0 unset
BLOCKED_SAFE
```

No held-out field result, nuisance threshold, nuisance probability, or performance claim is introduced.
