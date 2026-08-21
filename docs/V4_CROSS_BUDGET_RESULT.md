# V4 cross-budget development result

## Decision

V4 supports a **budget-regime claim**, not a universal-disagreement claim.
Structured disagreement is useful when audit capacity is scarce (10% and 25%),
but simple candidate/risk union is the only core Pareto policy at a 50% budget.
This development result narrows the claim before the one-shot V5 validation; it
is not final paper evidence.

## Fail-closed evaluation contract

The first cross-runner version sampled all 120 V4 conditions, including the 52
calibration conditions used to set the InsePi occlusion threshold. That mixed
result is invalid for held-out evaluation and is retained only as development
history.

The corrected runner:

- calibrates InsePi from the calibration split but evaluates policies on the 68
  test conditions only;
- rejects duplicate or divergent condition IDs;
- rejects PolliPi/InsePi mismatches in split, truth, or disturbance family;
- compares the six preregistered policies plus PolliPi-only and InsePi-only
  removals of the structured disagreement rule;
- reports the Pareto frontier on true-event recall, hidden-error recall, and
  captures per recovered hidden error; error-type yields and disturbance
  total-variation distance remain explicit guardrails.

## Provenance

- PolliPi source: `5541201b376689c32aaabeafbc8e7e9592150d23`
- InsePi evaluation source: `19db110e8610151711adf87accafa05b5f2969d2`
- V4 world fingerprint:
  `10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`
- evaluation split / conditions: `test` / 68
- synthetic world windows per replicate: 4,800
- replicates: 200
- seed: 20,260,821
- machine-readable ledger: `analysis/v4_cross_budget_report.json`

## Core policy result

| Budget | Core Pareto policies | Policy | Event recall | Hidden-error recall | Missed-event yield | Captures / hidden error | Disturbance TV |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 10% | intersection, disagreement | disagreement | 0.1528 | **0.1733** | **0.7641** | **1.3101** | 0.7054 |
| 10% | intersection, disagreement | intersection | **0.1872** | 0.1444 | 0.6292 | 1.5726 | 0.6666 |
| 25% | union, disagreement | disagreement | 0.2811 | **0.3187** | **0.5622** | **1.7800** | 0.7054 |
| 25% | union, disagreement | union | **0.3970** | 0.3165 | 0.3242 | 1.7921 | 0.3585 |
| 50% | union | disagreement | 0.5296 | 0.6004 | **0.5296** | 1.8889 | 0.3064 |
| 50% | union | union | **0.6714** | **0.6275** | 0.4364 | **1.8074** | 0.1850 |

At 10%, disagreement recovers substantially more hidden errors per capture than
every comparator, at the cost of lower event recall than intersection and strong
disturbance-distribution distortion. At 25%, disagreement and union form the
frontier: their hidden-error recalls are close, but they recover different
objectives. At 50%, union dominates disagreement on the central Pareto axes.

## Single-view removal

| Budget | Full disagreement hidden recall | PolliPi-only removal | InsePi-only removal | Gain over best removal |
| ---: | ---: | ---: | ---: | ---: |
| 10% | **0.1733** | 0.1134 | 0.1259 | +0.0474 |
| 25% | **0.3187** | 0.2715 | 0.3142 | +0.0044 |
| 50% | 0.6004 | 0.5143 | **0.6033** | -0.0029 |

The interaction between observers is material at 10%, small at 25%, and absent
at 50%. This is why V5 must test a preregistered scarce-budget claim rather than
assert that disagreement is always the best policy.

## Claim ceiling after V4

V4 justifies proceeding to locked validation of this narrower claim:

> Under scarce sensing or audit budgets, structured disagreement between an
> independently developed biological-evidence observer and observability
> observer can recover hidden missed-event errors more efficiently than either
> view alone or simple set-combination policies, while exposing an explicit
> event-recovery and sampling-bias trade-off.

V4 does not justify field accuracy, universal superiority, or superiority at
high budgets. Those statements remain outside the paper claim.
