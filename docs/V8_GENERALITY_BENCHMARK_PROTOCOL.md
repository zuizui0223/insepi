# V8 generality benchmark — pre-registered applicability map

## Why V8 exists

V7 asks a narrow validation question: does the frozen V6 allocator survive one new locked visual world? V8 asks a different question needed for broad methodological uptake:

> **Under what combinations of event prevalence, sensing budget, observer quality, observer residual correlation and disturbance prevalence is exploration-guarded dual-observer allocation useful, unnecessary, or inferior to a simpler design?**

V8 is **not** another opportunity to tune V6. The frozen allocation vector remains:

```text
uniform exploration   0.50
biological evidence   0.10
observability risk    0.40
direct disagreement   0.00
```

No V8 result may change those weights under the V6/V7 generation.

## Separation from V7

V8:

- does not import the V7 generator;
- does not derive or inspect the V7 seed;
- does not render V7 pixels;
- does not use frozen V7 traces;
- does not alter V7 hard gates or claim levels;
- is based on an abstract observer-quality world rather than PolliPi/InsePi-specific image features.

A V8 result therefore cannot rescue a failing V7 result. Conversely, V7 cannot be used to tune V8 after this protocol is committed.

## Factorial parameter space

The machine-readable registry is `benchmarks/v8_generality_protocol.json`.

The fixed grid is:

- event prevalence: 0.02, 0.10, 0.50, 0.90;
- budget: 0.05, 0.10, 0.25, 0.50;
- evidence-observer quality: 0.60, 0.75, 0.90;
- observability-observer quality: 0.60, 0.75, 0.90;
- shared residual correlation: 0.00, 0.50, 0.90;
- disturbance prevalence: 0.10, 0.40.

This gives **864 regimes**, each evaluated on 800 windows × 10 paired replicates.

`evidence_quality` and `observability_quality` are monotone simulation controls, not claimed AUC values. `residual_correlation` controls shared stochastic residual structure; it is not asserted to equal the empirical correlation of binary observer errors.

## Abstract world

Each window has:

1. latent true event presence/absence;
2. disturbance state;
3. independent scene-difficulty state;
4. an evidence score whose discrimination is degraded by scene risk;
5. an observability-risk score that attempts to identify scene risk.

The evidence observer's binary decision error against latent event truth defines `evidence_hidden_error` for audit-recovery comparison. Observer-O never receives that error label as input; it sees a simulated risk signal generated from disturbance and scene difficulty.

## Frozen policy registry

All policies see the same paired worlds.

### Uniform

100% non-preferential selection.

### Guarded V6

50% exploration + 10% evidence + 40% observability, with separate quotas.

### Same-exploration comparators

- 50% exploration + 50% evidence only;
- 50% exploration + 50% observability only;
- 50% exploration + 50% fused scalar `0.20*evidence + 0.80*observability`;
- 50% exploration + 50% `max(evidence, observability)`.

These comparisons are critical. They distinguish:

- benefit attributable merely to retaining 50% exploration;
- benefit attributable to one observer alone;
- benefit attainable by collapsing observers back into one scalar;
- benefit specifically associated with separate observer quotas.

No comparator weights may be changed after inspecting V8 output.

## Primary recovery metrics

For every regime/policy:

- true-event recall under the finite selection budget;
- evidence-observer hidden-error recall;
- disturbance/scene-family total variation from the full world;
- event-recall ratio to uniform;
- hidden-error-recall ratio to uniform;
- joint recovery ratio = minimum of those two ratios.

The principal applicability question is whether frozen V6 has joint ratio >= 1, and whether it matches or exceeds the best same-exploration comparator.

## Ecological-inference check

Each guarded policy retains the exact identities of its uniform exploration subset.

For every paired replicate V8 therefore computes two prevalence estimators relative to the realised full-world event prevalence:

1. **naive selected-sample prevalence** using all selected windows as though they were representative;
2. **exploration-only prevalence** using only the explicitly retained simple-random exploration subset.

V8 reports signed bias and RMSE for both. This does not prove a universal ecological estimator, but directly tests the methodological idea that targeted event/error recovery can coexist with a design-valid reference subset.

No estimator is changed after result inspection.

## Finite-budget analytical guarantees

The ideal mixture theorem is complemented by finite-population results in `interaction_sensing.finite_budget_guarantees`.

For a population of `N` windows and a reserved simple-random exploration quota `q_U`:

### Inclusion floor

Every window has overall inclusion probability at least

```text
q_U / N,
```

because targeted selection can add inclusion probability but cannot remove a uniform selection.

### Exact family-miss probability

For any family containing `m` of `N` windows, the probability that uniform exploration misses the family completely is

```text
C(N-m, q_U) / C(N, q_U).
```

### Finite-budget weight bound

If the target design is a simple-random total budget `B`, then target inclusion is `B/N`, whereas guarded inclusion is at least `q_U/N`. Therefore

```text
(B/N) / pi_i <= B / q_U.
```

At exactly half exploration and even integer quotas this is at most 2, matching the ideal-mixture importance-ratio bound up to integer quota effects.

## Pre-registered interpretation

V8 is an **applicability map**, not a winner-selection benchmark.

- If V6 dominates broadly, report the region and its boundaries.
- If V6 helps only when both observers are informative and not strongly redundant, report that conditional result.
- If a same-alpha single-observer policy matches V6 in a region, do not attribute that region's gain to dual-observer separation.
- If fused scalar targeting matches or beats separate quotas, narrow the architectural claim accordingly.
- If exploration-only prevalence estimation has lower bias/RMSE than naive selected-sample estimation, interpret that as evidence for preserving a reference-design component, not as proof that every downstream estimator is unbiased.
- Do not alter V6 weights, V7 rules or this parameter grid after inspecting V8.
