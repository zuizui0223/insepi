# V15-v2 coupled/decision calibration gate

## Why the readiness core changed

A pre-heldout audit found two quantities that were required by the runtime architecture but were not independently represented in the readiness registry:

1. the field measurement that creates the target-coupled `C` route;
2. the operational calibration that turns target/coupled/nuisance field measurements into the thresholds and effect-specific nuisance evidence used by the V15 decision layer.

Leaving these outside the gate would allow a nominally `READY` registry while `VisitSystemThresholds` development defaults or an uncalibrated nuisance index could still be changed after held-out outcomes were visible.

This is therefore a **definition defect in the prefreeze registry**, not a field result and not a reason to change V14b/V14c.

## New core item: `coupled_field_adapter`

V15 declares `C` as a quantity separate from direct target evidence and nuisance. The field bridge must therefore independently provide:

- `coupled_response_score`: positive evidence that the focal target/flower exhibits the predeclared local response;
- `target_link_confidence`: evidence that the response is attributable to the focal actor/interaction.

The usable coupled target route remains:

```text
coupled_response_score * target_link_confidence
```

Neither quantity may be copied from PolliPi direct target evidence or defined as a complement of nuisance.

No field implementation or calibration is frozen yet, so this item remains `development_defined` and blocks held-out use of the coupled route.

## New core item: `target_nuisance_decision_calibration`

The existing numbers:

```text
target_high   = 0.65
target_low    = 0.25
nuisance_high = 0.60
```

are historical development defaults. They are **not field-frozen thresholds**.

The final V15-v2 held-out generation must predeclare and hash:

- final target high/low boundaries;
- final nuisance high boundary;
- the development-only mapping from field nuisance measurements to the three positive nuisance-effect quantities:
  - false-event risk;
  - missed-event risk;
  - attribution risk;
- calibration dataset/split provenance;
- calibration method and diagnostics.

The field nuisance `nuisance_process_index` is not allowed to become all three risks merely because it lies in `[0,1]`.

## Separation from claim thresholds

Operational decision thresholds answer:

> How does the system turn field measurements into T/C/N/O inference states?

Claim thresholds answer:

> Given held-out estimates and uncertainty, what empirical conclusion is strong enough to report?

They are different freeze objects. A favorable claim threshold cannot repair an unfrozen observer threshold, and an operational target/nuisance threshold does not authorize a scientific superiority claim.

## Readiness impact

After adding the missing items, the core registry contains 14 items rather than 12. On the stacked target-adapter branch the expected state is:

```text
7 frozen
7 development_defined
0 unset
BLOCKED_SAFE
```

The held-out gate remains closed. This correction is made before any V15 field held-out result is scored.
