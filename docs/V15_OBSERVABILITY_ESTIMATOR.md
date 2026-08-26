# V15 — Estimating observation support without target or nuisance truth

## Why `unobservable` is not a noise class

The visit-observation system now separates four quantities:

- `T`: the focal insect / visit process;
- `N`: exogenous nuisance capable of mimicking, hiding or corrupting target inference;
- `C`: a target-coupled local response caused by the focal interaction;
- `O`: observation support — whether the primary stream contained enough information to interpret a visit opportunity.

A physical disturbance may cause both nuisance risk and support loss, but those are different statements. Wind can produce large nuisance while the insect remains clearly observable. A quiet frame can be unobservable because the focal flower is outside the usable field of view, hidden behind an occluder, too poorly resolved, saturated or missing in time.

Therefore:

```text
high N  does not imply low O
low N   does not imply high O
O       is not 1 - N
```

## The O estimator is deliberately independent

`PrimaryStreamSupportEstimator` accepts only `PrimaryStreamSupportMeasurements`:

1. target-zone coverage;
2. target-zone visibility;
3. spatial resolution;
4. photometric sufficiency;
5. temporal continuity.

Its API cannot receive target evidence, nuisance risk, biological truth or nuisance labels. This is intentional: otherwise the third axis would merely rename information already contained in PolliPi or InsePi.

The current reference synthesiser uses the minimum component as a support ceiling. This implements a necessary-component interpretation: one hard measurement-channel failure can make a biological non-detection uninterpretable. The default thresholds (`<=0.30` unobservable, `>=0.70` observable) are development placeholders, not field-calibrated probabilities.

## What must be measured from the primary stream

### Coverage

Did the required focal interaction zone remain inside the usable frame throughout the relevant opportunity? Camera geometry, crop metadata and target-zone location can provide this measurement without knowing whether an insect visited.

### Visibility

Was the relevant interaction zone physically visible rather than hidden? This should be estimated by an independent visibility/occlusion audit or target-zone visibility measurement. It must not be defined from low insect evidence.

### Spatial resolution

Did the stream retain the actor/contact-scale detail required by the operational visit definition? A flower may remain visible while the insect/contact scale is too poorly resolved for inference.

### Photometric sufficiency

Were exposure and contrast usable, rather than information-destroying darkness, clipping or saturation? This is a property of the recorded channel, not of whether an insect was present.

### Temporal continuity

Was enough of the event interval recorded to observe the defined visit? Missing frames, dropouts or a truncated interval can make a visit opportunity unobservable despite otherwise good pixels.

## Validation truth is independent of the estimator

V15 uses `PrimaryStreamSupportTruth`, which stores component-level primary-stream truth or unresolved status. Support truth is annotated or physically measured without algorithm outputs. It is not inferred from PolliPi, InsePi or the reference-camera biological label.

This creates two independent observation channels for validation:

```text
primary stream
  -> T/C/N/O algorithms under test

independent reference channel
  -> biological-event and coupling truth only

blinded primary-stream support annotation/measurement
  -> O truth only
```

The same primary stream can therefore be `unobservable` while the reference channel still proves that a visit occurred. That is exactly the configuration needed to measure false biological absence.

## Development sequence

### V15-O1 — measurement development

On development days/scenes only:

- define each component's physical or image-derived measurement;
- define normalisation references;
- quantify disagreement between automated support measurement and blinded support truth;
- inspect failure modes separately by support component;
- change only the O measurement layer while target/nuisance observers remain frozen for that diagnostic round.

### V15-O2 — support-estimator freeze

Before held-out use, freeze:

- five measurement procedures;
- normalisation constants/references;
- missing-data policy;
- observable/unobservable thresholds;
- support metrics and cluster unit.

### V15-O3 — held-out support validation

Use new recording days and focal scenes/flowers. Primary metrics are:

- exact availability accuracy on resolved support truth;
- unobservable recall;
- observable false-censor rate;
- compromised-state recall;
- unresolved support-truth fraction.

No biological-event or nuisance label is required for these metrics.

### V15-O4 — full visit-observation validation

Only after O is frozen do we evaluate the complete visit system:

```text
direct insect evidence
+ target-coupled response evidence
+ exogenous nuisance diagnosis
+ independent observation support
+ protected random audit
```

The main ecological comparison then asks whether explicit support censoring reduces false absence without discarding too much genuinely observable effort, while the target-coupled route improves recall where direct insect evidence is weak.

## Claim boundary

The current implementation establishes semantic and software separation, not field calibration. The next scientific result must come from independently labelled real primary-stream support. Until that exists, do not claim calibrated observability, detection probability or field visit accuracy.
