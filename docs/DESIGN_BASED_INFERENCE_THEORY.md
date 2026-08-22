# Design-based inference from protected exploration

This note extends the exploration-guard result from sampling safety to ecological inference. The result concerns only the **initial protected uniform-exploration draw**. It does not treat the complete adaptive sample as representative.

## Setup

Fix a finite population of `N` observation windows with binary ecological states

```text
y_i in {0,1},  i=1,...,N.
```

Let

```text
K = sum_i y_i
P = K/N
```

be the realised finite-population event prevalence.

The guarded allocator first draws `q` distinct windows uniformly without replacement, before any evidence or observability targeting occurs. Call this set `S_U`. Targeted arms are processed only after `S_U` is fixed and cannot remove its members.

The design-based estimator is

```text
P_hat_U = (1/q) sum_{i in S_U} y_i.
```

## Proposition 1 — exact design unbiasedness

Under simple random sampling without replacement,

```text
E[P_hat_U | y_1,...,y_N] = P.
```

### Proof

Each window has inclusion probability `q/N`. Therefore

```text
E[P_hat_U]
= (1/q) sum_i y_i Pr(i in S_U)
= (1/q) sum_i y_i q/N
= K/N
= P.
```

No assumption is required about Observer-E, Observer-O, event prevalence, targeted-arm accuracy, or dependence among their scores.

## Proposition 2 — exact finite-population variance for binary states

For SRSWOR,

```text
Var(P_hat_U | world)
= (1-q/N) S_y^2 / q,
```

where

```text
S_y^2 = (1/(N-1)) sum_i (y_i-P)^2.
```

For binary states,

```text
sum_i (y_i-P)^2 = N P(1-P),
```

hence

```text
Var(P_hat_U | world)
= (N-q)/(q(N-1)) P(1-P).
```

This makes the cost of protecting a probability-sample subset explicit: smaller `q` preserves design validity but increases estimator variance.

## Proposition 3 — exact finite-population confidence set

Conditional on a world with `K` event-positive windows, the number `X` observed in the protected exploration sample follows

```text
X ~ Hypergeometric(N, K, q).
```

For observed `x`, define the accepted values of `K` as those for which both equal-tailed exact tests are not rejected:

```text
Pr_K(X >= x) > alpha/2
and
Pr_K(X <= x) > alpha/2.
```

The minimum and maximum accepted `K`, divided by `N`, give an exact two-sided confidence interval for finite-population prevalence. By inversion of valid one-sided hypergeometric tests, coverage is at least `1-alpha` (possibly conservative because the distribution is discrete).

V9 fixes `alpha=.05` before result inspection and verifies the inversion implementation by exhaustive enumeration on a small finite population before running the large simulation.

## Why targeted spillover is excluded

If a targeted arm exhausts its positive-priority candidates, the allocator may return unused quota to a uniform-looking spillover stage. Those spillover choices occur **after** targeted selections have removed windows from the candidate pool. They are therefore not automatically the same SRSWOR design as the initial exploration draw.

For inference, V9 uses only the initial protected set `S_U`. This deliberately sacrifices some possible sample size in exchange for a clean probability-sampling interpretation.

## Why the complete adaptive sample is not automatically valid for prevalence inference

Let `S = S_U union S_T`, where `S_T` contains evidence- and observability-targeted selections. Inclusion probabilities in `S_T` depend on acquisition scores that may be associated with `y_i` or with conditions affecting its detectability. Therefore

```text
mean_{i in S} y_i
```

need not be unbiased for `P`.

A correct estimator using all adaptive observations would require the full inclusion probabilities (and generally joint inclusion probabilities for standard design-based variance estimation), or a defensible model for the preferential selection mechanism. V9 does not assume those quantities are known. Instead it preserves `S_U` as an auditable design-based reference sample.

## Study-design interpretation

The guarded portfolio can therefore be separated conceptually into two simultaneous functions:

```text
protected exploration -> probability-sample ecological denominator/reference
observer targeting      -> efficient event/error discovery
```

The theoretical claim is not that targeted data should be discarded. It is that a finite adaptive sensing budget can reserve an explicit component whose inferential meaning remains valid even when the targeted component is highly preferential.

## Scope

These propositions establish finite-population design validity for prevalence-like means of variables measured without error on the protected subset. They do not by themselves solve:

- measurement error in the protected observations;
- occupancy/detection models with repeated visits;
- temporal or spatial dependence when the target design is not SRSWOR;
- inference from the complete targeted sample without known inclusion probabilities;
- field accuracy of either observer.

Those extensions would require new estimators or new sampling designs and are not introduced under V9 after result inspection.
