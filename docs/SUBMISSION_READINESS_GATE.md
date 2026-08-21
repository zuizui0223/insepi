# Submission readiness gate — standalone simulation methods paper

Primary target: **Methods in Ecology and Evolution**.
Secondary target if the final contribution reads more as sensing/informatics
architecture: **Ecological Informatics**.

This gate separates *method-development readiness* from *final validation outcome*.
It is intentionally stricter than “the code runs”.

## R1 — A method rather than workflow glue

**PASS.**

The transferable methodological object is now explicit:

```text
epistemically distinct acquisition signals
+ contradiction-guided falsification
+ guaranteed non-preferential exploration
+ independent targeted quotas
+ exact-budget spillover
+ sampling-distortion accounting
+ locked generational validation
```

The generic `interaction_sensing.guarded_portfolio` reference API expresses the
allocation method using arbitrary score names and has exact-selection parity tests
against the frozen V6 implementation. PolliPi/InsePi are the development instance,
not the public API specification.

## R2 — Formal method property

**PASS.**

`docs/EXPLORATION_GUARANTEE_THEORY.md` proves for
`Q = alpha U + (1-alpha)R`:

```text
TV(Q,U) = (1-alpha) TV(R,U) <= 1-alpha
Q(A) >= alpha U(A)
U(x)/Q(x) <= 1/alpha
D_infinity(U||Q) <= log(1/alpha)
```

The results require no assumptions about observer accuracy or independent failure.
They are sampling-safety guarantees, not performance claims.

## R3 — Broad applicability beyond one taxon/system

**PASS at architecture/API level; empirical transfer not claimed.**

`docs/GUARDED_PORTFOLIO_TUTORIAL.md` shows the same contracts for acoustic bird
monitoring, nest cameras, phenology cameras and wildlife camera traps. The generic
selector accepts user-defined evidence/observability/acquisition score arms.

Frozen PolliPi/InsePi weights are explicitly not claimed universal.

## R4 — Simulation/benchmark validation with known truth

**PASS for development and V5 falsification; FINAL PENDING V7.**

Evidence already includes latent-policy contradiction tests, byte-identical pixel
worlds, equal-budget Monte Carlo evaluation, prevalence shift, disturbance
mixtures/intensity changes, OOD conditions, arm-removal and OR/AND baselines,
Pareto/sampling-distortion metrics and preserved negative results.

V5 is a one-shot locked falsification of fixed scalar disagreement allocation.
V4 is explicitly development evidence for V6 and is not presented as untouched
validation.

## R5 — Final untouched validation

**BLOCKED, by design; execution path is complete.**

The final one-shot workflow now exists as `.github/workflows/v7-one-shot.yml`.
Its first CI execution completed successfully in `BLOCKED_SAFE` mode: every step
from frozen-branch verification through materialisation, observer inference and
scientific evaluation was skipped, and the final assertion confirmed that no V7
pixel artifact existed.

V7 remains blocked until the exact V5 observer commits become publicly reachable
as branch `frozen/v5-method` in their respective repositories:

- PolliPi `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`
- InsePi `980813bab996909020140fad5bd83b055eb3db9c`

`docs/V5_FROZEN_COMMIT_RECOVERY.md` gives the no-rewrite recovery contract.
This is the only remaining hard scientific blocker to the final validation run.

## R6 — Same-input / no-leakage validation boundary

**PASS at infrastructure level.**

V7 is structurally separated into:

1. external exact-branch reachability + lock verification;
2. frozen-observer API smoke tests **before any seed derivation**;
3. one canonical pixel materialisation;
4. independent observer trace generation from the same bytes in separate exact
   frozen checkouts;
5. trace-only allocation evaluation.

The external runners pass only image arrays to the observers. Latent truth is
attached after inference. The evaluator neither calls observers nor renders pixels.

## R7 — Metric semantics and anti-circularity

**PASS.**

Primary `hidden_error_recall` is explicitly labelled observer-relative PolliPi
detection/attribution-error recall. It is not treated as a world-intrinsic error
state.

V7 additionally reports observer-independent disturbance-window recall and
disturbed true-event recall. These secondary metrics do not change the
preregistered hard gate.

## R8 — Baselines and ablations

**PASS / FROZEN for V7.**

The final registry contains exactly nine policies: uniform, PolliPi-only,
InsePi-only, legacy fixed disagreement, OR, AND, frozen V6, V6 without PolliPi arm,
and V6 without InsePi arm.

Registry SHA-256:
`94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975`.

## R9 — Reproducibility and provenance

**PASS at pre-execution level.**

The package has source commit pins, exact frozen branch-tip checks,
seed-independent world-spec hash, deterministic seed derivation, canonical
pixel-artifact SHA-256, observer trace provenance, baseline-registry hash, report
hash, no-overwrite materialisation receipt and a final execution ledger recording
orchestrator/evaluator/materializer provenance.

The one-shot workflow treats **CI success as execution integrity**, not scientific
success. A scientifically falsifying V7 run still uploads the immutable report and
ledger with `V7_GATE=FAIL` and the preregistered claim level.

Final V7 hashes remain intentionally absent.

## R10 — Preserved falsification trail

**PASS.**

The manuscript blueprint begins with failed hypotheses rather than hiding them:
V3 showed direct disagreement was not automatically superior; V5 falsified fixed
scalar disagreement under prevalence shift; V6 changed policy class rather than
retuning the same score.

Disagreement survives as a diagnostic/development variable but has zero direct
frozen allocation weight.

## R11 — Claim ceiling fixed before final result

**PASS.**

`docs/V7_CLAIM_CEILING.md` maps V7 outcomes to maximum claims A–E before final
result inspection. `scripts/v7_evaluate_locked.py` applies that mapping to the
locked gate output and records the selected level in the execution ledger.

No V7 result may trigger same-generation retuning or a revised seed.

## R12 — Manuscript narrative and figure plan

**PASS as blueprint.**

`docs/METHOD_PAPER_BLUEPRINT.md` contains abstract, Introduction, Methods, Results,
Discussion, six main figures, supplementary package and prohibited-claim list.
The V7 Results subsection remains a genuine placeholder.

## R13 — Literature positioning

**PASS as working review; bibliography requires final metadata check.**

The method is explicitly distinguished from Query by Committee / disagreement
acquisition, N-version programming / majority consensus, differential testing,
ecological preferential sampling and camera-trap active learning.

The novelty claim is the falsification-driven architecture and exploration guard,
not a claim that disagreement, ensemble diversity or active learning is new.

## R14 — Software usability for external researchers

**PASS for core allocation API; polished release packaging remains pre-submission.**

Current public-facing components include the generic guarded-portfolio API,
taxon-agnostic tutorial, exact frozen-method parity tests, applicability guidance
and the full locked validation contract. Frozen 50/10/40 weights are an evaluated
instance, not universal defaults.

Before actual submission/release, concise API docs/version tag/citation metadata
may be added; those packaging changes must not alter frozen scientific evidence.

## R15 — Field-data boundary

**PASS.**

The manuscript explicitly makes no claims about field visit-rate accuracy, taxon
classifier accuracy, real-world power/storage performance or ecological effect
sizes. Empirical data are external validation, not retroactive justification for
the simulation method.

# Current readiness verdict

## Scientific method package

**READY FOR FINAL LOCKED VALIDATION.**

No additional V6 tuning or simulation development is justified before V7.
The one-shot execution software is staged and has been verified to fail closed.

## Final validation

**EXECUTION SOFTWARE READY; PROVENANCE INPUTS BLOCKED.**

The exact frozen V5 observer SHAs remain unreachable from public GitHub. Recovering
those unchanged commits as `frozen/v5-method` branch tips is now the sole blocker.
Once both tips match, the manifest can change from `blocked` to `ready`; that
single commit triggers exact-SHA verification, pre-materialisation API smoke tests,
deterministic seed derivation, one canonical pixel artifact, both frozen observer
traces, 200-replicate locked evaluation and claim-level assignment.

## Manuscript submission

**NOT SUBMISSION-READY until V7 claim level is known.**

Once V7 runs, the manuscript must take the highest allowed level in
`V7_CLAIM_CEILING.md` without changing the method generation.

# Actions allowed before V7

- improve exposition, bibliography metadata and presentation;
- prepare figures from V1–V6 development/falsification evidence;
- prepare manuscript text with V7 placeholders blank;
- recover the exact frozen commits without rewriting them;
- run blocked-safe CI/preflight.

# Actions forbidden before V7

- change frozen V6 weights or selector;
- tune observers using V7 families;
- inspect a final V7 seed/world;
- add/remove V7 baselines after seeing results;
- change hard pass/fail thresholds;
- reconstruct a lost frozen commit and label it the same V7 generation;
- rerun V6 candidate searches to find a larger apparent margin.
