# Manuscript claim-to-evidence traceability ledger

This ledger is a writing control. It prevents the manuscript from upgrading development evidence, hiding locked failures, treating observer disagreement as truth, or describing proxy/real-pixel tests as biological field validation.

## Claim classes

| ID | Manuscript claim | Evidence | Status | Permitted wording | Forbidden upgrade |
|---|---|---|---|---|---|
| C1 | Biological-evidence and observability-risk observers answer non-equivalent scientific questions | V1–V2 + software contracts | development / architecture | “epistemically distinct observation programs” | “statistically independent failures” |
| C2 | Same-input contradictions persist on byte-identical pixels | V2 | development | “structured contradictions persisted under shared pixels” | “field validity” |
| C3 | Direct disagreement is not automatically an effective finite-budget acquisition priority | V3 | negative development | “did not outperform the strongest alternatives in the tested equal-budget screen” | “disagreement can never be useful” |
| C4 | Fixed scalar disagreement is not prevalence-robust | locked V5 | locked falsification | “V5 falsified the preregistered scalar-allocation claim” | “V5 falsified observer complementarity” |
| C5 | V6 changed policy class to protected exploration + separate quotas | V6 | development fact | report 50/10/40 as frozen development instance | call 50/10/40 optimal/universal |
| C6 | Protected exploration has sampling-safety guarantees independent of observer accuracy | analytical + tests | supported | TV contraction, support lower bound, importance bound, finite miss probability | infer event-performance superiority from theorem |
| C7 | Frozen 50/10/40 did not establish unseen-world superiority | locked V7 | **FAIL / C** | “V7 rejected general allocation-superiority claim” | “V7 confirmed V6” |
| C8 | Guarded 50/10/40 is robust relative to uniform in many abstract regimes but rarely regime-wise best | V8 | broad simulation | “794/864 uniform-or-better; 185/864 best same-alpha” | “generally optimal” |
| C9 | Protected random exploration preserves a design-valid inferential denominator | V9 + finite-population theory | supported | report bias/RMSE/coverage and SRSWOR interpretation | “all targeted data become unbiased” |
| C10 | Observability signal transfers only partially to real image texture | locked V10 | **C** | “family-specific real-pixel perturbation transfer” | biological-event/species accuracy |
| C11 | Static contradiction states do not provide transferable causal failure labels | locked V11 | **FAIL / D** | “V11 rejected static contradiction-state localisation” | “independent observers are useless” |
| C12 | Controlled interventions can restore conditional causal identifiability | locked V12 | **B** | “dual channels improved diagnostic efficiency under controlled interventions” | universal causal discovery / universal dual superiority |
| C13 | Separate response dimensions matter when scalar projection destroys intervention-response separation | generic theory/API | analytical + parity tests | null-space / signature-separation claim | “higher dimension is always better” |
| C14 | V13 is a blinded physical validation protocol | V13 | pre-field frozen | describe apparatus/split/blinding/freeze only | report performance before acquisition/unseal |
| C15 | Protected random audit is needed because agreement does not exclude shared blind spots | V9 + conceptual consequence of V11 | supported as design rationale | “random audit can sample regions not requested by either observer” | “audit proves observers are wrong” |
| C16 | The central contribution is contradiction-guided development, not a fixed allocator | generational evidence V3–V12 | synthesis | “contradiction generates tests; interventions identify causes; probability sampling protects inference” | “disagreement itself is the final algorithm” |
| C17 | No field biological-accuracy claim is established | study scope | fixed | state explicitly | pollinator detection probability, species accuracy, occupancy validity |

## Fixed numerical evidence

### V3 equal-budget screen

At 25% budget:

- uniform: event recall ≈ `0.251`, observer-relative hidden-error recall ≈ `0.251`;
- biological-candidate priority: event ≈ `0.325`, hidden error ≈ `0.100`;
- observability audit: event ≈ `0.189`, hidden error ≈ `0.251`;
- disagreement: event ≈ `0.188`, hidden error ≈ `0.251`.

Supports C3 only.

### V5 locked falsification

- PolliPi commit: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- InsePi commit: `980813bab996909020140fad5bd83b055eb3db9c`;
- world fingerprint: `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`;
- PolliPi trace SHA-256: `56ec4de0b710273ee47e500d6b1d7f92c50ba40274619528f857e133633385c0`;
- cross-report SHA-256: `a6d1f30b3d18707e83cb5d0d5f60581d06fdf42f7bbe485fb0992079f3ce495e`.

Permitted conclusion: fixed scalar disagreement was not prevalence-robust. Complementary signal remained; observer independence was not proven or rejected.

### V6 development candidate

Frozen allocator: `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`.

| Candidate | Gate | Worst joint | Mean joint | Max TV |
|---|---:|---:|---:|---:|
| U=.40 P=.10 I=.50 | fail | 1.00842 | 1.11598 | 0.26567 |
| **U=.50 P=.10 I=.40** | **pass** | **1.00846** | **1.11642** | **0.21919** |
| U=.60 P=.10 I=.30 | pass | 1.00832 | 1.10303 | 0.17222 |
| U=.70 P=.10 I=.20 | fail | 0.98329 | 1.08413 | 0.12907 |

Permitted conclusion: selected frozen development candidate, not universal optimum.

### V7 locked result

- gate: **FAIL**;
- claim: **C**;
- worst joint ratio: `0.9247839629`;
- mean joint ratio: `0.9509088103`;
- max TV: `0.202475`;
- report SHA-256: `20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae`.

Permitted conclusion: sampling distortion remained bounded but general frozen-allocation superiority failed.

### V8 generality map

- total regimes: `864`;
- 50U/10E/40O joint recovery at-or-above uniform: `794/864 = 91.9%`;
- best same-alpha policy: `185/864 = 21.4%`;
- strong failure boundary: event prevalence `0.90` and increasing observer residual correlation.

Permitted conclusion: broad robustness region, not regime-wise optimality.

### V9 design-based inference

Across `57,600` finite worlds:

- protected-exploration estimator mean bias ≈ `9.1e-7`;
- protected 95% coverage: `97.75%`;
- naive targeted-all-sample mean bias ≈ `+0.0426`;
- naive coverage ≈ `52.4%`;
- protected RMSE `0.04282`;
- theoretical finite-population SD `0.04237`;
- RMSE / theoretical SD ≈ `1.01`.

Permitted conclusion: the protected random subset functions as a design-valid inferential denominator under the simulated finite-population design.

### V10 locked real-pixel result

Manual one-shot run `32693453262`:

- claim: **C**, `partial_or_family_specific_transfer`;
- positive high-tier families: `4/6`;
- dose-monotone families: `5/6`;
- global high-tier median paired risk delta: `0.62718017578125`;
- V6 allocation cells at/above paired uniform: `54/54`;
- mean paired-uniform recall ratio: `1.309028695295118`;
- report SHA-256: `f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b`;
- evaluation receipt SHA-256: `52b25d57201a9b191d1cce1ecda7dae19dec2af8b4e4b2f36b26a9b5d0d560c7`;
- evidence artifact digest: `8767e17ba18db106c3794c20a2f36f6b79580c785fbe58ad40a40cde6399c193`.

Permitted conclusion: partial observation-process transfer on real pixels. Biological-event accuracy is explicitly untested.

### V11 locked failure localisation

Contradiction-guided static representation:

- claim: **D**;
- held-out localisation: `0.3469`;
- wrong-module intervention: `0.8707`;
- shared-blind-spot discovery: `0.2511`;
- repair-positive transfer: `0.1963`;
- result SHA-256: `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`.

Permitted conclusion: static contradiction-state meaning did not transfer across mechanism subtype shift.

### V12 controlled interventions

- claim: **B**, `conditional_causal_identification_advantage`;
- dual accuracy after 2 interventions: `0.9858`;
- early fusion after 2: `0.9658`;
- dual accuracy after 1: `0.9608`;
- early fusion after 1: `0.7367`;
- dual wrong-module rate: `0.0159`;
- early-fusion wrong-module rate: `0.0433`;
- dual stable interventions: `1.0108`;
- early fusion: `1.2614`;
- result SHA-256: `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`.

Permitted conclusion: distinct channels gave a strong first-intervention diagnostic-efficiency benefit and a smaller final two-intervention benefit; frozen A threshold was not met.

### V13 pre-field freeze

- scientific result: **none yet**;
- critical scientific/execution paths: `22`;
- execution digest: `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d`;
- development blocks: `108`;
- held-out blocks: `72`;
- held-out physical clusters: `6` actual date × scene clusters;
- exact observers: V5 commits above;
- all pre-field/freeze/exact-observer/full unit CI gates green at freeze.

Do not insert V13 performance values until the blinded prediction ledger is committed, held-out truth is unsealed, and the frozen evaluator emits A/B/C/D.

## Analytical claim boundary

For `Q = alpha U + (1-alpha)R`:

1. `TV(Q,U) = (1-alpha)TV(R,U)`;
2. `Q(A) >= alpha U(A)`;
3. `U(x)/Q(x) <= 1/alpha` on target support;
4. `D_infinity(U||Q) <= log(1/alpha)`.

For finite protected simple-random quota `q_U` from `N` windows and a family of size `m`:

`P(miss family) = C(N-m, q_U) / C(N, q_U)`.

Do not translate these sampling-safety results into claims of biological-performance superiority.

## Writing vocabulary

Prefer:

- “biological-evidence observer”;
- “observability-risk observer”;
- “epistemically distinct observation programs”;
- “contradiction-guided development”;
- “controlled intervention-response diagnosis”;
- “protected random audit” / “protected probability sample”;
- “locked falsification / locked validation”;
- “diagnostic efficiency”;
- “partial real-pixel observation-process transfer”.

Avoid:

- “independent failures”;
- “optimal 50/10/40”;
- “disagreement-driven final allocator”;
- “contradiction is the truth label”;
- “field-validated” for V10 or V12;
- “V13 result” before locked execution;
- “pollinator detection accuracy” without appropriate biological truth;
- any wording implying V12 upgraded beyond locked claim B.