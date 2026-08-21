# Supplementary Information — pre-V7 locked version

**Manuscript:** *When disagreement should not drive sampling: contradiction-guided development of exploration-guarded ecological sensing*

This document contains only evidence available before the final one-shot V7 materialisation. No V7 seed, pixel array, observer trace or result is included. Sections marked `[[V7_LOCKED_RESULT]]` may be completed only from the immutable V7 execution ledger.

---

## Appendix S1. Observer contracts

| Property | Biological-evidence observer | Observability-risk observer |
|---|---|---|
| Scientific question | Is there local visual evidence for a biological interaction candidate? | Is the observation process reliable enough for event/absence/attribution interpretation? |
| Core output | candidate / uncertain / environmental-noise / no-activity state | clean / audit-priority / confounded / unobservable state plus risk scores |
| Intended allocation role in frozen V6 | 10% evidence quota | 40% observability-risk quota |
| Not intended to infer | whether non-detection is trustworthy under every observation condition | whether a biological event is actually present |
| Cross-observer dependency | none during inference | none during inference |
| Comparison stage | after both traces are emitted | after both traces are emitted |

The observers are epistemically distinct rather than redundant estimators of a common label. Independence here means implementation and decision-contract separation; it does not imply statistically independent errors.

---

## Appendix S2. Method-generation ledger

| Generation | Core question | Evidence role | Outcome | Consequence |
|---|---|---|---|---|
| V1 | Do distinct observer objectives create structured contradictions? | development | yes | preserve both views |
| V2 | Do contradictions persist from byte-identical pixels? | development | yes; additional front-end misses exposed | use portable traces and same-pixel parity |
| V3 | Does direct disagreement win under equal budget? | development falsification | no | do not assume disagreement is an acquisition objective |
| V4 | Can observability become complementary without merging observers? | development | calibration-only local-structure improvement retained | V4 downgraded to development after inspection |
| V5 | Is fixed scalar disagreement prevalence-robust? | one-shot locked validation | **FAIL** | change policy class, not score weights |
| V6 | Can guaranteed exploration plus separate observer quotas repair the allocation seam? | development | E=.50/P=.10/I=.40/D=0 frozen | stop V6 search |
| V7 | Does frozen V6 survive a new locked world? | one-shot final validation | `[[V7_LOCKED_RESULT]]` | claim level A–E determined mechanically |

---

## Appendix S3. Complete V3 equal-budget comparison

V3 used the shared V2 pixel conditions, 25% acquisition budget, 2,400 sampled windows per replicate and 100 deterministic paired replicates.

| Policy | True-event recall | Observer-relative hidden-error recall | Missed-event audit yield | Captures per hidden error | Disturbance TV |
|---|---:|---:|---:|---:|---:|
| Uniform | 0.251 | 0.251 | 0.503 | 1.992 | 0.022 |
| Biological candidate only | 0.325 | 0.100 | 0.201 | 5.019 | 0.301 |
| Observability audit only | 0.189 | 0.251 | 0.503 | 1.990 | 0.667 |
| Candidate OR risky | 0.313 | 0.084 | 0.168 | 6.016 | 0.261 |
| Candidate AND risky | 0.284 | 0.182 | 0.365 | 2.745 | 0.251 |
| Fixed disagreement | 0.188 | 0.251 | 0.502 | 1.995 | 0.500 |

The early result shows why neither event recall nor hidden-error recall alone can define the allocation objective. Targeted policies can improve one quantity while degrading another or severely distorting the disturbance distribution.

---

## Appendix S4. V4 observability-development diagnostics

V4 contained 120 deterministic same-pixel conditions split into calibration and inspected development-test conditions. The retained observability front end calibrated a local high-frequency structure-loss threshold only on the calibration split.

At the final retained V4 development state:

- calibration disturbance-risk recall = 0.7292;
- inspected test disturbance-risk recall = 0.8750;
- inspected clean false-risk rate = 0.0000;
- test risk recall was 1.0 for blur, occlusion+blur, shadow, shake, shake+clutter, wind and wind+shadow;
- test risk recall was 0.75 for clutter and occlusion;
- the unseen lens family remained 0.0, preventing a misleading claim that every novel corruption was automatically detected.

Because the V4 test output was inspected during this feature development, V4 is reported only as development evidence.

---

## Appendix S5. Locked V5 falsification record

### S5.1. Frozen design

- 180 conditions;
- 3 event-prevalence regimes: rare, balanced, common;
- 3 finite budget fractions: 10%, 25%, 50%;
- 8 policies;
- 4,800 windows per sampled world;
- 200 paired replicates;
- method code frozen before one-shot inspection.

Frozen evidence identifiers:

- V5 world fingerprint: `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`;
- biological-observer trace SHA-256: `56ec4de0b710273ee47e500d6b1d7f92c50ba40274619528f857e133633385c0`;
- cross-report SHA-256: `a6d1f30b3d18707e83cb5d0d5f60581d06fdf42f7bbe485fb0992079f3ce495e`.

### S5.2. Falsified claim

The tested claim was:

> A fixed scalar ranking derived from independent-observer disagreement is a robust finite-budget acquisition policy under shifts in event prevalence.

The claim failed. Only the balanced-prevalence, 25%-budget regime satisfied the complete locked gate. In rare-prevalence 10% and 25% regimes, fixed disagreement fell off the Pareto frontier and was inferior to a single-view removal. At common prevalence and 25% budget, observability-only allocation recovered more hidden errors. At low budget, disturbance-distribution TV could approach approximately 0.833.

Complementary observer signals nevertheless remained in six to seven disturbance families within each prevalence regime. The failure therefore localised to the scalar allocation seam rather than to complete loss of observer complementarity.

### S5.3. Frozen V5 method commits

- biological-evidence observer: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- observability-risk observer: `980813bab996909020140fad5bd83b055eb3db9c`.

These exact git objects remain the provenance prerequisite for V7. Reconstructed or rebased equivalents are not substituted under the same generation label.

---

## Appendix S6. V6 focused candidate comparison

All focused candidates used direct-disagreement quota 0 and biological-evidence quota 0.10. High-resolution development used paired 4,800-window worlds and 200 replicates across all 3 prevalence × 3 budget regimes.

| Candidate | Exploration | Evidence | Observability | Disagreement | 9-regime gate | Worst joint ratio | Mean joint ratio | Max TV |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| E40/P10/I50 | 0.40 | 0.10 | 0.50 | 0.00 | FAIL | — | — | 0.26567 |
| **E50/P10/I40** | **0.50** | **0.10** | **0.40** | **0.00** | **PASS** | **1.00846** | **1.11642** | **0.21919** |
| E60/P10/I30 | 0.60 | 0.10 | 0.30 | 0.00 | PASS | 1.00832 | 1.10303 | 0.17222 |
| E70/P10/I20 | 0.70 | 0.10 | 0.20 | 0.00 | FAIL | 0.98329 | — | — |

The predefined development ordering preferred passing the hard gate, then stronger worst-case and mean joint recovery subject to the TV ceiling. E50/P10/I40 was frozen; V6 candidate search subsequently stopped.

Frozen allocator implementation commit: `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`.

---

## Appendix S7. Exploration-guard derivation

Let U be the non-preferential target sampling distribution, R an arbitrary targeted distribution and α ∈ (0,1] the guaranteed exploration share. Define

\[
Q = \alpha U + (1-\alpha)R.
\]

Then

\[
Q-U = (1-\alpha)(R-U),
\]

and by homogeneity of total variation,

\[
TV(Q,U) = (1-\alpha)TV(R,U) \le 1-\alpha.
\]

For any measurable set A,

\[
Q(A)=\alpha U(A)+(1-\alpha)R(A)\ge\alpha U(A).
\]

For every x in the support of U,

\[
Q(x)\ge\alpha U(x),
\]

hence

\[
\frac{U(x)}{Q(x)}\le\frac{1}{\alpha}.
\]

Taking the essential supremum of the log ratio gives

\[
D_\infty(U\Vert Q)\le\log(1/\alpha).
\]

For α=0.5, the ideal target-to-adaptive importance ratio is therefore bounded by 2. These identities are properties of the sampling mixture and make no assumption that either observer is accurate or that their failures are statistically independent.

---

## Appendix S8. V7 seed-independent preregistration

### S8.1. Frozen identifiers

- allocator commit: `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`;
- generator commit: `1c4c5ffc214ebdfb71ddabe170a071352acd4879`;
- evaluator commit: `6860fa973ce8f25b25028f49723710e8a920709c`;
- materializer commit: `11f5a7ad97dc71720a5ba0249bf36c6997a4e289`;
- V7 world-spec SHA-256: `9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3`;
- baseline-registry SHA-256: `94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975`.

### S8.2. World contract

V7 specifies 180 conditions from 15 disturbance families × 3 intensity tiers × 2 replicate slots × visit absence/presence. The registry includes new OOD perturbations such as sensor banding, glare and framing drift. Concrete pixels are not rendered until the lock is ready.

### S8.3. Core evaluation

- prevalence = 0.10, 0.50, 0.90;
- budget = 0.10, 0.25, 0.50;
- world windows = 4,800;
- replicates = 200;
- nine frozen policies/ablations;
- paired sampled worlds across policies.

### S8.4. Hard rules

The full V6 candidate passes the strongest claim gate only if:

1. every prevalence × budget regime has joint event/error ratio ≥ 0.98 relative to uniform;
2. mean joint ratio across nine regimes is >1.0;
3. maximum disturbance TV ≤0.25;
4. worst-joint robustness is not materially lower than any frozen legacy targeted comparator (0.01 tolerance);
5. neither observer-arm removal strictly dominates full V6 on `(worst_joint_ratio, mean_joint_ratio, -max_tv)`;
6. hidden truth cannot affect allocation while emitted observer traces are held fixed;
7. world, pixel, trace, source and report provenance is internally consistent.

### S8.5. Current pre-execution status

`[[V7_LOCKED_RESULT:STATUS]]`

Until the exact two V5 observer git objects are externally reachable, the committed V7 lock remains blocked and no final seed/pixel artifact may be generated.

---

## Appendix S9. V7 results and complete evidence ledger

`[[V7_LOCKED_RESULT:SUPPLEMENTARY]]`

This section must be generated from the one-shot execution ledger. It will contain:

- all nine policy summaries for every prevalence × budget regime;
- observer-independent disturbance-window and disturbed-true-event coverage;
- arm-removal results;
- family-level observer complementarity diagnostics;
- world fingerprint, pixel SHA-256, two observer trace SHA-256 values and final report SHA-256;
- mechanically assigned claim level A–E.

No V7 value may be entered manually before the locked ledger exists.
