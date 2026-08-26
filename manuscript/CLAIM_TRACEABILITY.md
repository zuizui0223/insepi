# Manuscript claim-to-evidence traceability ledger

This ledger is a writing control, not a new scientific analysis. It prevents the
manuscript from silently upgrading development evidence, changing the target of a
failed hypothesis, or describing an observer-relative metric as a world-intrinsic
quantity.

## Claim classes

| ID | Manuscript claim | Evidence generation | Evidence status | Permitted wording | Forbidden upgrade |
|---|---|---|---|---|---|
| C1 | PolliPi and InsePi express non-equivalent observation objectives and produce structured contradictions | V1 | development | “structured contradictions occurred under canonical scenarios” | “the observers fail independently” |
| C2 | Same-input contradictions persist after pixel rendering | V2 | development, byte-identical benchmark | “contradictions persist on identical rendered pixels” | “same-pixel results establish field validity” |
| C3 | Direct disagreement is not automatically the best finite-budget allocator | V3 | negative development result | “direct disagreement did not outperform the strongest alternatives in the initial equal-budget test” | “disagreement can never be useful for acquisition” |
| C4 | Gradient-based local-structure audit improves InsePi observability on the inspected V4 development benchmark | V4 | inspected development holdout | report exact V4 rates as development results | call V4 “untouched validation” |
| C5 | Fixed scalar disagreement is not prevalence-robust in the locked V5 test | V5 | one-shot locked falsification | “V5 falsified the preregistered prevalence-robust scalar-allocation claim” | “V5 falsified observer complementarity” |
| C6 | Complementary observer signals remained after the V5 scalar-allocation failure | V5 | locked descriptive result | “complementary signal was observed in 6–7 disturbance families per prevalence setting” | “observer independence was proven” |
| C7 | V6 changes policy class rather than retuning the failed scalar score | V6 | development design fact | “the allocation architecture changed from one ranking to independent quotas plus exploration” | imply V6 was preregistered before V5 |
| C8 | Focused V6 development selected U=.50/P=.10/I=.40/D=0 under the predefined lexicographic development rule | V6 | inspected high-resolution development | report candidate comparison and weak common-prevalence margin | call 50/10/40 universally optimal |
| C9 | The exploration mixture has exact distributional safety properties | analytical | theorem/algebra | state TV contraction, coverage lower bound and importance-ratio bound | infer event-recovery superiority from the theorem |
| C10 | Generic guarded-portfolio API reproduces the frozen V6 selector on representative parity tests | software verification | unit-test evidence | “exact selection parity was tested for the frozen development instance” | “all third-party score systems will behave equivalently” |
| C11 | V7 supports the final allocation claim | V7 | **unknown until one-shot execution** | `[[V7_LOCKED_RESULT]]` only before execution | any positive/negative V7 result before ledger exists |
| C12 | No field-accuracy claim is established | study scope | fixed | explicitly state simulation-only scope | infer ecological effect size or real visit-rate accuracy |

## Fixed numerical evidence

### V3 initial equal-budget screen

At 25% budget on the V2-derived world:

- uniform: event recall ≈ 0.251; observer-relative hidden-error recall ≈ 0.251;
- PolliPi candidate: event ≈ 0.325; hidden error ≈ 0.100;
- InsePi audit: event ≈ 0.189; hidden error ≈ 0.251;
- union: event ≈ 0.313; hidden error ≈ 0.084;
- intersection: event ≈ 0.284; hidden error ≈ 0.182;
- disagreement: event ≈ 0.188; hidden error ≈ 0.251.

These numbers support C3 only. They do not identify a final policy.

### V4 observability development

Inspected V4 test benchmark:

- clean false-risk rate: 0.00;
- overall disturbed-window risk recall: 0.875;
- occlusion: 0.75;
- clutter: 0.75;
- blur: 1.00;
- occlusion+blur: 1.00;
- wind / shadow / shake and tested broad mixed families: 1.00;
- lens OOD: 0.00.

V4 world fingerprint:
`10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`.

Because V4 informed feature development, these are development results only.

### V5 locked falsification

Frozen evidence supplied by the locked V5 run:

- PolliPi method: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- InsePi method: `980813bab996909020140fad5bd83b055eb3db9c`;
- world fingerprint: `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`;
- PolliPi trace SHA-256: `56ec4de0b710273ee47e500d6b1d7f92c50ba40274619528f857e133633385c0`;
- cross-report SHA-256: `a6d1f30b3d18707e83cb5d0d5f60581d06fdf42f7bbe485fb0992079f3ce495e`.

Design:

- 180 conditions;
- three prevalence regimes;
- three budget regimes;
- eight policies;
- 4,800 sampled windows per regime;
- 200 Monte Carlo replicates.

Locked interpretation:

- full fixed-disagreement gate passed only balanced prevalence / 25% budget;
- rare 10% and 25% were outside the Pareto frontier and lost to single-view removal;
- common 25% had higher hidden-error recall under InsePi-only;
- 10% budget could produce disturbance TV ≈ 0.833;
- complementary observer signals remained in roughly 6–7 disturbance families.

Permitted conclusion: **fixed scalar disagreement allocation was not prevalence
robust**. Do not broaden this to rejection of dual observers.

### V6 frozen development candidate

Frozen allocator implementation:
`a8ac75991ab28fd74a3f3a5482304a2b127a97bc`.

High-resolution paired V4-development design:

- 4,800 windows;
- 200 replicates;
- prevalence 0.10 / 0.50 / 0.90;
- budget 0.10 / 0.25 / 0.50.

Focused alternatives:

| Candidate | Development gate | Worst joint | Mean joint | Max TV | Interpretation |
|---|---:|---:|---:|---:|---|
| U=.40 P=.10 I=.50 D=0 | fail | 1.00842 | 1.11598 | 0.26567 | TV ceiling exceeded |
| **U=.50 P=.10 I=.40 D=0** | **pass** | **1.00846** | **1.11642** | **0.21919** | frozen candidate |
| U=.60 P=.10 I=.30 D=0 | pass | 1.00832 | 1.10303 | 0.17222 | safer TV, slightly lower lexicographic score |
| U=.70 P=.10 I=.20 D=0 | fail | 0.98329 | 1.08413 | 0.12907 | common-prevalence hidden-error failure |

The weakest frozen-candidate margin is common-prevalence event recovery, only
about 1.008–1.009 relative to uniform. This must be visible in text/figures.

## Analytical claim boundary

For `Q = αU + (1−α)R`:

1. `TV(Q,U) = (1−α)TV(R,U)`;
2. `Q(A) >= αU(A)` for every target-supported condition set A;
3. `U(x)/Q(x) <= 1/α` on the target support;
4. consequently `D_infinity(U||Q) <= log(1/α)`.

These statements concern the ideal mixture distribution. The finite quota
implementation has exact budget accounting and spillover-to-exploration but should
not be described as an exact i.i.d. draw from Q.

## V7 claim insertion rule

Before V7, manuscript files may contain only the placeholder:

`[[V7_LOCKED_RESULT]]`

After the one-shot run, insert values **only** from
`v7_execution_ledger.json` / `v7_report.json`:

- gate PASS/FAIL;
- claim level A–E;
- worst joint ratio;
- mean joint ratio;
- max TV;
- individual locked failures;
- arm-removal outcome;
- observer-independent coverage metrics;
- world fingerprint;
- PolliPi trace SHA-256;
- InsePi trace SHA-256;
- report SHA-256;
- frozen source/evaluator/materializer/orchestrator identifiers.

Do not rerun with changed weights, seed, families, thresholds or baselines under
label V7.

## Writing vocabulary

Prefer:

- “biological-evidence observer”;
- “observability-risk observer”;
- “observer-relative detection-error recall”;
- “contradiction-guided development”;
- “exploration-guarded portfolio”;
- “locked falsification / locked validation”;
- “architectural transferability”.

Avoid:

- “ground-truth observation error” when referring to PolliPi-relative hidden error;
- “independent failures”;
- “optimal 50/10/40 allocation”;
- “field-validated”;
- “disagreement-driven allocation” for the final V6 method;
- “V7 confirms” before the immutable report exists.
