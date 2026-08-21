# V7 locked validation protocol — pre-execution boundary

**Do not generate or run V7 from this document.** This file defines the claim
boundary before any final V7 world is materialised.

## Frozen V6 candidate

High-resolution V4 development is complete and the V6 allocator is frozen.

- method: `exploration_guarded_dual_observer_portfolio_v6`
- allocator implementation commit:
  `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`
- exact weights: exploration `0.50`, PolliPi `0.10`, InsePi `0.40`, direct
  disagreement `0.00`
- freeze manifest: `benchmarks/v6_method_freeze.json`
- development world fingerprint:
  `10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`

V4 remains development evidence; it is not final validation.

## Why V7 exists

V5 falsified fixed scalar disagreement allocation. V6 is a new allocation family
built from V1–V5/V4 development evidence. Because V4 has been repeatedly
inspected during V6 development, it cannot carry the final generalisation claim.
V7 is a new one-shot validation generation.

## Frozen V7 infrastructure

The seed-independent validation contract is already frozen before final observer
reachability is restored.

- V7 generator commit:
  `1c4c5ffc214ebdfb71ddabe170a071352acd4879`
- seed-independent world-spec SHA-256:
  `9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3`
- baseline/ablation registry SHA-256:
  `94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975`
- blocked lock manifest: `benchmarks/v7_lock_manifest.json`
- execution architecture: `docs/V7_EXECUTION_ARCHITECTURE.md`
- metric semantics audit: `docs/V7_METRIC_AUDIT.md`
- pre-result claim map: `docs/V7_CLAIM_CEILING.md`

The generator contract contains exactly 180 conditions: 15 disturbance families x
3 intensity tiers x 2 replicate slots x visit absence/presence. It includes
seed-locked OOD operators absent from V4 (`sensor_banding`, `glare`, and
`framing_drift`).

No final master seed, final world fingerprint or final pixel artifact exists.

## Preconditions before V7 may be materialised

All must be true:

1. PolliPi observer code used by V7 is frozen at an explicit reachable commit.
2. InsePi observer code used by V7 is frozen at an explicit reachable commit.
3. The V6 allocation candidate is frozen at an explicit reachable commit.
4. The exact allocation weights are committed in a method-freeze manifest.
5. Baseline policies and ablations are frozen.
6. V7 generator code, disturbance-family registry, prevalence regimes, budgets,
   metrics, and pass/fail rules are committed.
7. The V7 seed-generation rule is committed, but the resulting world has not been
   rendered or inspected.
8. The user-reported V5 frozen commits/evidence are published or otherwise made
   reproducibly materialisable.

Preconditions **3–7 are satisfied**. Preconditions **1, 2 and 8 remain blocked**
because the user-reported V5 observer SHAs are still not resolvable from public
GitHub.

## Seed rule

Only after `validate_ready_manifest()` verifies all frozen inputs and externally
verified observer reachability may the master seed be derived.

The committed seed domain is:

```text
pollipi-insepi-v7-master-seed-v1
```

and the effective rule is:

```text
SHA256(
  domain |
  pollipi_method_sha |
  insepi_method_sha |
  allocator_sha |
  generator_sha |
  baseline_registry_sha256 |
  world_spec_sha256
)
```

For V7, the allocator and generator identifiers are already frozen to:

- allocator: `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`
- generator: `1c4c5ffc214ebdfb71ddabe170a071352acd4879`

The seed may not be hand-picked, rerolled, replaced or inspected before the lock is
ready.

## Canonical pixel rule

After seed unlock, V7 is rendered **once** into one canonical compressed pixel
artifact. PolliPi and InsePi must consume those exact bytes; they do not regenerate
V7 independently.

The canonical artifact manifest records:

- world-spec SHA-256;
- final V7 world fingerprint;
- condition count and shape;
- byte-level pixel-artifact SHA-256.

Both observer traces must name the same world fingerprint and same pixel-artifact
SHA-256.

## Core regimes

V7 retains the unknown-prevalence stress dimensions that falsified V5:

- rare prevalence: `0.10`;
- balanced prevalence: `0.50`;
- common prevalence: `0.90`;
- sensing/audit budgets: `0.10`, `0.25`, `0.50`.

Each regime uses 4,800 sampled windows and 200 paired Monte Carlo replicates.

## Required comparators

The registry contains exactly nine policies:

1. uniform exploration;
2. PolliPi-only candidate priority;
3. InsePi-only audit priority;
4. legacy fixed scalar disagreement;
5. candidate OR risky;
6. candidate AND risky;
7. frozen V6 `E=.50/P=.10/I=.40/D=0`;
8. V6 with PolliPi allocation arm removed and quota returned to exploration;
9. V6 with InsePi allocation arm removed and quota returned to exploration.

Because the frozen V6 candidate has disagreement weight zero, no artificial
positive disagreement quota is introduced for V7.

## Primary paired metrics

All policies receive the same sampled world in each replicate.

For each prevalence x budget regime report:

- true-event recall;
- **observer-relative hidden-error recall**: recovery of latent-truth PolliPi
  detection/attribution errors;
- captures per recovered hidden error;
- disturbance-distribution total-variation distance;
- paired ratios against uniform for true-event and hidden-error recall.

The headline robustness statistic remains:

```text
worst_joint_ratio = min_regime(
  min(event_ratio_to_uniform, hidden_error_ratio_to_uniform)
)
```

This definition is unchanged from the frozen V6/V7 hard-gate logic and directly
tests the prevalence-shift failure discovered in V5.

## Observer-independent secondary metrics

To prevent circular interpretation of `hidden_error_recall`, V7 also reports two
latent-world-only coverage metrics:

- disturbance-window recall: selected non-clean windows / all non-clean windows;
- disturbed true-event recall: selected true visits under non-clean disturbance /
  all true visits under non-clean disturbance.

These metrics do not inspect PolliPi state or InsePi risks and **do not change the
locked hard gate**. Their role is interpretation and reviewer-facing robustness.
See `docs/V7_METRIC_AUDIT.md`.

## Locked pass/fail rules

A strong V6 allocation claim passes only if all are satisfied:

1. **No material prevalence-regime collapse:** every regime has
   `joint_ratio >= 0.98` against uniform.
2. **Overall benefit:** mean joint ratio across the nine core regimes is > 1.00.
3. **Selection-bias control:** maximum disturbance TV distance is <= 0.25.
4. **Robustness relative to legacy allocation:** the frozen V6 candidate's
   worst-joint ratio is at least as high as every frozen legacy targeted
   comparator, within a 0.01 numerical tolerance.
5. **Observer contribution:** neither the PolliPi-arm removal nor the InsePi-arm
   removal may strictly dominate full V6 on
   `(worst_joint_ratio, mean_joint_ratio, -max_tv)`.
6. **No hidden-truth leakage:** flipping latent truth while holding emitted
   observer traces fixed leaves V6 selections unchanged.
7. **Reproducibility:** world fingerprint, canonical pixel hash, emitted trace
   provenance, report hash, source commits and test counts are recorded before
   interpretation.

Failure of any hard rule lowers the claim ceiling according to
`docs/V7_CLAIM_CEILING.md`. V7 is not rerun with modified weights, thresholds,
family definitions or seed under the same generation label.

## Execution stages

V7 must execute in four separated stages:

```text
A. lock + external reachability
B. one canonical pixel materialisation
C. independent PolliPi and InsePi trace generation
D. trace-only paired evaluation + hard gate
```

The evaluator does not call either observer and does not render pixels. The
observers do not receive latent truth as decision input. See
`docs/V7_EXECUTION_ARCHITECTURE.md`.

## One-shot rule

After first V7 result inspection:

- do not modify V6 method code and call the same V7 a validation;
- do not choose a new seed;
- do not regenerate a preferred world;
- do not delete failing baselines, regimes or OOD families;
- preserve the full result and claim ceiling;
- any subsequent method change becomes a new method generation and requires a
  new validation generation.

## Current status

V7 execution is **BLOCKED_SAFE**.

The seed-independent generator, canonical-artifact contract, independent observer
adapters, trace-only evaluator, hard gate, materialiser and preflight tests are
implemented. The committed blocked manifest is verified by CI, and the latest
preflight explicitly records:

```text
V7_MASTER_SEED NOT_MATERIALISED
V7_WORLD_FINGERPRINT NOT_MATERIALISED
V7_PIXEL_ARTIFACT NOT_MATERIALISED
```

The remaining blocker is reproducible reachability of the user-reported V5 frozen
observer commits:

- PolliPi: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`
- InsePi: `980813bab996909020140fad5bd83b055eb3db9c`

Until both are externally reachable and the thin artifact adapters are anchored to
those exact method generations, the lock must remain blocked and no final V7 seed
may be derived.
