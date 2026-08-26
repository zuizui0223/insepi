# V7 execution architecture — one-shot validation runbook

V7 is the untouched validation generation for the V6 frozen allocation method.
This document freezes the execution architecture before the final observer commits
are reachable and before the V7 master seed is derived.

## Non-negotiable separation

V7 is a four-stage pipeline. No stage may silently absorb the responsibilities of
another.

```text
A. lock + reachability
        |
        v
B. canonical pixel materialisation
        |
        +----------------------+
        |                      |
        v                      v
C1. PolliPi trace        C2. InsePi trace
        |                      |
        +-----------+----------+
                    |
                    v
D. trace-only allocation evaluation + hard gate
```

The purpose of this split is not software elegance. It is the scientific control
that keeps latent truth, world generation, observer inference, and allocation
scoring from leaking into each other.

## Stage A — lock and external reachability

Inputs are frozen in `benchmarks/v7_lock_manifest.json`.

The current manifest is deliberately `status=blocked`. A V7 master seed may not be
derived while either frozen observer SHA cannot be externally resolved.

The lock verifier requires all of the following before returning validated frozen
inputs:

- reachable PolliPi frozen method SHA;
- reachable InsePi frozen method SHA;
- exact V6 allocator SHA;
- exact V7 generator SHA;
- exact baseline-registry SHA-256;
- exact seed-independent world-spec SHA-256;
- frozen V6 weights `E=.50/P=.10/I=.40/D=0`;
- frozen prevalence, budget, sample-size, replicate and pass/fail registries;
- absence of any already-materialised final seed/world/report fields.

External reachability is a real check supplied to the verifier. A syntactically
valid 40-hex string is not treated as proof of a reproducible commit.

Only after this stage passes may the deterministic master seed be derived from the
frozen identifiers. It is never hand-selected or rerolled.

## Stage B — canonical pixel materialisation

The V7 generator contract is frozen before seed derivation. It specifies:

- 180 latent conditions;
- 15 disturbance families;
- three intensity tiers;
- two replicate slots;
- visit absence/presence;
- 96 x 128 grayscale background/frame pairs;
- explicit OOD operators absent from V4: sensor banding, glare and framing drift.

After Stage A unlocks, `materialise_locked_v7()` performs exactly one
materialisation:

1. derive the locked master seed;
2. render the 180 condition pairs;
3. write one compressed canonical NPZ pixel artifact;
4. write an artifact manifest with world fingerprint and byte-level NPZ SHA-256;
5. write a materialisation receipt containing all frozen inputs and a receipt
   SHA-256;
6. refuse to overwrite any existing V7 output.

The canonical pixel artifact is the only V7 image input. PolliPi and InsePi do not
independently regenerate the world.

## Stage C — independent observer traces

### PolliPi

PolliPi reads the canonical artifact, verifies its bytes, then calls its frozen
observer as:

```text
analyze(frame, background)
```

No latent family, visit label, intensity, prevalence or budget is passed to the
observer. Latent metadata is attached to the trace only after the decision.

The trace provenance records the frozen PolliPi source commit, world fingerprint,
world-spec fingerprint and canonical pixel-artifact SHA-256.

### InsePi

InsePi follows the same boundary. Its frozen observer is injected as a two-image
decision function:

```text
decision_fn(frame, background)
```

The decision must emit observability/noise and false/missed/attribution-risk
outputs. Again, latent metadata is attached only after inference.

There is no PolliPi import in InsePi inference and no InsePi import in PolliPi
inference.

## Stage D — trace-only allocation evaluation

The evaluator receives only:

- PolliPi emitted trace;
- InsePi emitted trace;
- canonical artifact/world provenance;
- frozen baseline registry;
- locked master seed for paired Monte Carlo sampling.

It does not know how pixels were rendered and does not call either observer.

The locked comparator set contains nine policies:

1. uniform exploration;
2. PolliPi candidate priority;
3. InsePi audit priority;
4. legacy fixed scalar disagreement;
5. candidate OR risky;
6. candidate AND risky;
7. frozen V6 portfolio `E=.50/P=.10/I=.40/D=0`;
8. V6 without PolliPi allocation arm, quota returned to exploration;
9. V6 without InsePi allocation arm, quota returned to exploration.

All policies receive the same sampled world in every replicate. Core evaluation is
3 prevalences x 3 budgets x 4,800 windows x 200 paired replicates.

Primary outputs are true-event recall, hidden-error recall, captures per recovered
hidden error and disturbance-family TV distance.

## Locked hard gate

For V6 to support the strong standalone method claim, V7 must satisfy every rule:

1. every prevalence x budget regime has joint event/error ratio >= 0.98 relative
   to uniform;
2. mean joint ratio across the nine regimes is strictly > 1.00;
3. maximum disturbance-family TV <= 0.25;
4. V6 worst-joint robustness is not more than 0.01 below any frozen legacy
   targeted comparator;
5. neither PolliPi-arm removal nor InsePi-arm removal strictly dominates full V6
   on `(worst_joint, mean_joint, -max_TV)`;
6. latent-truth invariance remains enforced;
7. all world, artifact, trace and report hashes are preserved before
   interpretation.

V7 is not rerun with different weights, thresholds, family definitions or seed if
any rule fails.

## Current status

**BLOCKED_SAFE.**

The software route from lock verification through materialisation, independent
trace generation, trace-only evaluation and hard-gate reporting is implemented and
tested using explicit dummy test identifiers. Those dummy executions are unit
tests only and are not V7 evidence.

The final V7 seed, final V7 world fingerprint and final canonical pixel artifact
have not been materialised.

The remaining scientific blocker is reproducible reachability of the user-reported
V5 frozen observer commits. Once they are reachable, the adapters must be anchored
to those exact generations before the lock can change from `blocked` to `ready`.
