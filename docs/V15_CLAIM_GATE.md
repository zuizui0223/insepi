# V15-v2 claim authorization gate

## Why this exists

V15-v2 must not decide what counts as “good enough” after held-out results are visible. The held-out claim layer therefore has a separate pre-data contract from the observers themselves.

The rule is intentionally stricter than checking a point estimate against a target:

```text
prefreeze READY
+ numerical claim threshold frozen before held-out scoring
+ predeclared confidence interval / cluster uncertainty procedure
+ relevant held-out confidence bound crosses threshold
= claim supported
```

If the interval overlaps the threshold, the claim is **inconclusive**. The threshold is not moved. If the whole interval is unfavorable, the claim is **not supported**.

## No numerical defaults

`benchmarks/v15_claim_thresholds_v1_template.json` contains the planned claim slots but leaves the numerical thresholds as `null`.

That is deliberate. Numerical thresholds must be justified together with:

- a minimum effect of scientific interest (MESI) where the claim is comparative;
- the V15 cluster/power plan;
- the final uncertainty model;
- the actual estimand and denominator;
- the scientific consequence of false positive versus false negative conclusions.

A null threshold authorizes no claim and cannot satisfy the held-out readiness gate.

## Confidence-bound semantics

For `at_least` claims:

```text
lower confidence bound >= frozen threshold -> SUPPORTED
upper confidence bound <  frozen threshold -> NOT_SUPPORTED
otherwise                            -> INCONCLUSIVE
```

For `at_most` claims:

```text
upper confidence bound <= frozen threshold -> SUPPORTED
lower confidence bound >  frozen threshold -> NOT_SUPPORTED
otherwise                            -> INCONCLUSIVE
```

The point estimate alone never changes those decisions.

## Absence claim boundary

A target-absence claim has an additional prerequisite:

```text
independently validated A-
```

Without `A-`, even a favorable false-absence-looking metric cannot authorize a biological absence claim. Good `O` plus low positive-target evidence remains unresolved.

`ClaimThreshold` enforces this structurally: every `TARGET_ABSENCE` claim must set `requires_a_minus=True`, and `evaluate_claim()` returns `NOT_EVALUABLE` unless the independent absence channel was validated under the frozen protocol.

For the first V15-v2 held-out generation, the absence strategy is now predeclared as:

```text
retain_upper_bound_1_without_A_minus
```

with provenance in `benchmarks/v15_absence_strategy_v1.json`.

Consequences:

- V15-v2 does not make a calibrated biological target-absence claim;
- `O=observable` plus low/zero target evidence remains unresolved;
- target-presence upper bounds remain 1 unless a separately identified sampling/missingness model provides another bound;
- a future independently validated `A-` requires a new pre-data generation/protocol and cannot retroactively change V15-v2 held-out claims.

## Endpoint-specific claims only

V15-v2 does not permit a single “full system is universally superior” declaration.

Possible held-out conclusions are endpoint-specific, for example:

- observable visit recall meets a predeclared minimum;
- candidate false-positive rate stays below a predeclared maximum;
- `O` catches unobservable windows while controlling false censoring;
- coupled response provides useful rescue while its spurious-rescue guardrail remains controlled;
- forced binary absence incurs a predeclared minimum excess cost relative to the safe system.

A target-absence claim is **not part of the V15-v2 held-out claim set** under the fixed no-`A-` strategy.

Failure or inconclusive evidence lowers only the affected claim.

## Current status

The V15-v2 design surface is now **design-complete but not scientifically frozen**:

- all twelve core prefreeze items have a development-defined contract or implementation;
- no core item remains `unset`;
- the no-`A-` absence strategy is predeclared and hashed;
- numerical claim thresholds, calibrations, final cluster/sample assumptions and other freeze values are still unfrozen.

The readiness registry therefore remains `BLOCKED_SAFE`. Completing and hashing the development-defined items is a future pre-held-out action, not something to infer from held-out output.
