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

Evidence already includes:

- latent-policy contradiction tests;
- byte-identical pixel worlds;
- equal-budget Monte Carlo evaluation;
- prevalence shift;
- disturbance mixtures/intensity changes;
- OOD conditions;
- arm-removal and logical OR/AND baselines;
- Pareto and sampling-distortion metrics;
- preserved negative results.

V5 is a one-shot locked falsification of fixed scalar disagreement allocation.
V4 is explicitly development evidence for V6 and is not presented as untouched
validation.

## R5 — Final untouched validation

**BLOCKED, by design.**

V7 software infrastructure is complete and preflight is `BLOCKED_SAFE`, but the
final seed/world cannot be materialised until the exact user-reported V5 frozen
observer commits become externally reachable:

- PolliPi `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`
- InsePi `980813bab996909020140fad5bd83b055eb3db9c`

This is the only remaining hard scientific blocker to the final validation run.

## R6 — Same-input / no-leakage validation boundary

**PASS at infrastructure level.**

V7 is structurally separated into:

1. external reachability + lock verification;
2. one canonical pixel materialisation;
3. independent observer trace generation from the same bytes;
4. trace-only allocation evaluation.

Observer adapters accept image arrays only. Latent truth is attached after
inference. The final evaluator does not call observers or render pixels.

## R7 — Metric semantics and anti-circularity

**PASS.**

Primary `hidden_error_recall` is explicitly labelled observer-relative PolliPi
detection/attribution-error recall. It is not treated as a world-intrinsic error
state.

V7 additionally reports observer-independent:

- disturbance-window recall;
- disturbed true-event recall.

These secondary metrics do not change the preregistered hard gate.

## R8 — Baselines and ablations

**PASS / FROZEN for V7.**

The final registry contains exactly nine policies:

1. uniform;
2. PolliPi-only;
3. InsePi-only;
4. legacy fixed disagreement;
5. OR;
6. AND;
7. frozen V6;
8. V6 without PolliPi allocation arm;
9. V6 without InsePi allocation arm.

Registry SHA-256:
`94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975`.

## R9 — Reproducibility and provenance

**PASS at pre-execution level.**

The package has:

- source commit pins;
- seed-independent world-spec hash;
- deterministic seed derivation;
- canonical pixel-artifact SHA-256;
- observer trace provenance;
- baseline-registry hash;
- report hash;
- no-overwrite one-shot materialisation receipt;
- CI-enforced blocked state before final V7.

Final V7 hashes remain intentionally absent.

## R10 — Preserved falsification trail

**PASS.**

The manuscript blueprint begins with the failed hypotheses rather than hiding them:

- V3: direct disagreement not automatically superior;
- V5: fixed scalar disagreement not prevalence robust;
- V6: change policy class, not same-test retuning.

Disagreement survives as a diagnostic/development variable but has zero direct
frozen allocation weight.

## R11 — Claim ceiling fixed before final result

**PASS.**

`docs/V7_CLAIM_CEILING.md` maps V7 outcomes to maximum claims A–E before final
result inspection.

No V7 result may trigger same-generation retuning or a revised seed.

## R12 — Manuscript narrative and figure plan

**PASS as blueprint.**

`docs/METHOD_PAPER_BLUEPRINT.md` contains abstract, Introduction, Methods, Results,
Discussion, six main figures, supplementary package and prohibited-claim list.
The V7 Results subsection remains a genuine placeholder.

## R13 — Literature positioning

**PASS as working review; bibliography requires final metadata check.**

The method is explicitly distinguished from:

- Query by Committee / disagreement acquisition;
- N-version programming / majority consensus;
- differential testing;
- ecological preferential sampling;
- camera-trap active learning.

The novelty claim is the falsification-driven architecture and exploration guard,
not a claim that disagreement, ensemble diversity, or active learning is new.

## R14 — Software usability for external researchers

**PASS for core allocation API; polished release packaging remains a pre-submission task.**

Current public-facing components:

- generic guarded-portfolio API;
- taxon-agnostic tutorial;
- exact frozen-method parity tests;
- explicit applicability / non-applicability guidance.

Before actual submission/release, add concise API docs/version tag/citation metadata
only; these are packaging tasks and must not alter frozen scientific evidence.

## R15 — Field-data boundary

**PASS.**

The manuscript explicitly makes no claims about:

- field visit-rate accuracy;
- taxon classifier accuracy;
- real-world power/storage performance;
- ecological effect sizes.

Empirical data are external validation, not retroactive justification for the
simulation method.

# Current readiness verdict

## Scientific method package

**READY FOR FINAL LOCKED VALIDATION, subject to observer-commit reachability.**

No additional V6 tuning or simulation development is justified before V7.

## Final validation

**NOT YET RUNNABLE REPRODUCIBLY.**

The exact frozen V5 observer SHAs remain unreachable from public GitHub. The V7
lock must remain blocked until this provenance gap is closed.

## Manuscript submission

**NOT SUBMISSION-READY until V7 claim level is known.**

Once V7 runs, the manuscript should take the highest allowed level in
`V7_CLAIM_CEILING.md` without changing the method generation.

# Actions allowed before V7

- improve exposition, tutorial and documentation;
- verify bibliography metadata;
- prepare figures using V1–V6 development/falsification evidence;
- prepare manuscript text that leaves V7 placeholders blank;
- make the frozen observer commits externally reachable;
- anchor thin V7 adapters to those exact commits;
- run CI/preflight.

# Actions forbidden before V7

- change frozen V6 weights or selector;
- tune observers using V7 families;
- inspect a final V7 seed/world;
- add or remove V7 baselines after seeing results;
- change hard pass/fail thresholds;
- rerun V6 candidate searches to find a larger apparent margin.
