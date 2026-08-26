# Exploration-guard theory for finite-budget sensing

This note states the analytical part of the frozen V6 method independently of any
particular simulation result.

## Setup

Let `U` denote the target non-preferential sampling distribution over observation
windows or observation conditions. Let `R` be an arbitrary targeted allocation
distribution produced by biological-evidence, observability-risk, disagreement, or
any future acquisition rule.

An exploration-guarded sampling distribution is

```text
Q = alpha U + (1-alpha) R,
```

with `0 < alpha <= 1`.

The frozen V6 allocation has `alpha = 0.50`. Its concrete implementation uses
fixed quotas without replacement, but targeted-arm exhaustion/spillover returns to
uniform exploration, so the realised exploration fraction can only be larger than
the nominal floor. The distributional statements below therefore describe the
ideal mixture exactly and act as conservative guarantees for the quota allocator
in expectation.

## Proposition 1 — exact total-variation contraction

For any two probability distributions `U` and `R` on the same measurable space,

```text
TV(Q, U) = (1-alpha) TV(R, U) <= 1-alpha.
```

### Proof

By definition,

```text
Q - U
= alpha U + (1-alpha)R - U
= (1-alpha)(R-U).
```

Total variation is homogeneous for signed measures, therefore

```text
TV(Q,U)
= (1-alpha) TV(R,U).
```

Because total variation between probability distributions is at most one,

```text
TV(Q,U) <= 1-alpha.
```

For the frozen V6 `alpha=0.50`, no targeted allocation distribution can create an
expected TV distortion greater than `0.50`; the empirical V4 development maximum
was much smaller (`0.21919`).

## Proposition 2 — no condition can be completely starved

For every measurable set of observation conditions `A`,

```text
Q(A) >= alpha U(A).
```

### Proof

Since `R(A) >= 0`,

```text
Q(A)
= alpha U(A) + (1-alpha)R(A)
>= alpha U(A).
```

Thus any condition family that has non-zero mass under the target sampling process
retains non-zero sampling mass under the exploration-guarded process.

For a rare disturbance family occupying target fraction `p`, `n` independent
selections from `Q` have expected count at least

```text
n alpha p.
```

This is the formal sense in which the exploration quota prevents a targeted
observer from completely deleting an unanticipated condition from the audit
sample.

## Proposition 3 — bounded target-to-sample importance weights

Where `U(x) > 0`, define the target-to-sample density ratio

```text
w(x) = U(x) / Q(x).
```

Because

```text
Q(x) >= alpha U(x),
```

we have

```text
0 <= w(x) <= 1/alpha.
```

For the frozen V6 `alpha=0.50`,

```text
w(x) <= 2.
```

Therefore any future inverse-propensity or importance-weighted correction from the
adaptive sample back toward `U` has a finite worst-case likelihood-ratio bound
under the ideal mixture. A purely targeted policy (`alpha=0`) has no corresponding
general bound and may assign zero probability to parts of the target support.

This proposition does not by itself prove low finite-sample variance, but it rules
out arbitrarily large weights caused solely by complete targeted exclusion.

## Corollary — bounded max-divergence from target to sample

The same density-ratio bound yields

```text
D_infinity(U || Q) <= log(1/alpha).
```

For `alpha=0.50`,

```text
D_infinity(U || Q) <= log 2.
```

This is another way to state that the adaptive sample cannot become arbitrarily
unlikely under the target distribution when the exploration floor is positive.

## Proposition 4 — targeted allocation cannot reduce the uniform component

Suppose the total audit budget is `B` selections and the allocator reserves
`alpha B` selections for uniform exploration before targeted arms are processed.
If a targeted arm has fewer unique positive-priority windows than its quota and
its unused quota spills back to uniform exploration, then the realised uniform
share `alpha_realised` satisfies

```text
alpha_realised >= alpha.
```

Consequently Propositions 1–3 remain conservative if `alpha` is replaced by the
nominal floor.

The PolliPi/InsePi V6 allocator implements exactly this spillover rule: unused
PolliPi, InsePi, or disagreement quota is never reassigned to another targeted
observer; it returns to uniform exploration.

## What the theory does and does not establish

The propositions establish **sampling safety properties**, not biological
superiority.

They establish:

- an upper bound on sampling-distribution distortion;
- a lower bound on coverage of every target-supported condition family;
- a finite upper bound on target-to-adaptive importance weights;
- persistence of these bounds under targeted-quota spillover.

They do not establish:

- that PolliPi or InsePi scores are accurate in the field;
- that `alpha=0.50` is universally optimal;
- that the V6 portfolio improves event or error recovery in unseen worlds;
- that empirical ecological estimates are unbiased without an explicit estimator.

The last two performance claims are exactly what locked V7 is designed to test.

## Why this matters for the V5 -> V6 transition

V5 showed that a fixed targeted ranking could strongly over-concentrate sampling
on selected disturbance states as prevalence changed. The V6 response is therefore
not merely a different ranking score. It changes the admissible policy family from

```text
all budget -> one targeted ranking
```

to

```text
guaranteed exploration + bounded targeted exploitation.
```

The theory explains why that architectural change directly addresses the failure
mode exposed by V5 even before any new validation result is inspected.

## Manuscript-ready theorem statement

A compact statement suitable for the methods paper is:

> **Exploration-guard theorem.** Let `U` be the target observation distribution and
> `R` any adaptive acquisition distribution. For `Q = alpha U + (1-alpha)R` with
> `alpha > 0`, (i) `TV(Q,U) = (1-alpha)TV(R,U) <= 1-alpha`; (ii) every measurable
> set `A` satisfies `Q(A) >= alpha U(A)`; and (iii) the density ratio
> `U(x)/Q(x) <= 1/alpha` wherever `U(x)>0`. Thus a positive exploration floor
> simultaneously bounds selection distortion, prevents support deletion, and
> bounds inverse-propensity weights independently of the targeted acquisition
> rule.

The proof requires no assumptions about observer accuracy or independence.
