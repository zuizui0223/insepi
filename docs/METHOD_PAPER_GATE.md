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

### G2 — Pixel parity

- Both repositories reproduce the same portable rendered world fingerprint.
- Both make decisions from identical pixels.
- Hidden scenario labels are used only for post-hoc evaluation, never as inputs to either sensing decision.

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

### G4 — Equal-budget competition

Compare at fixed storage / audit budget:

1. uniform sampling;
2. PolliPi candidate-priority;
3. InsePi audit-priority;
4. disagreement-priority.

Primary endpoints are fixed before looking at the result:

- latent observation-error recall;
- true-event recovery;
- false-event audit yield;
- missed-event audit yield;
- attribution-error audit yield;
- total-variation distortion of sampled disturbance conditions;
- captures or bytes per recovered hidden error.

No method is declared superior from classifier accuracy alone.

### G5 — Held-out generalisation

- Tune thresholds on calibration worlds only.
- Evaluate on held-out seeds, disturbance intensities, event prevalences, and mixed disturbances.
- Include at least one deliberately misspecified / out-of-distribution world family.
- Report where disagreement-priority loses as well as where it wins.

### G6 — Ablation

Required comparisons:

- disagreement score without PolliPi state;
- disagreement score without InsePi risk;
- simple union (`candidate OR risky`);
- simple intersection (`candidate AND risky`);
- learned or tuned combined score, if introduced;
- full independent disagreement policy.

This determines whether the gain comes from genuine contradiction structure rather than simply spending more observations on anything unusual.

### G7 — Reproducible benchmark ledger

Every headline result must be reproducible from:

- fixed simulator version;
- explicit seed registry;
- scenario manifest;
- source commit IDs for both programs;
- portable traces;
- one command or CI workflow producing manuscript tables.

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

## Current status

- G1: implemented in V1 architecture.
- G2: V2 portable-pixel contract implemented; CI validation required.
- G3: partial; single disturbances implemented, mixed/intensity gradients remain.
- G4: next implementation target.
- G5: not yet complete.
- G6: not yet complete.
- G7: CI benchmark ledgers started in both repositories.
