# V6 method freeze — exploration-guarded dual-observer portfolio

## Frozen allocator

V6 allocation is frozen at implementation commit:

`a8ac75991ab28fd74a3f3a5482304a2b127a97bc`

Method name:

`exploration_guarded_dual_observer_portfolio_v6`

Frozen quota vector:

```text
uniform exploration   0.50
PolliPi evidence      0.10
InsePi observability  0.40
disagreement          0.00
```

No prevalence estimate is supplied at runtime. The only deployment control used
by the selector is the externally given total sensing/audit budget.

The frozen runtime method must not be edited before a future V7 execution. Tests,
documentation, validation infrastructure, and manifests may be added without
changing the method implementation.

## Why disagreement has zero allocation weight

This is an empirical and conceptual outcome of the simulation-first contradictory
development programme, not a deletion of the disagreement concept.

V5 falsified fixed scalar disagreement ranking under prevalence shift. V6 first
replaced that scalar with independent budget quotas. Development ablations then
showed that forcing a positive disagreement quota was unnecessary. Calibration
sparse fitting repeatedly drove the disagreement allocation weight to zero, and
the forced four-arm candidate lost hidden-error recall relative to uniform in
balanced/common regimes.

Disagreement remains valuable for:

- revealing incompatible observer assumptions;
- localising failure seams;
- deciding which observer requires development;
- defining falsification tests and ablations;
- interpreting why allocation policies fail.

It is therefore a **diagnostic/development variable**, not a direct V6 allocation
priority.

## Why uniform exploration is structural

The 50% exploration quota is not merely a fitted heuristic. If `alpha` of the
selected sample is uniform exploration, the expected selected distribution can be
written as

```text
Q = alpha U + (1 - alpha) R
```

for arbitrary targeted distribution `R`. Therefore

```text
TV(Q, U) <= 1 - alpha.
```

With the frozen `alpha = 0.50`, the theoretical worst-case expected total-
variation distortion is bounded by 0.50, while targeted-arm quota spillover can
only increase the realised uniform share. The observed high-resolution V4
maximum family-level TV was much lower: 0.21919.

This explicitly addresses the V5 failure where fixed scalar ranking could produce
TV distortion around 0.833 at low sensing budget.

## High-resolution development evidence

V4 is **development evidence**, not untouched validation. The final focused
comparison used:

- 4,800 sampled windows per regime;
- 200 paired Monte Carlo replicates;
- prevalence = 0.10, 0.50, 0.90;
- sensing budget = 0.10, 0.25, 0.50;
- the same sampled worlds for candidate and uniform baseline;
- V4 world fingerprint
  `10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`;
- PolliPi emitted-trace source commit
  `5541201b376689c32aaabeafbc8e7e9592150d23`.

The development hard gate required:

```text
worst regime min(event_recall_ratio_to_uniform,
                 hidden_error_recall_ratio_to_uniform) >= 1.00
max disturbance-family TV <= 0.25
```

Frozen V6 result:

- worst joint ratio: **1.00846**;
- mean joint ratio: **1.11642**;
- maximum TV: **0.21919**;
- regimes with joint ratio >= 1: **9 / 9**.

### Per-regime paired ratios

| prevalence | budget | event ratio | hidden-error ratio | joint ratio | TV |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.10 | 0.10 | 1.25691 | 1.34958 | 1.25691 | 0.21919 |
| 0.10 | 0.25 | 1.26794 | 1.34923 | 1.26794 | 0.21571 |
| 0.10 | 0.50 | 1.29637 | 1.37983 | 1.29637 | 0.20378 |
| 0.50 | 0.10 | 1.06397 | 1.07263 | 1.06397 | 0.18349 |
| 0.50 | 0.25 | 1.06406 | 1.06696 | 1.06406 | 0.17826 |
| 0.50 | 0.50 | 1.07249 | 1.07446 | 1.07249 | 0.16788 |
| 0.90 | 0.10 | 1.00864 | 1.06937 | 1.00864 | 0.17921 |
| 0.90 | 0.25 | 1.00846 | 1.06473 | 1.00846 | 0.17386 |
| 0.90 | 0.50 | 1.00896 | 1.06417 | 1.00896 | 0.16375 |

The weakest margin is intentionally visible: under common prevalence the event-
recall advantage over uniform is only about 0.8%. This is exactly the sort of
small-margin result that V7 must independently challenge.

## Focused alternatives

The last development sweep tested only the neighbourhood already exposed by V6
screening, keeping PolliPi at 0.10 and disagreement at zero.

- `E=.40, P=.10, I=.50`: all nine joint ratios above one but **failed TV**
  (`max TV = 0.26567`).
- `E=.50, P=.10, I=.40`: **passed**, highest selected worst/mean joint result.
- `E=.60, P=.10, I=.30`: **passed**, lower TV (`0.17222`) but slightly lower
  worst joint (`1.00832`) and lower mean joint (`1.10303`).
- `E=.70, P=.10, I=.20`: **failed**, common-prevalence hidden-error recall fell
  below uniform (`worst joint = 0.98329`).

Selection followed the already coded lexicographic development rule: satisfy the
hard gate, maximise worst joint ratio, then mean joint ratio, then minimise TV.

## Claim ceiling after V6 development

The V6 candidate supports **no field-accuracy claim** yet. The current candidate
claim to be challenged in V7 is:

> Under finite sensing budgets and unknown event prevalence, an
> exploration-guarded portfolio that preserves independent biological-evidence
> and observability-risk quotas can avoid the prevalence-shift collapse of fixed
> scalar prioritisation while improving recovery of both true events and hidden
> observation errors relative to uniform sampling.

This is deliberately different from the original disagreement-allocation claim.
The development path has narrowed the hypothesis rather than forcing the initial
idea to survive.

## V7 status

**BLOCKED. No V7 seed or world has been generated.**

`docs/V7_LOCKED_VALIDATION_PROTOCOL.md` defines the one-shot rules. Before V7 may
be materialised, all observer commits, allocator commit, baselines, generator,
manifest and pass/fail rules must be reachable and frozen. In particular, the
user-reported V5 frozen observer commits remain local/unpushed and were not
resolvable from GitHub when V6 was developed; that reproducibility gap must be
closed before the final locked run.
