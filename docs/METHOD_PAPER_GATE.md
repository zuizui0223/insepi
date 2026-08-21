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

**Status: PASS for V2 and V4.** V2 and V4 fingerprints are fixed and verified independently in both repositories. PolliPi now emits a provenance-pinned V4 trace artifact rather than sharing decision code.

### G3 — Broad perturbation coverage

V4 covers visit presence/absence, wind, camera displacement, shadow, occlusion, blur, clutter, mixed disturbances, intensity shifts, and lens contamination as an OOD family.

**Status: PASS as a development benchmark, not final validation.** V4 test results were inspected during InsePi feature development and therefore V4 is explicitly a development holdout. Final untouched validation is reserved for locked V5.

### G4 — Equal-budget competition

Compare at fixed storage / audit budget:

1. uniform sampling;
2. PolliPi candidate-priority;
3. InsePi audit-priority;
4. disagreement-priority;
5. simple union and intersection ablations.

Primary endpoints:

- latent observation-error recall;
- true-event recovery;
- false-event audit yield;
- missed-event audit yield;
- attribution-error audit yield;
- total-variation distortion of sampled disturbance conditions;
- captures or bytes per recovered hidden error.

**Status: V3 IMPLEMENTED BUT NOT PASSED.** At a 25% budget on the first V2-derived competition, structured disagreement did not outperform the strongest alternatives. Hidden-error recall was about 0.251 for uniform, InsePi-only, and disagreement-priority. This negative result is retained; disagreement weights were not tuned to force a win.

**V4 cross-budget bridge now exists.** PolliPi emits a source-commit/world-fingerprint trace artifact and InsePi has a provenance-checked cross-repo V4 runner. The next comparison uses the improved gradient-structure observability observer.

### G5 — Held-out generalisation

V4 used separate calibration/test seeds and intensities plus mixed and OOD families. Because V4 test output was subsequently used diagnostically, it is no longer the final untouched evidence.

**Status: DEVELOPMENT PASS / FINAL PENDING.** A one-shot V5 protocol is preregistered in `docs/V5_LOCKED_VALIDATION.md`. V5 seeds will be derived from the frozen PolliPi and InsePi commit SHAs, preventing favourable seed selection after results are known.

### G6 — Ablation

Required comparisons:

- disagreement without PolliPi state;
- disagreement without InsePi risk;
- simple union (`candidate OR risky`);
- simple intersection (`candidate AND risky`);
- learned/tuned combined score, if introduced;
- full independent disagreement policy.

**Status: PARTIAL.** Union and intersection are already implemented. Single-view removals and any learned-score ablation remain.

### G7 — Reproducible benchmark ledger

Every headline result must be reproducible from fixed simulator versions, seed registries, source commits, fingerprints, traces and CI.

**Status: STRONG.** Both repositories emit benchmark ledgers. PolliPi now publishes a V4 JSONL artifact containing source commit and world fingerprint provenance; InsePi consumes emitted traces without importing PolliPi decision logic.

## What V3 falsified

The first equal-budget result falsified the naive expectation that disagreement alone is automatically superior. Identical-pixel inspection showed that InsePi failed to provide independent warning for several PolliPi misses, especially occlusion/blur/clutter in V2.

## V4 development result

The initial intensity-correlation occlusion audit recovered all V4 disturbances but falsely flagged 50% of clean test windows. It was rejected.

Replacing it with **local gradient-correlation** gave a much better trade-off:

- test clean false-risk rate: **0.00**;
- test disturbance risk recall: **0.875**;
- occlusion risk recall: **0.75**;
- occlusion+blur: **1.00**;
- wind, shadow, shake and mixed broad disturbances: **1.00**;
- lens OOD: **0.00**.

The lens miss is intentionally retained rather than tuned away: V4 is for development diagnosis, and V5 will test whether the final architecture generalises without another tuning cycle.

PolliPi V4 visit recovery on the same pixels is only about **0.353** overall, with zero recovery in occlusion, shadow, shake and several mixed families. This creates the complementary-error structure required for a meaningful disagreement test, but the actual equal-budget advantage remains to be demonstrated.

## Development rule

Do not modify disagreement weights merely to win a benchmark. Improve an observer only for an independently justified observation-process failure, and separate development holdouts from the final locked validation.

## Falsification criteria

The strong method-paper claim fails or must be narrowed if, on locked equal-budget validation:

- disagreement-priority is consistently dominated by a single-program policy;
- any apparent gain disappears under the `candidate OR risky` ablation;
- gains depend on hidden true-event labels in allocation;
- clean-scene false-audit cost removes the hidden-error benefit;
- gains collapse under prevalence or disturbance shifts;
- cross-repository provenance/fingerprints diverge.

## Manuscript structure if gates pass

1. **Problem:** ecological cameras estimate biological processes through a noisy observation process; target-first filtering and noise-first auditing optimise different objectives.
2. **Method:** independent parallel observers + post-decision disagreement operator.
3. **Theory/taxonomy:** agreement, complementary caution, allocation conflict, hidden-miss conflict, false-candidate conflict.
4. **Development evidence:** V1 latent-policy contradiction, V2 identical pixels, V3 negative equal-budget result, V4 observer improvement.
5. **Locked validation:** one-shot V5 across budgets and prevalence shifts.
6. **Ablations/Pareto frontier.**
7. **Scope:** no field-accuracy claim; empirical deployment is external validation.

## Current paper-readiness decision

**Not submission-ready yet, but substantially closer.** The architecture, reproducibility boundary, negative-result logic, and an improved complementary observability observer are now defensible. The decisive remaining tasks are: V4 cross-budget competition with the emitted PolliPi trace, missing ablations, then method freeze and one-shot V5.
