# V9 pre-result freeze — design-based ecological inference

V9 is a new inference-validation generation. It does **not** change the frozen V6 allocator, does not use V7 evidence, and does not retune V8 after seeing its generality map.

## Question

The guarded portfolio deliberately mixes probability sampling and preferential targeting. The inference question is therefore not whether the complete selected set can be treated as representative. It is:

> Can the initial protected uniform-exploration draw be retained as an explicit probability sample for ecological prevalence inference while the remaining budget is used adaptively for event/error recovery?

## Frozen design before first V9 result

Machine-readable protocol: `benchmarks/v9_design_inference_protocol.json`.

- finite population: `N = 800` windows per world;
- nominal event prevalence: `.01, .02, .05, .10, .50, .90`;
- total budget: `.05, .10, .25, .50`;
- evidence quality: `.55, .90`;
- observability quality: `.55, .90`;
- residual observer correlation: `0, .5, .9`;
- disturbance prevalence: `.10, .50`;
- 100 paired replicates per regime;
- total regimes: `6 × 4 × 2 × 2 × 3 × 2 = 576`;
- total generated worlds: `57,600`.

The frozen allocator remains:

```text
50% protected uniform exploration
10% evidence targeting
40% observability-risk targeting
 0% direct disagreement targeting
```

No prevalence estimate is provided to the selector.

## Primary estimand

For each generated finite world, let `K` be the realised number of event-positive windows. The primary estimand is the **finite-population prevalence**

```text
P = K / N.
```

Nominal generating prevalence is used only to group regimes. Coverage is judged against realised `K/N`, not the generating parameter.

## Two frozen estimators

### 1. Naive full-selected estimator

The event fraction among all guarded-selected windows. This is intentionally a diagnostic misuse: it treats a partly preferential sample as though it were representative.

Its 95% interval is the ordinary Wilson binomial interval, included only to quantify what goes wrong when sampling design is ignored.

### 2. Protected-exploration estimator

The event fraction among the **initial uniform exploration draw only**. This subset is sampled by simple random sampling without replacement before any targeted arm is processed.

Targeted spillover, if it occurs, is **not** added to the probability-sample inference subset. Keeping this boundary explicit is essential: "uniform-looking spillover" after targeted selections need not have the same simple-random design.

The 95% interval is an exact finite-population hypergeometric confidence set obtained by inverting equal-tailed tests for the unknown finite-population success count `K`.

## Analytical result to accompany V9

Let the protected exploration sample size be `q` from a finite population of size `N`, with finite-population prevalence `P = K/N`. Under simple random sampling without replacement,

```text
E[p_hat_explore | world] = P.
```

For binary events,

```text
Var(p_hat_explore | world)
  = (N-q) / (q (N-1)) * P(1-P).
```

Thus the protected subset is design-unbiased conditional on the realised world. This statement does not depend on the accuracy of Observer-E or Observer-O and does not require targeted selections to be ignorable.

The exact hypergeometric interval is an inversion of the same finite-population sampling law. Its coverage is therefore a property of the protected randomisation design, not a fitted simulation result.

## Metrics frozen before inspection

For both estimators:

- mean signed bias;
- RMSE;
- 95% interval coverage;
- mean 95% interval width.

Results will be summarized overall and by nominal prevalence and total budget. Failure regions will be retained.

## No-tuning rule

After the first V9 output is inspected:

- do not change the 50/10/40 weights;
- do not change the 576-regime grid;
- do not replace the estimators or confidence intervals;
- do not select only favorable prevalence/budget cells;
- do not use V9 to alter or rescue V7.

Any estimator redesign or new interval family receives a new generation label.
