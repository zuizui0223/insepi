# Method-paper gate: disagreement-driven ecological sensing

## Submission claim

The pre-empirical paper should not claim field accuracy. Its standalone claim is methodological:

> Keeping two observation programs epistemically independent, then using their structured disagreement as an adaptive audit signal, can improve discovery of observation-process failures under finite sensing budgets compared with either program alone.

PolliPi supplies a biological-evidence / capture-allocation view. InsePi supplies an observability / error-process view. The methodological object is the **development and sensing protocol built around their disagreement**, not a new monolithic classifier.

## What must be true before submission

A simulation-only manuscript is ready only after all gates below pass.

### G1 — Independent implementations

- PolliPi and InsePi remain separately executable.
- Neither imports the other's decision logic.
- Common material is restricted to benchmark contracts, latent truth, rendered pixels, and portable traces.
- Agreement is never a tuning target.

**Status: PASS for the current V1–V4 architecture.**

### G2 — Pixel parity

- Both repositories reproduce the same portable rendered world fingerprint.
- Both make decisions from identical pixels.
- Hidden scenario labels are used only for post-hoc evaluation, never as inputs to either sensing decision.

**Status: PASS for V2.** Both repositories reproduce the same V2 SHA-256 fingerprint. V4 adds a second held-out factorial pixel contract and must pass its fingerprint CI before promotion.

### G3 — Broad perturbation coverage

At minimum, simulations vary independently:

- true local event presence / absence;
- event visibility / signal-to-noise ratio;
- vegetation motion;
- camera displacement;
- illumination / moving shadow;
- occlusion;
- blur / focus degradation;
- multi-object clutter;
- unknown / out-of-distribution disturbance;
- mixed disturbances and intensity gradients.

**Status: IN PROGRESS.** V2 covers single canonical cases. V4 now separates calibration/test seeds and intensities, adds mixed wind+shadow, shake+clutter, occlusion+blur, and a test-only lens-contamination OOD family.

### G4 — Equal-budget competition

Compare at fixed storage / audit budget:

1. uniform sampling;
2. PolliPi candidate-priority;
3. InsePi audit-priority;
4. disagreement-priority;
5. simple union and intersection ablations.

Primary endpoints are fixed before looking at the result:

- latent observation-error recall;
- true-event recovery;
- false-event audit yield;
- missed-event audit yield;
- attribution-error audit yield;
- total-variation distortion of sampled disturbance conditions;
- captures or bytes per recovered hidden error.

No method is declared superior from classifier accuracy alone.

**Status: IMPLEMENTED BUT NOT PASSED in V3.** At a 25% budget on the first V2-derived competition, structured disagreement did **not** outperform the strongest alternatives. Hidden-error recall was approximately 0.251 for uniform, InsePi-only, and disagreement-priority. PolliPi-only and simple union were worse for hidden-error discovery but recovered more true events. Therefore the strong methods-paper claim is **not yet supported**.

This negative result is retained as a development result. The disagreement weights must not be tuned merely to force superiority.

### G5 — Held-out generalisation

- Tune thresholds on calibration worlds only.
- Evaluate on held-out seeds, disturbance intensities, event prevalences, and mixed disturbances.
- Include at least one deliberately misspecified / out-of-distribution world family.
- Report where disagreement-priority loses as well as where it wins.

**Status: V4 IMPLEMENTATION STARTED.** The V4 registry has separate calibration/test seeds and intensities, mixed disturbances only in test, and lens contamination only in test as OOD.

### G6 — Ablation

Required comparisons:

- disagreement score without PolliPi state;
- disagreement score without InsePi risk;
- simple union (`candidate OR risky`);
- simple intersection (`candidate AND risky`);
- learned or tuned combined score, if introduced;
- full independent disagreement policy.

This determines whether the gain comes from genuine contradiction structure rather than simply spending more observations on anything unusual.

**Status: PARTIAL.** Union and intersection are already in V3. Single-view removals and any learned-score ablation remain.

### G7 — Reproducible benchmark ledger

Every headline result must be reproducible from:

- fixed simulator version;
- explicit seed registry;
- scenario manifest;
- source commit IDs for both programs;
- portable traces;
- one command or CI workflow producing manuscript tables.

**Status: IN PROGRESS.** Both repositories emit CI benchmark ledgers. InsePi consumes an immutable PolliPi V2 trace snapshot named by PolliPi source commit rather than importing PolliPi logic.

## What V3 falsified

The first equal-budget result falsified the naive expectation that disagreement alone is automatically superior. Inspection of the identical-pixel traces identified the limiting mechanism:

- PolliPi misses true visits under vegetation motion, camera shake, shadow, clutter, occlusion, and blur in the V2 world.
- InsePi correctly marks several broad-disturbance cases as audit-priority, but its current pixel front end calls the V2 occlusion, blur, and clutter cases clean.
- Consequently the second observer supplies no independent warning for several PolliPi hidden misses, so disagreement-priority cannot recover them better than uniform sampling.

This is precisely the intended role of parallel contradictory development: a failed combined result localises which observer lacks complementary information.

## Development rule after V3

Do **not** modify disagreement weights to win V3. Improve an observer only when a failure is diagnosed from calibration conditions or from a target-independent observability principle, then evaluate the change on untouched held-out/OOD conditions.

For V4, observation-process interventions are rendered more physically. In particular, blur is applied to the scene rather than represented merely by a weak local event. Calibration may be used to develop texture-loss, occlusion, clutter, and other target-independent observability features; test labels must remain inaccessible to tuning.

## Falsification criteria

The method-paper claim fails or must be narrowed if, on held-out equal-budget simulations:

- disagreement-priority is consistently dominated by a single-program policy;
- any apparent gain disappears under the `candidate OR risky` ablation;
- gains depend on using hidden true-event labels in the allocation score;
- cross-repository pixel fingerprints diverge;
- performance collapses under modest changes in event prevalence or disturbance intensity.

A negative result is still informative for development, but it is not sufficient for the strong standalone methods claim above.

## Manuscript structure if gates pass

1. **Problem:** ecological cameras estimate biological processes through a noisy observation process; target-first filtering and noise-first auditing optimize different objectives.
2. **Method:** independent parallel observers + post-decision disagreement operator.
3. **Theory / taxonomy:** agreement, complementary caution, allocation conflict, hidden-miss conflict, false-candidate conflict.
4. **Simulation benchmark:** latent-policy V1, identical-pixel V2, equal-budget V3, held-out/OOD V4.
5. **Results:** Pareto comparison of error discovery, event recovery, and resource cost.
6. **Ablations:** show whether structured disagreement adds information beyond union/intersection heuristics.
7. **Scope:** no field-accuracy claim; empirical PolliPi/InsePi deployment is external validation and a later paper/application.

## Current paper-readiness decision

**Not submission-ready yet.** The architecture and reproducibility claim are already defensible, but the central performance claim has not passed its own falsification test. The next decisive result is held-out V4: whether calibration-only improvement of the independent observability observer creates complementary error information that lets structured disagreement improve the equal-budget Pareto frontier without using hidden test truth.
