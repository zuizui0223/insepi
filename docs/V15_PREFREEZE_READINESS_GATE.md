# V15-v2 prefreeze readiness gate

## Purpose

V15-v2 is now the active empirical bridge, but it is still **pre-data**. The next safe step is not to start held-out scoring. It is to make the boundary between development and held-out execution mechanically explicit.

`src/interaction_sensing/v15_prefreeze.py` and `benchmarks/v15_prefreeze_readiness_registry.json` implement a fail-closed gate:

```text
BLOCKED_SAFE -> one or more required items are not scientifically frozen
READY        -> every required item is frozen with evidence path + SHA-256
```

A blocked gate is the expected current state. It is not a failed scientific result.

## Why this gate exists

The V15-v2 semantic correction established that:

- low target evidence is not biological absence evidence;
- observation support `O` is not an absence channel;
- target absence requires either a genuinely independent validated `A-` channel or an explicit decision to retain the target-presence upper bound at 1;
- forced binary negatives must remain distinguishable from certified negative evidence.

Those rules would be easy to violate if held-out work could begin while calibration, sampling, metrics, or the absence strategy were still fluid. The readiness gate therefore blocks held-out execution until the full measurement contract is frozen.

## Core freeze items

The gate requires these items exactly once:

1. biological-truth annotation;
2. target-coupling truth annotation;
3. exogenous nuisance-truth annotation;
4. primary-stream support-truth annotation;
5. split/blinding protocol;
6. `O` measurement and calibration;
7. target field adapter;
8. nuisance field adapter;
9. forced-versus-certified absence metrics;
10. cluster/exposure estimand;
11. MESI-linked sampling/power plan;
12. numerical claim thresholds.

Each item may be:

- `unset`;
- `development_defined`;
- `frozen`.

Only `frozen` satisfies the held-out gate, and a frozen item must carry both an evidence path and a lowercase 64-hex SHA-256. Merely having development code or prose does not count as scientific freeze.

## Two acceptable absence paths

The gate does not assume that an independent field-valid absence channel must exist.

Before held-out work the project must explicitly choose one of two strategies:

### 1. No validated `A-`

```text
absence_strategy = retain_upper_bound_1_without_A_minus
```

This path is allowed only if:

```text
safe_target_presence_upper_bound = 1.0
```

The method may then validate positive target detection, nuisance diagnosis, observation support, censoring, and forced-binary cost, but it may not claim calibrated biological absence from low target evidence.

### 2. Validated independent `A-`

```text
absence_strategy = validated_independent_A_minus
```

This path adds a conditional required item:

```text
a_minus_validation_protocol
```

That item must itself be frozen with independent measurement provenance and SHA-256 before held-out execution is READY.

## Current machine-readable state

The current registry deliberately evaluates to `BLOCKED_SAFE`.

Development-defined pieces already exist for layered truth, blinding, the five-component `O` estimator, positive target semantics, forced/certified absence metrics, and conditional interpretable-exposure rate estimation.

The clearest currently unset pieces are:

- a V15-v2 field-facing nuisance adapter with frozen provenance;
- the final MESI-linked sampling/power plan;
- numerical held-out claim thresholds.

The absence strategy is also still explicitly `undecided`.

No numbers are invented by this gate to remove those blockers.

## Usage

Status report:

```bash
python scripts/check_v15_prefreeze_readiness.py
```

A future held-out runner must enforce:

```bash
python scripts/check_v15_prefreeze_readiness.py --require-ready
```

while the current registry is blocked, that command must fail closed.

## Scientific boundary

This gate creates no field result, no calibration, no sample-size result, and no performance claim. It only makes the existing V15-v2 pre-data boundary executable and auditable.
