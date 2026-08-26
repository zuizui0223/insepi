# V15-v2 pre-data invariant freeze

Two V15-v2 components are now complete enough to freeze **without** seeing development or held-out field outcomes. They are definition/estimand invariants rather than fitted quantities.

## 1. Forced versus certified absence metrics

Frozen artifact:

`benchmarks/v15_absence_metric_freeze_v1.json`

The distinction is permanent for V15-v2:

- `negative_evidence` = certified absence only;
- `forced_absence_call` = deliberately unsafe binary comparator;
- the two cannot coexist on one prediction;
- censored windows cannot carry either call;
- unresolved biological truth is outside biological accuracy denominators.

Frozen rates use resolved biological truth only:

```text
false_certified_absence_rate
= false certified absence calls / all certified absence calls

missed_visit_as_certified_absence_rate
= resolved true visits certified absent / all resolved true visits

forced_false_absence_rate
= false forced absence calls / all forced absence calls

forced_missed_visit_as_absence_rate
= resolved true visits forced absent / all resolved true visits
```

A zero denominator returns zero in the frozen evaluator contract. That convention may be accompanied by the corresponding call count in reporting, but is not changed after held-out scoring.

Under the fixed V15-v2 no-`A-` strategy, the default safe system is not expected to emit certified absence. A certified negative appearing through another path requires explicit independent certification provenance and is not inferred from low positive-target evidence.

## 2. Cluster/exposure estimand

Frozen artifact:

`benchmarks/v15_cluster_exposure_estimand_freeze_v1.json`

Primary estimand:

> detected visit-event rate conditional on interpretable primary-stream exposure

Numerator:

- unique stable `event_id` values;
- one event is counted once within its block;
- the same `event_id` cannot belong to multiple blocks.

Denominator:

- interpretable primary-stream seconds / 3600;
- censored seconds are retained separately and **not** counted as no-visit exposure;
- zero interpretable exposure produces a null rate, not zero.

This is deliberately narrower than ecological visit rate over total deployment time. Total-time extrapolation requires a separately frozen sampling/missingness or probability-sample model.

## What is not frozen by this step

The following remain development-defined and continue to block held-out scoring:

- biological/coupling/nuisance/support truth annotation details;
- final split/blinding allocation;
- `O` calibration;
- final target and nuisance field calibration/adapters;
- cluster/sample assumptions and final N;
- numerical claim thresholds and confidence-interval procedure.

The absence strategy is already fixed separately to retain the target-presence upper bound at 1 without a validated `A-`.

## State after this freeze

The readiness registry is expected to report:

```text
design_complete = true
frozen core items = 2
development_defined core items = 10
unset core items = 0
held-out state = BLOCKED_SAFE
```

This is progress toward pre-data freeze, not a field result and not permission to score held-out V15 data.
