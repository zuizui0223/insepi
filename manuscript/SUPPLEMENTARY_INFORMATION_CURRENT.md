# Supplementary Information

## Contradiction-guided development of ecological sensing: independent observers, controlled interventions, and protected random audit

This Supplementary Information is organised by scientific generation. Development datasets are labelled as development evidence even when they contain internal test splits. Locked generations retain their original claim ceilings and are not retrospectively upgraded by later results.

---

## Appendix S1. Observation-program contracts

### S1.1 Biological-evidence observer

The biological-evidence program evaluates whether local image change provides evidence for a candidate biological event. Its visual states include:

- `no_activity`;
- `environmental_noise`;
- `uncertain_local_activity`;
- `strong_visitation_candidate`.

The observer is not a calibrated estimate of true visit probability. In cross-observer methodology it provides an event-evidence axis.

### S1.2 Observability-risk observer

The observability program evaluates the reliability of the observation process. Its decision model includes false-event, missed-event and attribution risks and can emit states including clean, confounded, audit-priority and unobservable.

The observer is not a species classifier and does not estimate the same latent quantity as the biological-evidence observer.

### S1.3 Independence contract

The two programs remain independently executable. Neither imports the other's decision logic. Shared material is restricted to world contracts, canonical pixels and emitted traces. Cross-observer comparison occurs after independent inference.

This software separation does **not** imply statistical independence of observer errors.

### S1.4 Protected random audit

The protected random component is not a third classifier. It is a probability-sampling lane used for:

1. observing conditions not requested by either targeted observer;
2. auditing possible shared blind spots;
3. preserving a probability-sample subset for ecological inference.

---

## Appendix S2. Generational evidence ledger

| Generation | Scientific question | Evidence status | Main outcome |
|---|---|---|---|
| V1 | Do distinct observation objectives produce structured contradictions? | development | yes, under canonical scenarios |
| V2 | Do contradictions persist on byte-identical rendered pixels? | development | yes |
| V3 | Is direct disagreement a strong equal-budget acquisition rule? | development negative | no |
| V4 | Can observability diagnosis improve without merging observers? | inspected development | yes for several disturbance families; retained failures remain |
| V5 | Is fixed scalar disagreement allocation robust to prevalence shift? | locked falsification | no |
| V6 | Can protected exploration plus separate quotas repair the allocation architecture? | development | frozen 50U/10E/40O candidate |
| V7 | Does the frozen V6 instance generalise on an unseen locked world? | locked | FAIL / C |
| V8 | Across what abstract regimes is guarded allocation robust or adverse? | broad development/generality benchmark | 794/864 at-or-above uniform; 185/864 regime-wise best |
| V9 | Does protected random exploration preserve finite-population inference? | frozen simulation design | yes |
| V10 | Does observation-risk response transfer to real image texture? | locked real-pixel one-shot | partial / C |
| V11 | Do static contradiction states localise causal failure across subtype shift? | locked | FAIL / D |
| V12 | Do controlled interventions restore causal identifiability? | locked | conditional support / B |
| V13 | Do intervention-response signatures transfer in a blinded physical same-stream design? | pre-field frozen | result pending |

The sequence is intentionally asymmetric: later generations are allowed to change the experimental question or policy class, but not to rewrite the scientific outcome of an earlier locked generation.

---

## Appendix S3. V2–V4 development evidence

### S3.1 Portable V2 visual contract

The portable V2 renderer produces byte-identical grayscale `uint8` 96×128 images in both repositories. The shared suite fingerprint is:

`f281fedd7ebf899dbc472b73b21afd25a30f18bb5481af71ec65b13f63a80ec8`.

Canonical conditions included clean event/absence, wind, shake, shadow, occlusion, blur, clutter and an unknown condition.

The V2 state matrix established that observer agreement and disagreement are structured by the scientific objective. It was not used as field validation.

### S3.2 V3 equal-budget policy screen

At a 25% budget on 2,400-window worlds with 100 replicates:

| Policy | Event recall | Observer-relative hidden-error recall | Disturbance TV |
|---|---:|---:|---:|
| uniform | 0.251 | 0.251 | 0.022 |
| biological candidate | 0.325 | 0.100 | 0.301 |
| observability audit | 0.189 | 0.251 | 0.667 |
| union | 0.313 | 0.084 | 0.261 |
| intersection | 0.284 | 0.182 | 0.251 |
| disagreement | 0.188 | 0.251 | 0.500 |

The initial strong claim that direct disagreement should dominate acquisition was therefore rejected.

### S3.3 V4 factorial development benchmark

V4 used 120 factorial conditions with calibration and inspected test subsets. The world fingerprint is:

`10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`.

For the observability observer on the inspected test subset:

- clean false-risk rate: `0.00`;
- overall disturbance-risk recall: `0.875`;
- blur: `1.00`;
- occlusion: `0.75`;
- clutter: `0.75`;
- occlusion+blur: `1.00`;
- wind / shadow / shake and tested broad mixed families: `1.00`;
- lens OOD: `0.00`.

Because V4 informed later observer development, these remain development results.

---

## Appendix S4. V5 locked scalar-allocation falsification

### S4.1 Frozen provenance

Exact observer commits:

- biological-evidence observer: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- observability-risk observer: `980813bab996909020140fad5bd83b055eb3db9c`.

Locked world fingerprint:

`9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`.

Biological-observer trace SHA-256:

`56ec4de0b710273ee47e500d6b1d7f92c50ba40274619528f857e133633385c0`.

Cross-report SHA-256:

`a6d1f30b3d18707e83cb5d0d5f60581d06fdf42f7bbe485fb0992079f3ce495e`.

### S4.2 Design

- 180 conditions;
- event prevalences 0.10 / 0.50 / 0.90;
- budgets 0.10 / 0.25 / 0.50;
- eight policies;
- 4,800 windows per world;
- 200 paired replicates.

### S4.3 Locked interpretation

The complete fixed-disagreement gate passed only in a limited balanced-prevalence / 25% budget setting. Rare-event low/mid budgets fell outside the Pareto frontier and common-prevalence regimes could favour single-observer alternatives. Low-budget disturbance-family concentration could reach TV around 0.833.

Complementary observer signal nevertheless remained across roughly six to seven disturbance families per prevalence setting. The falsified hypothesis is therefore:

> independent-observer disagreement collapsed into one fixed scalar allocation ranking is prevalence-robust.

The result does not falsify the existence of complementary observer information.

---

## Appendix S5. V6 development architecture and V7 locked challenge

### S5.1 V6 policy-class change

V6 replaced one scalar ranking with exact-budget quotas:

1. protected uniform exploration;
2. biological-evidence targeting;
3. observability-risk targeting;
4. optional structured disagreement targeting.

Unused targeted quota returns to uniform exploration rather than another targeted arm.

Focused development candidates:

| Candidate | Development gate | Worst joint | Mean joint | Max TV |
|---|---:|---:|---:|---:|
| U=.40 E=.10 O=.50 D=0 | fail | 1.00842 | 1.11598 | 0.26567 |
| **U=.50 E=.10 O=.40 D=0** | **pass** | **1.00846** | **1.11642** | **0.21919** |
| U=.60 E=.10 O=.30 D=0 | pass | 1.00832 | 1.10303 | 0.17222 |
| U=.70 E=.10 O=.20 D=0 | fail | 0.98329 | 1.08413 | 0.12907 |

The U=.50/E=.10/O=.40 instance was frozen as the development candidate. It is not described as optimal.

### S5.2 Sampling-safety theory

For `Q = alpha U + (1-alpha)R`:

- `TV(Q,U) = (1-alpha)TV(R,U) <= 1-alpha`;
- `Q(A) >= alpha U(A)`;
- `U(x)/Q(x) <= 1/alpha` on target support;
- `D_infinity(U||Q) <= log(1/alpha)`.

For a finite population of `N` windows, protected simple-random quota `q_U` and condition family of size `m`:

`P(miss family) = C(N-m,q_U) / C(N,q_U)`.

These are sampling-safety properties, not biological-performance claims.

### S5.3 V7 locked result

V7 used a new locked world and the exact frozen V5 observer commits.

Result:

- gate: **FAIL**;
- claim level: **C**;
- worst joint ratio: `0.9247839629`;
- mean joint ratio: `0.9509088103`;
- max disturbance-family TV: `0.202475`;
- report SHA-256: `20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae`.

V7 therefore rejected general unseen-world superiority of the frozen 50/10/40 instance while retaining its explicit protected-exploration sampling architecture.

---

## Appendix S6. V8 abstract generality benchmark

V8 varied:

- event prevalence;
- sensing budget;
- biological-observer quality;
- observability-observer quality;
- residual observer correlation;
- disturbance prevalence.

The preregistered grid contained 864 regimes. Same-alpha comparators separated the effect of 50% protected exploration from the effect of maintaining separate observer-targeting quotas.

Key results:

- 50U/10E/40O achieved joint event/error recovery at-or-above uniform in `794/864 = 91.9%` of regimes;
- it was the best same-alpha policy in only `185/864 = 21.4%`;
- all tested regimes at prevalence 0.02, 0.10 and 0.50 met the uniform-or-better joint criterion;
- only 67.6% did so at prevalence 0.90;
- favourable-regime frequency declined as residual observer correlation increased.

The result supports a broad robustness region and explicit failure regions, not regime-wise optimality.

Canonical V8 result SHA-256:

`5a6a828c5a48b8b1d73a466c4f933f5934dc7d9dc4c178d5867564720dbdeefe`.

---

## Appendix S7. V9 finite-population inference

V9 compared:

1. a naive prevalence estimate obtained by treating the full adaptively targeted sample as representative;
2. a design-based prevalence estimate using only the protected simple-random subset.

Across 57,600 finite worlds:

| Quantity | Protected random subset | Naive full targeted sample |
|---|---:|---:|
| Mean bias | ~`9.1e-7` | ~`+0.0426` |
| 95% coverage | `97.75%` | ~`52.4%` |
| RMSE | `0.04282` | — |
| Finite-population theoretical SD | `0.04237` | — |

The protected RMSE/theoretical-SD ratio was approximately `1.01`.

This result motivates the phrase **protected random audit**: the probability-sampling lane is both an audit channel for shared blind spots and a reference denominator for ecological inference.

---

## Appendix S8. V10 locked real-pixel perturbation transfer

### S8.1 Scope

V10 used seven byte-frozen real honeybee evaluation videos. Deposited Experiment 1 files did not provide independent human frame-level biological-event truth suitable for the locked benchmark. Therefore V10 tested **known observation-process perturbation transfer**, not pollinator-detection accuracy.

The real-pixel artifact contained:

- 364 native one-second windows;
- 19 variants per window;
- 6,916 total conditions;
- perturbation families: shadow, occlusion, blur, sensor banding, glare and framing drift;
- three fixed intensity tiers.

Pixel artifact SHA-256:

`b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66`.

### S8.2 One-shot result

Manual locked run: `32693453262`.

- claim level: **C** (`partial_or_family_specific_transfer`);
- positive high-tier families: `4/6`;
- dose-monotone families: `5/6`;
- global high-tier median paired risk delta: `0.62718017578125`;
- frozen V6 allocation cells at-or-above paired uniform: `54/54`;
- mean paired-uniform disturbance-recall ratio: `1.309028695295118`.

Report SHA-256:

`f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b`.

Evaluation receipt SHA-256:

`52b25d57201a9b191d1cce1ecda7dae19dec2af8b4e4b2f36b26a9b5d0d560c7`.

Immutable evidence artifact digest:

`8767e17ba18db106c3794c20a2f36f6b79580c785fbe58ad40a40cde6399c193`.

The stronger transfer claim was not met because fewer than five families had positive high-tier paired risk response.

---

## Appendix S9. V11 locked static contradiction-state localisation

V11 compared failure-localisation strategies under development-to-heldout mechanism-subtype shift. The contradiction-guided representation combined separate observer values with thresholded high/low states and protected-audit information.

Locked outcome:

- claim level: **D**;
- held-out contradiction-guided localisation: `0.3469`;
- wrong-module intervention rate: `0.8707`;
- shared-blind-spot discovery: `0.2511`;
- repair-positive transfer: `0.1963`;
- result SHA-256: `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`.

The dominant failure was true fault → `no_fault` collapse. The meaning of the low-evidence/low-risk state also shifted strongly between development and held-out mechanism subtypes.

V11 therefore rejected a stable static contradiction taxonomy as a general causal localiser.

---

## Appendix S10. V12 controlled causal-intervention diagnosis

V12 changed the experiment instead of retuning V11. All representations used the same intervention candidates, intervention budget and nearest-centroid/maximin diagnostic algorithm. They differed only in the response representation.

Representations:

- event-only;
- observability-only;
- early scalar fusion;
- dual `(delta evidence, delta observability)` vector.

Locked result:

| Representation | Accuracy after 1 intervention | Accuracy after 2 | Wrong-module rate | Mean interventions to stable diagnosis |
|---|---:|---:|---:|---:|
| dual | **0.9608** | **0.9858** | **0.0159** | **1.0108** |
| early scalar fusion | 0.7367 | 0.9658 | 0.0433 | 1.2614 |
| event-only | 0.7653 | 0.8767 | 0.0885 | 1.5328 |
| observability-only | 0.7794 | 0.8772 | 0.0867 | 1.5108 |

Canonical result SHA-256:

`7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`.

Claim level: **B**, `conditional_causal_identification_advantage`.

The strongest distinct-channel effect occurred after the first intervention. The final two-intervention advantage over early fusion was only about 0.02 and did not satisfy the stronger frozen A threshold.

Protected audit was not the sole explanation: unaudited dual episodes retained approximately 0.983 accuracy.

---

## Appendix S11. Generic causal-diagnostic API and identifiability condition

The V12 diagnostic logic was extracted into an observer-agnostic API implementing:

1. response-signature fitting by failure hypothesis and intervention;
2. maximin first-intervention selection;
3. nearest-competing-hypothesis identification;
4. second-intervention selection to maximise separation of remaining hypotheses;
5. nearest-centroid diagnosis in the observed response space.

Exact parity tests reproduce V12 dual-channel centroids, intervention order and predictions.

A scalar projection can destroy identifiability. If response-vector differences between two hypotheses lie in the null space of a chosen projection, the projected responses become identical even when the original channel vectors remain distinct. Separate channels therefore help only when controlled interventions create diagnostically relevant response geometry that the projection would remove.

---

## Appendix S12. V13 blinded physical same-stream protocol

V13 contains no scientific result at the time of this SI.

### S12.1 Experimental units and split

- development: `3 days × 3 scenes × 4 classes × 3 replicates = 108 blocks`;
- held-out: `2 new days × 3 new scenes × 4 classes × 3 replicates = 72 blocks`;
- total: `180 blocks`;
- four 10-s phase clips per block: `720 clips` total;
- frames within a block are repeated measurements, not independent replicates.

Final uncertainty uses the actual completed-capture `recording_date_local × physical_scene_code` cluster. Development and held-out dates/scenes must be disjoint. Every day×scene cluster contains exactly 12 blocks: three replicates for each of four treatment classes.

### S12.2 Physical treatment classes

- event-side;
- nuisance-side;
- shared optical;
- no-fault matched control.

Development and held-out subtypes differ.

Frozen apparatus includes:

- standard event proxy: 100±2 mm matte circular disk at camera distance 1000±20 mm;
- development event-side contrast: 0.20–0.30 × standard target/carrier luminance contrast;
- held-out event-side: 50±2 mm target-scale shift;
- development nuisance: fan-driven background at 1.5±0.2 m/s;
- held-out nuisance: moving shadow 0.50±0.05 Hz with trough illuminance 0.60±0.10 × unshadowed;
- development shared optical: partial occlusion covering 0.30±0.03 of canonical frame width;
- held-out shared optical: full-aperture diffuser with transmittance 0.70±0.10.

Apparatus measurements are made without access to observer output.

### S12.3 Non-cumulative intervention battery

Every block records placebo first and all three active interventions:

- `event_restore`;
- `observability_restore`;
- `shared_restore`.

The active order is private-salt randomised. After each active phase, the latent placebo treatment state must be restored during washout. Active interventions are not cumulative.

### S12.4 Measurement path

Each 10-s 30-fps phase retains native frame indices:

`75, 105, 135, 165, 195, 225, 255, 285`.

Frames are deterministically canonicalised to 96×128 grayscale using the V10 mapping. The block background is the exact pixel-wise median of the eight placebo frames only. The same background is supplied to both frozen observers for all phases of the block.

Primary scalar mappings:

- evidence: `strong_visitation_candidate=1.0`, `uncertain_local_activity=0.7`, other biological states `0`;
- observability risk: maximum of false-event, missed-event and attribution risks.

Phase response is the median of eight sample scores. Each active causal response is active-phase median minus the common placebo median.

### S12.5 Blinding and freeze

- private salt and latent treatment ledger remain outside observer/prediction environment;
- only development labels enter model fitting;
- held-out treatment truth remains sealed until predictions are emitted and SHA-committed;
- 25% protected physical-QC blocks are selected before acquisition;
- QC annotators do not see observer output or predicted classes;
- treatment compliance cannot be redefined after observer output.

Scientific execution freeze:

- critical paths: `22`;
- digest SHA-256: `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d`.

At freeze, V13 pre-field, execution-freeze, exact-observer-smoke and full Python 3.10/3.11 CI gates were green.

### S12.6 Claim ceiling

V13 will receive A/B/C/D from the frozen evaluator. No result may be inserted before blinded prediction commitment and held-out truth unseal. An unfavourable outcome is retained without retuning under label V13.

---

## Appendix S13. Reproducibility ledger

| Evidence | Identifier |
|---|---|
| V2 portable visual fingerprint | `f281fedd7ebf899dbc472b73b21afd25a30f18bb5481af71ec65b13f63a80ec8` |
| V4 world fingerprint | `10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193` |
| V5 world fingerprint | `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5` |
| V7 report | `20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae` |
| V8 canonical result | `5a6a828c5a48b8b1d73a466c4f933f5934dc7d9dc4c178d5867564720dbdeefe` |
| V10 real-pixel artifact | `b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66` |
| V10 report | `f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b` |
| V10 immutable evidence artifact | `8767e17ba18db106c3794c20a2f36f6b79580c785fbe58ad40a40cde6399c193` |
| V11 result | `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1` |
| V12 result | `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222` |
| V13 pre-field execution digest | `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d` |

Exact 40-character Git commit identifiers are retained in the canonical repositories and automatically pseudonymised in the double-anonymous review bundle. Scientific 64-character evidence fingerprints are retained for reviewer audit.

---

## Appendix S14. Claims explicitly outside the present evidence

The current evidence does not establish:

- natural pollinator-detection probability;
- species-identification accuracy;
- occupancy or abundance validity;
- universal superiority of dual observers;
- statistically independent observer failures;
- universal optimality of a 50/10/40 allocation;
- causal discovery without controlled intervention assumptions;
- physical V13 transfer before its locked evaluation exists.
