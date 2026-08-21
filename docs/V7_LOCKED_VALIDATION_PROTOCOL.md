# V7 locked validation protocol — pre-execution boundary

**Do not generate or run V7 from this document.** This file defines the claim
boundary before any V7 world is materialised. Candidate weights are frozen only
after the V6 high-resolution development comparison is complete.

## Why V7 exists

V5 falsified fixed scalar disagreement allocation. V6 is a new allocation family
built from V1–V5/V4 development evidence. Because V4 has been repeatedly
inspected during V6 development, it cannot carry the final generalisation claim.
V7 is a new one-shot validation generation.

## Preconditions before V7 may be materialised

All must be true:

1. PolliPi observer code used by V7 is frozen at an explicit reachable commit.
2. InsePi observer code used by V7 is frozen at an explicit reachable commit.
3. The V6 allocation candidate is frozen at an explicit reachable commit.
4. The exact allocation weights are committed in a method-freeze manifest.
5. Baseline policies and ablations are frozen.
6. V7 generator code, disturbance-family registry, prevalence regimes, budgets,
   metrics, and pass/fail rules are committed.
7. The V7 seed-generation rule is committed, but the resulting worlds have not
   been rendered or inspected.
8. The user-reported local V5 frozen commits/evidence are either published or
   otherwise made reproducibly materialisable. Until then, public GitHub V6 work
   is development evidence and V7 execution is blocked.

## Seed rule

After the method and generator commits are frozen, the V7 master seed must be
derived deterministically from immutable identifiers, for example:

```text
SHA256("V7" || pollipi_method_sha || insepi_method_sha || allocator_sha || generator_sha)
```

The seed may not be hand-picked, rerolled, or replaced after inspection.

## Core regimes

V7 must include the same unknown-prevalence stress dimensions used to falsify V5:

- rare event prevalence;
- balanced event prevalence;
- common event prevalence;
- 10%, 25%, and 50% finite sensing/audit budgets.

Additional unseen disturbance mixtures/OOD families may be included only if the
family registry and generator are frozen before seed derivation.

## Required comparators

At minimum:

- uniform exploration;
- PolliPi-only candidate priority;
- InsePi-only audit priority;
- legacy fixed scalar disagreement;
- candidate OR risky;
- candidate AND risky;
- frozen V6 candidate;
- V6 candidate with PolliPi allocation arm removed and its quota returned to
  exploration;
- V6 candidate with InsePi allocation arm removed and its quota returned to
  exploration.

If the frozen V6 candidate has disagreement weight zero, no artificial positive
disagreement quota is introduced merely for V7.

## Primary paired metrics

All candidate comparisons use the same sampled worlds per replicate.

For each prevalence × budget regime report:

- true-event recall;
- hidden-observation-error recall;
- captures per recovered hidden error;
- disturbance-distribution total-variation distance;
- paired ratios against uniform for event recall and hidden-error recall.

The headline robustness statistic is:

```text
worst_joint_ratio = min_regime(min(event_ratio_to_uniform,
                                   hidden_error_ratio_to_uniform))
```

This directly tests the prevalence-shift failure discovered in V5.

## Locked pass/fail rules

Before V7 execution the final method-freeze manifest must copy these rules and
fill the frozen candidate identifiers.

A strong V6 allocation claim passes only if all are satisfied:

1. **No material prevalence-regime collapse:** every regime has
   `joint_ratio >= 0.98` against uniform.
2. **Overall benefit:** mean joint ratio across the nine core regimes is > 1.00.
3. **Selection-bias control:** maximum disturbance TV distance is <= 0.25.
4. **Robustness relative to legacy allocation:** the frozen V6 candidate's
   worst-joint ratio is at least as high as every legacy targeted allocation
   comparator listed above, within a 0.01 numerical tolerance.
5. **Observer contribution:** neither the PolliPi-arm removal nor the InsePi-arm
   removal may strictly dominate the full frozen V6 candidate on the tuple
   `(worst_joint_ratio, mean_joint_ratio, -max_tv)`.
6. **No hidden-truth leakage:** flipping latent truth while holding emitted
   observer traces fixed leaves V6 selections unchanged; this invariant remains
   enforced by unit tests.
7. **Reproducibility:** V7 world fingerprint, emitted traces, report hashes,
   source commits, and all test counts are recorded before interpretation.

Failure of any hard rule lowers the claim ceiling. V7 is not rerun with modified
weights or thresholds under the same generation label.

## One-shot rule

V7 is executed once after all preconditions are frozen. After first inspection:

- do not modify V6 method code and claim the same V7 as validation;
- do not choose a new seed;
- do not delete failing baselines or regimes;
- preserve full result and claim ceiling;
- any subsequent method change becomes a new method generation and requires a
  new validation generation.

## Current status

V7 execution is **BLOCKED**. V6 high-resolution development selection is still in
progress, and the user-reported V5 frozen method commits are not currently
resolvable from the public GitHub repository. This status must be changed only by
an explicit method-freeze commit after those prerequisites are satisfied.
