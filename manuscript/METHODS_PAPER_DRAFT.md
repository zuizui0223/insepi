# Contradiction-guided development of ecological sensing: independent observers, controlled interventions, and protected random audit

**Target journal:** Methods in Ecology and Evolution  
**Status:** current working manuscript through V12; V13 physical validation is frozen but not yet executed.  
**Claim boundary:** no field biological-event accuracy, species-identification, occupancy, or universal observer-superiority claim.

## Abstract

1. Adaptive ecological sensors can conserve storage, power and human review by preferentially retaining observations that appear informative. However, biological-event evidence and the reliability of the observation process are different scientific quantities, and preferential acquisition can distort the sample from which ecological absence, prevalence and error are inferred. We asked whether keeping these observation hypotheses separate could make adaptive sensing easier to falsify, diagnose and audit.

2. We developed two independently executable observation programs on the same visual stream: a biological-evidence observer and an observability-risk observer. We organised development into frozen generations in which disagreement-based allocation, guarded sampling, failure localisation and causal diagnosis were each allowed to fail without being silently retuned. A protected probability-sampling component was analysed theoretically and by finite-population simulation. We then tested observer transfer on byte-frozen real image texture and compared static contradiction states with controlled intervention-response diagnosis.

3. Direct disagreement was not a robust acquisition priority, and a locked unseen-world validation rejected general superiority of a frozen 50% uniform / 10% biological-evidence / 40% observability-risk portfolio (worst joint ratio 0.925; mean 0.951 relative to uniform). Nevertheless, abstract generality tests showed this guarded portfolio was at least as good as uniform for joint event/error recovery in 794/864 regimes, while being regime-wise best in only 185/864. Protected random exploration produced essentially unbiased finite-population prevalence estimates and near-nominal interval coverage, whereas treating the targeted sample as representative produced positive bias and severe undercoverage. Real-pixel validation supported only partial disturbance-risk transfer (claim C). A static contradiction-state localiser failed on held-out mechanism subtypes (claim D), but controlled interventions restored causal identifiability: after one intervention, the dual-channel representation reached 0.961 localisation accuracy versus 0.737 after early scalar fusion; after two interventions the corresponding accuracies were 0.986 and 0.966 (claim B).

4. The methodological contribution is therefore not a winning allocation vector or a universal disagreement score. It is a falsifiable development protocol: preserve observation programs with different scientific purposes long enough to expose contradictions; use contradictions to formulate competing failure hypotheses rather than as truth; choose controlled interventions that separate those hypotheses; and retain protected random audit because observer agreement cannot exclude shared blind spots and because probability sampling preserves an inferential denominator. A blinded same-stream physical intervention generation is preregistered as the next external validation step.

**Keywords:** adaptive sampling; ecological monitoring; observability; preferential sampling; causal diagnosis; differential testing; active learning; camera traps; reproducibility; falsification

---

## 1. Introduction

Autonomous ecological sensors observe biological processes through an observation process. A camera does not record visitation truth directly: wind, illumination, camera motion, blur, occlusion, clutter and optical contamination can all change whether an event is visible, whether apparent motion is biological and whether absence is interpretable. The same distinction occurs in acoustic monitoring, where wind, overlap and recorder saturation affect what can be concluded from a recording independently of whether target evidence is present.

Resource constraints create pressure to make this observation process adaptive. A device may preferentially retain windows that look biologically interesting, send only high-priority clips for review, or allocate additional measurements where a detector is uncertain. Such decisions can improve efficiency, but they also determine which observation conditions enter the scientific record. This makes adaptive ecological sensing a sampling-design problem as well as a classification problem. Preferential sampling is already known to bias ecological inference when the observation process depends on the system or conditions under study (Diggle, Menezes & Su, 2010; Conn, Thorson & Johnson, 2017), and adaptive ecological sampling raises related challenges for representativeness and downstream inference (Henrys, Mondain-Monval & Jarvis, 2024).

A common engineering response is to create a single confidence score. Yet two questions can be scientifically distinct even when computed from the same pixels: *is there biological evidence worth preserving?* and *is the observation process trustworthy enough to interpret presence, absence or attribution?* A target detector and an observability diagnostic need not approximate the same latent label. Their disagreement may therefore be expected rather than erroneous.

This distinction separates our problem from conventional ensemble learning. Query by Committee selects observations because multiple predictors of the same target disagree (Seung, Opper & Sompolinsky, 1992). N-version programming uses independently developed implementations intended to satisfy a common specification and often relies on voting or agreement (Avizienis, 1985). Differential testing instead treats divergent outputs as evidence that some assumption or implementation should be investigated (McKeeman, 1998). Our setting is closest to the last analogy, but with an additional complication: the programs intentionally answer different scientific questions.

We therefore began with a deliberately falsifiable idea: preserving epistemically distinct observation programs might reveal failures that early fusion would hide. Importantly, this does not imply that disagreement itself should drive acquisition. Our development programme was designed so that disagreement-based allocation could fail while the broader independent-observer architecture remained testable.

The resulting study changed direction several times under locked negative evidence. A direct disagreement allocation rule failed. A fixed scalar disagreement ranking failed under prevalence shift. A later exploration-guarded portfolio performed well in development but failed a second locked unseen-world performance gate. A static contradiction-state representation then failed to localise causal failure on held-out mechanism subtypes. Only after changing the *experiment*—from passive classification of contradiction states to controlled interventions on candidate causal pathways—did separate observer responses provide a clear diagnostic-efficiency advantage.

This sequence motivates the present question:

> Can ecological observation systems be developed more reliably by keeping scientifically distinct observation hypotheses separate, using contradiction to choose falsifying interventions, and retaining probability-sample audit to protect against shared blind spots and preferential-sampling bias?

We evaluate that question in four parts. First, we preserve and report the failed acquisition hypotheses. Second, we characterise the sampling-safety role of protected random exploration theoretically and over broad abstract regimes. Third, we test whether contradiction states themselves identify failure causes. Fourth, we replace static contradiction classification with controlled intervention-response diagnosis and preregister a blinded physical same-stream validation.

---

## 2. Materials and Methods

### 2.1. Two epistemically distinct observation programs

We developed two edge-oriented observation programs with different scientific roles. The biological-evidence observer (PolliPi) estimates whether local image change provides evidence for a visitation candidate. Its visual pipeline produces states including `no_activity`, `environmental_noise`, `uncertain_local_activity` and `strong_visitation_candidate`.

The observability observer (InsePi) characterises the observation process rather than the biological target. It represents false-event, missed-event and attribution risks under disturbances such as camera motion, vegetation motion, illumination or shadow change, occlusion, blur, clutter and optical degradation. Its outputs include clean, confounded, audit-priority and unobservable states.

The programs were kept independently executable. Neither imported the other's decision logic. Shared material was restricted to world contracts, canonical pixels and emitted traces. We do not assume statistically independent errors, equal calibration or a latent consensus label that both programs should approximate.

### 2.2. Same-input / independent-decision contract

When the two programs were compared, they received the same canonical image bytes but emitted decisions independently. Hidden biological and disturbance labels were not provided during observer inference. Cross-program comparison occurred only after both traces existed. Relevant source commits, pixel artifacts, evaluator versions and output hashes were frozen or recorded by generation.

This contract is essential to the interpretation of contradiction. A disagreement can indicate an expected difference between scientific objectives, a failure of one observer, a failure of both, or a mismatch between the experimental manipulation and the observer representation. It is therefore diagnostic evidence, not a truth label.

### 2.3. Generational falsification design

Development was divided into named generations so that a dataset inspected to diagnose one hypothesis could not later be described as untouched validation of another.

| Generation | Main question | Locked outcome / role |
|---|---|---|
| V1–V2 | Do distinct observers produce structured contradictions on shared conditions/pixels? | Development: yes |
| V3 | Does direct disagreement improve equal-budget acquisition? | Negative development result |
| V4 | Can observability be improved without merging observers? | Development; test split inspected |
| V5 | Is fixed scalar disagreement robust to prevalence shift? | Locked failure |
| V6 | Can protected exploration + separate quotas repair allocation? | Development candidate 50/10/40 |
| V7 | Does frozen V6 generalise to a new locked world? | Locked FAIL / claim C |
| V8 | Where does guarded dual-observer allocation work or fail abstractly? | 864-regime generality map |
| V9 | Can protected exploration preserve ecological inference? | 57,600 finite-world design-based test |
| V10 | Do observation-risk signals transfer to real image texture? | Locked partial transfer / claim C |
| V11 | Do static contradiction states localise causal failure? | Locked FAIL / claim D |
| V12 | Do controlled interventions restore causal identifiability? | Locked conditional support / claim B |
| V13 | Does intervention-response diagnosis transfer physically across new days/scenes? | Pre-field frozen; result pending |

Locked failure reduced the claim ceiling but did not trigger tuning under the same generation.

### 2.4. Early disagreement and scalar-allocation tests

V3 compared equal-budget policies including uniform selection, biological-candidate priority, observability-audit priority, logical union/intersection and direct disagreement priority. This was an early falsification screen.

V5 then tested a stronger claim under a one-shot locked protocol: that a fixed scalar ranking derived from independent-observer disagreement would remain robust under event-prevalence shift. The benchmark contained 180 conditions, three prevalence regimes, three budget regimes, eight policies, 4,800-window worlds and 200 paired replicates. The tested claim concerned the scalar allocation rule, not whether the observers contained complementary information.

### 2.5. V6 exploration-guarded portfolio

After V5, we changed policy class rather than retuning the failed scalar score. An exact budget was partitioned into a protected uniform component and independent observer-specific targeting quotas. Targeted arms ranked observations independently; unused targeted quota returned to uniform exploration rather than being reallocated to another targeted signal.

A focused development sweep retained the instance

```text
50% protected uniform exploration
10% biological-evidence targeting
40% observability-risk targeting
 0% direct-disagreement targeting
```

because it passed all nine inspected prevalence × budget development cells under the prespecified development rule. These weights were frozen as a test instance, not presented as universal defaults.

### 2.6. Sampling-safety theory

Let `U` be the target non-preferential sampling distribution, `R` an arbitrary targeted distribution and `alpha` the protected exploration share. For

\[
Q = \alpha U + (1-\alpha)R,
\]

we use the exact identity

\[
TV(Q,U) = (1-\alpha)TV(R,U) \le 1-\alpha,
\]

and the support/importance bounds

\[
Q(A) \ge \alpha U(A), \qquad \frac{U(x)}{Q(x)} \le \frac{1}{\alpha}
\]

on target support. The latter also implies `D_infinity(U||Q) <= log(1/alpha)`.

For a finite population of `N` windows with a protected simple-random quota `q_U`, every window has at least the inclusion opportunity induced by that random component. For a condition family of size `m`, the probability that protected exploration misses the family entirely is

\[
P(\mathrm{miss}) = \frac{\binom{N-m}{q_U}}{\binom{N}{q_U}}.
\]

These are sampling-design statements; they make no assumption that either observer is accurate.

### 2.7. V7 locked unseen-world validation

V7 froze observer commits, allocator, world generator, comparator registry, metrics, hard gate and claim ceiling before final materialisation. The frozen 50/10/40 portfolio passed the strong claim only if every prevalence × budget cell had joint event/error recovery ratio at least 0.98 relative to uniform, the mean joint ratio exceeded 1, maximum disturbance-family TV did not exceed 0.25, and additional ablation/provenance rules passed.

The final world contained 15 disturbance families × three intensity tiers × two replicate slots × event absence/presence, including OOD sensor banding, glare and framing drift.

### 2.8. V8 abstract generality benchmark

To separate allocation architecture from one image renderer, V8 generated abstract worlds in which event prevalence, sensing budget, biological-observer quality, observability-observer quality, residual error correlation and disturbance prevalence were varied independently. The full grid contained 864 regimes. Six policies were evaluated on paired worlds, with same-`alpha` comparators used to separate the effect of protected exploration from the effect of preserving separate observer quotas.

V8 also measured prevalence-estimation bias from the full targeted sample versus the protected exploration subset.

### 2.9. V9 design-based inference benchmark

V9 treated the protected exploration subset explicitly as a simple random sample without replacement from a finite population. Across 57,600 worlds we compared the naive estimator obtained by treating all targeted observations as representative with a design-based prevalence estimator using only protected exploration.

We evaluated bias, RMSE, exact finite-population interval coverage and agreement between empirical RMSE and the finite-population theoretical standard deviation. The scientific goal was not to make targeted samples unbiased, but to test whether a protected probability sample could preserve a valid inferential denominator within an adaptive sensing workflow.

### 2.10. V10 locked real-pixel perturbation transfer

V10 tested observation-process transfer on seven byte-frozen real honeybee evaluation videos. Human frame-level biological-event truth was not available in the deposited experiment files; therefore V10 did not evaluate pollinator-detection accuracy. Instead, known image perturbations were applied to real image texture.

The frozen artifact contained 364 native one-second windows and 19 variants per window (native plus six perturbation families × three intensity tiers), for 6,916 real-pixel conditions. Families were shadow, occlusion, blur, sensor banding, glare and framing drift. Exact frozen observers were run independently on the same artifact. A trace-only evaluator assessed dose response and finite-budget allocation transfer under 18 balanced panels, three budgets and 200 paired replicates.

### 2.11. V11 static contradiction-state localisation

V11 asked whether disagreement patterns could localise which scientific module had failed. Four causal classes were simulated: event-side failure, observability-side failure, shared-representation failure and no fault. Development and held-out sets used different mechanism subtypes.

The contradiction-guided representation contained separate evidence/risk channels plus high/low diagnostic states and a protected audit indicator, and was evaluated with the same fixed nearest-centroid framework used for comparison. The purpose was to test whether static contradiction states themselves carried transferable causal meaning.

### 2.12. V12 controlled causal interventions

V12 changed the experiment rather than retuning the failed V11 representation. Candidate causal pathways were actively intervened on, and diagnosis used paired response relative to placebo.

Each failure hypothesis `h` and intervention `j` is represented by an intervention-response vector

\[
r_{h,j} = (\Delta E, \Delta O),
\]

where `Delta E` is change in biological-evidence response and `Delta O` is change in observability response. All representations used the same training episodes, intervention candidates, intervention budget and nearest-centroid/maximin diagnostic algorithm. The only difference was the representation: event-only, observability-only, early scalar fusion, or the separate two-channel vector.

The first intervention was chosen to maximise separation among candidate hypothesis centroids. After observing that response, the nearest competing hypotheses were retained and the next intervention was chosen to maximise their separation. The held-out diagnostic budget was two interventions. Protected audit could restrict fault versus no-fault possibilities but never supplied the causal module label.

### 2.13. Generic causal-diagnostic API and identifiability boundary

The V12 diagnostic logic was extracted into an observer-agnostic API accepting arbitrary failure hypotheses, intervention names and finite-dimensional response vectors. Exact parity tests reproduce the V12 dual-channel centroids, intervention order and diagnoses.

The core information boundary is representation-specific. If two failure hypotheses have intervention-response vectors whose difference lies in the null space of a scalar projection, they become indistinguishable after that fusion even though they remain separable in the original channel space. Additional controlled interventions can restore separation only if at least one measured response dimension differs under those interventions.

### 2.14. V13 blinded physical intervention protocol

V13 is the preregistered physical validation generation and has not yet produced scientific results. The experimental unit is one physical block, not one frame. Development uses 3 actual days × 3 actual scenes × 4 latent treatment classes × 3 replicates = 108 blocks. Held-out validation uses 2 new days × 3 new scenes × 4 classes × 3 replicates = 72 blocks.

Each block records a placebo and three non-cumulative controlled interventions: `event_restore`, `observability_restore` and `shared_restore`. All three are physically collected in private-salt random order, but the primary held-out analysis replays only the two interventions selected by the frozen generic diagnostic API. Final uncertainty uses the completed capture log's actual `recording_date_local × physical_scene_code` clusters; synthetic planning slots are forbidden for final cluster inference.

Held-out treatment truth remains sealed until a prediction ledger is emitted and SHA-committed. Protected physical-QC blocks are selected before acquisition and annotated without access to observer outputs or predicted classes. Any change to the frozen scientific execution path after acquisition begins requires a new generation label.

---

## 3. Results

### 3.1. Independent objectives produced structured contradictions

The two programs generated reproducible complementary states rather than random disagreement. Clean visits could produce strong biological evidence under low observation risk, whereas broad motion or illumination disturbance could suppress biological evidence while raising audit risk. Occlusion and blur exposed cases in which apparent biological quiet did not imply trustworthy absence.

These contradictions established that the programs were measuring different aspects of the observation process. They did not establish that disagreement should be prioritised for acquisition.

### 3.2. Direct disagreement and scalar disagreement allocation failed

In the V3 equal-budget test, disagreement priority did not outperform uniform or observability-only allocation for hidden-error recovery. At a 25% budget, hidden-error recall was approximately 0.251 for uniform, observability-only and direct disagreement, while biological-candidate priority increased event recall but sharply reduced hidden-error recovery.

Locked V5 provided the stronger negative result. The fixed scalar disagreement policy satisfied its complete preregistered gate only in a limited balanced-prevalence setting. Rare/common regimes showed prevalence sensitivity, and low-budget disturbance-family TV could become extreme. Complementary observer information nevertheless remained across multiple disturbance families. The locked failure was therefore attributed to scalar allocation rather than to the absence of complementary signal.

### 3.3. Guarded allocation performed well in development but failed general locked superiority

V6 development selected the frozen 50/10/40 portfolio with zero direct disagreement quota. Across the nine inspected development prevalence × budget cells, its worst joint event/error recovery ratio relative to uniform was 1.00846, mean joint ratio 1.11642 and maximum disturbance-family TV 0.21919.

V7 did not reproduce that general performance advantage on a new locked world. The scientific gate failed with worst joint ratio `0.9247839629`, mean joint ratio `0.9509088103` and maximum TV `0.202475`. The mechanically assigned claim level was C. Thus the protected exploration component continued to constrain distributional distortion, but the frozen observer-specific allocation did not establish unseen-world superiority.

This result demotes 50/10/40 from proposed method to tested historical instance.

### 3.4. V8 showed broad robustness but not regime-wise optimality

Across 864 abstract regimes, the frozen guarded portfolio achieved joint event/error recovery at or above uniform in `794/864 = 91.9%` of regimes. However, it was the best same-`alpha` comparator in only `185/864 = 21.4%`.

Failure regions were informative. All tested regimes at event prevalences 0.02, 0.10 and 0.50 met the uniform-or-better joint criterion, whereas only 67.6% did so at prevalence 0.90. Increasing residual correlation between the two observers also reduced the proportion of favourable regimes. The portfolio is therefore better described as a robust fixed compromise over many unknown regimes than as an optimal allocation rule.

### 3.5. Protected random exploration preserved the inferential denominator

V9 produced a qualitatively different result from the allocation benchmarks. Across 57,600 finite worlds, the prevalence estimator using protected exploration had mean bias approximately `9.1e-7`, while the naive estimator treating the full targeted sample as representative had mean bias approximately `+0.0426`.

The protected estimator's 95% interval coverage was `97.75%`, whereas naive coverage fell to approximately `52.4%`. Protected-estimator RMSE (`0.04282`) closely matched the finite-population theoretical standard deviation (`0.04237`), with ratio approximately `1.01`.

These results support a structural role for random exploration even when targeted acquisition is useful: it preserves a probability-sample subset that can support ecological estimation and reveal conditions jointly missed by all targeted observers.

### 3.6. V10 showed partial observation-risk transfer on real pixels

The locked V10 one-shot completed successfully after machine-verifying the prior V7 generation and exact observer commits. The preregistered result was claim C: `partial_or_family_specific_transfer`.

Four of six perturbation families had a strictly positive high-tier median paired risk delta, and five of six were dose-monotone. The global high-tier median paired risk delta was `0.62718017578125`. The frozen V6 allocation achieved the paired-uniform disturbance-recall criterion in `54/54` panel × budget cells, with overall mean paired-uniform recall ratio `1.309028695295118`.

However, the frozen stronger transfer criterion required at least five positive high-tier families. V10 therefore supports family-specific observability transfer on real image texture, not universal transfer. Because biological-event human truth was unavailable, it does not validate biological-event accuracy.

### 3.7. V11 rejected static contradiction states as transferable causal labels

The contradiction-guided V11 representation achieved held-out causal localisation accuracy only `0.3469`, with wrong-module intervention rate `0.8707`, shared-blind-spot discovery `0.2511` and repair-positive transfer `0.1963`. The locked claim level was D.

The dominant error was collapse of true failures into the no-fault class. In addition, the meaning of the low-evidence/low-risk state changed under mechanism-subtype shift: a state that had sometimes indicated a shared miss during development rarely did so in held-out worlds. Static contradiction states were therefore not stable causal labels.

### 3.8. Controlled interventions restored causal identifiability

V12 changed the information available to diagnosis by measuring how each observer responded to targeted interventions. Under the same two-intervention budget, dual-channel localisation accuracy was `0.9858`, compared with `0.9658` after early scalar fusion, `0.8767` for event-only and `0.8772` for observability-only representations.

The larger distinction appeared after the first intervention. Dual-channel accuracy was `0.9608`, whereas early scalar fusion was `0.7367`. Dual-channel wrong-module intervention rate was `0.0159` versus `0.0433` after early fusion, and mean interventions required to reach a stable diagnosis were `1.0108` versus `1.2614`.

The final two-intervention margin over early fusion was below the frozen threshold for a strong A claim, so V12 received claim B: `conditional_causal_identification_advantage`. Protected audit did not explain the effect: unaudited dual-channel episodes still reached approximately 0.983 accuracy.

The result supports a narrower interpretation: keeping observer channels separate can improve *diagnostic efficiency* when controlled interventions create channel-specific response signatures that distinguish competing failure hypotheses.

### 3.9. V13 physical validation is frozen but not yet claim-bearing

V13's physical apparatus, randomisation, blinding, measurement mapping, exact observer commits, held-out split, prediction commitment, cluster-level uncertainty and A–D claim ceiling are frozen before acquisition. The scientific execution digest is `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d` over 22 critical paths.

All pre-field protocol, execution-freeze, exact-observer smoke and full Python 3.10/3.11 CI gates pass. No V13 field clip, canonical pixel artifact, observer trace, held-out prediction or scientific result exists at the time of this draft.

---

## 4. Discussion

### 4.1. Contradiction was useful when it selected a test, not when it supplied an answer

The development history repeatedly rejected stronger interpretations of disagreement. Direct disagreement was not an efficient acquisition rule. Scalar disagreement was not robust to prevalence shift. A static taxonomy of disagreement states did not transfer as a causal failure label. These negative results converge on one point: a contradiction between scientifically different observers is underdetermined.

The useful role of contradiction emerged only after it was treated as a prompt for experiment design. If evidence and observability respond differently to controlled changes in a candidate causal pathway, the paired response can separate hypotheses that passive observation cannot. Contradiction-guided development therefore means *use disagreement to decide what to perturb or audit next*, not *use disagreement as truth*.

This is closer to differential testing than to disagreement-based active learning. The objective is not to maximise the frequency of disagreement. It is to turn incompatible observations into discriminating experiments.

### 4.2. Epistemic diversity is useful only when the experiment preserves its information

Keeping multiple channels separate is not automatically beneficial. V11 is an explicit counterexample: a richer contradiction-state representation performed poorly on held-out causes. V12 shows the condition under which distinct channels become valuable—controlled interventions generate response vectors whose geometry differs among competing failure hypotheses.

Early scalar fusion can erase that geometry. If two hypotheses differ along a channel direction that lies in the scalar projection's null space, no classifier applied after fusion can recover the lost distinction from that intervention. Separate channels are therefore not a generic virtue; they are useful when intervention responses contain complementary dimensions that matter for identifiability.

### 4.3. Protected random audit addresses a different failure: shared blind spots

Two observers can agree and still both be wrong. This is why contradiction cannot be the only diagnostic trigger. A protected probability sample provides information about the region where targeted observers do not request attention.

V9 makes that role concrete. The random component preserves an inferential denominator with finite-population sampling properties, while V8 shows that targeted performance varies with prevalence and observer correlation. The probability sample is therefore both an audit channel and an ecological estimation resource.

This suggests a three-lane deployment architecture:

```text
protected random exploration
  -> ecological denominator + shared-blind-spot audit

biological-evidence targeting
  -> event enrichment

observability-risk targeting
  -> observation-failure enrichment
```

Contradiction between targeted channels belongs primarily to development/diagnosis, not to a universal priority queue.

### 4.4. Locked negative results are part of the method

Simulation-rich software research is vulnerable to benchmark overfitting because every failure can become another tuning opportunity. Our generation structure intentionally converts some failures into permanent historical constraints.

V5 rejected fixed scalar disagreement. V7 rejected general superiority of frozen 50/10/40. V11 rejected static contradiction-state causal localisation. None of these generations was retuned after inspection. The later successful or partially successful generations changed the experimental question or policy class instead.

This separates two kinds of validation. Unit tests ask whether software behaves according to specification. Locked scientific tests ask which claims the specified software is allowed to support. A negative scientific result can therefore coexist with a successful reproducible workflow.

### 4.5. The allocation results should be interpreted conservatively

The guarded portfolio remains useful as a sampling architecture, but not as a universal performance recipe. V8 found wide regions in which 50/10/40 was robust relative to uniform, yet also showed that it was rarely regime-wise best and weakened under common events or highly correlated observer failures. V7 rejected unseen-world superiority, while V10 showed strong disturbance enrichment on real pixels without validating biological-event recovery.

The transferable part is therefore the *separation of functions*: probability-sample protection, event enrichment, observability audit and causal diagnosis. Numeric quotas must be revalidated for each deployment objective.

### 4.6. Relation to preferential sampling and active learning

The method acts upstream of model-based preferential-sampling correction. Protected exploration reduces the risk that adaptive selection removes large parts of the observation support, but statistical analysis should still retain acquisition probabilities or design metadata when estimates depend on the selected sample.

Likewise, the method is not a new disagreement-based active learner. Active learning commonly aims to improve label efficiency by selecting observations expected to improve a target predictor. Here the observation programs may have different targets, and the protected random component has a scientific-sampling role even when it is not the most label-efficient use of budget.

### 4.7. Limitations

First, most claim-bearing evidence remains simulation-based. V10 adds real image texture but no human biological-event truth. Second, V12 uses a known synthetic intervention topology and therefore demonstrates identifiability under controlled response structure rather than universal causal discovery. Third, V13 is a standardised physical proxy experiment, not natural-pollinator validation. Fourth, the PolliPi and InsePi observers are simple development programs, and their quantitative performance should not be generalised to other sensing systems. Fifth, maintaining separate implementations does not imply statistically independent failures. Sixth, protected exploration preserves a probability sample only if the random component is implemented and recorded as specified. Finally, the paper does not estimate device-specific energy gains, ecological effect sizes or species-level detection probabilities.

### 4.8. What V13 can establish

V13 is designed to answer a narrow transfer question: do intervention-response signatures learned on one set of physical failure subtypes support blinded causal treatment identification on new days, new scenes and different held-out physical subtypes?

A favourable V13 result would strengthen the claim that contradiction-guided intervention diagnosis transfers beyond synthetic response tables. An unfavourable result would not invalidate the sampling-safety theory or V9 design-based inference. It would instead bound the physical generality of the causal-diagnostic layer.

Field biological validation remains a later question requiring appropriate event truth, species labels or ecological response variables.

---

## 5. Software and reproducibility

The development programme is recorded in independently executable observer repositories plus a cross-observer methodology repository. Scientific generations are separated by frozen manifests, source commits, canonical artifacts, trace schemas, deterministic evaluators and claim ceilings.

Key locked provenance includes:

- V7 report SHA-256 `20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae`;
- V10 report SHA-256 `f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b`;
- V10 immutable artifact digest `8767e17ba18db106c3794c20a2f36f6b79580c785fbe58ad40a40cde6399c193`;
- V11 result SHA-256 `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`;
- V12 result SHA-256 `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`;
- V13 pre-field execution digest `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d`.

The generic guarded-portfolio and generic causal-diagnostic APIs are separated from PolliPi/InsePi-specific wiring and are covered by parity tests against their frozen development generations.

---

## 6. Data availability

Simulation worlds, frozen real-pixel perturbation artifacts, emitted traces, evaluation ledgers and reproducibility hashes are versioned or retained as workflow evidence according to generation. V10's underlying real evaluation videos are externally licensed data; V10's claim concerns predefined perturbations applied to those image bytes rather than redistribution of unrestricted biological-event labels.

V13 data do not yet exist. When acquired, raw native clips, observer-safe randomisation metadata, canonical truth-free pixel artifacts, observer traces, prediction commitment, blinded QC and final result provenance should be archived according to the frozen execution order, subject to storage and licensing constraints.

---

## 7. Author contributions

**To be completed before submission.** Separate conceptualisation, methodology, software, validation, visualisation, writing and supervision contributions using the journal's requested taxonomy.

---

## References (working citations)

Avizienis, A. (1985). The N-version approach to fault-tolerant software. *IEEE Transactions on Software Engineering*, SE-11(12), 1491–1501.

Bothmann, L. et al. (2023). Automated wildlife image classification: An active learning tool for ecological applications. *Ecological Informatics*, 77, 102231. https://doi.org/10.1016/j.ecoinf.2023.102231

Conn, P.B., Thorson, J.T. & Johnson, D.S. (2017). Confronting preferential sampling when analysing population distributions: diagnosis and model-based triage. *Methods in Ecology and Evolution*, 8(11), 1535–1546. https://doi.org/10.1111/2041-210X.12803

Diggle, P.J., Menezes, R. & Su, T.-l. (2010). Geostatistical inference under preferential sampling. *Journal of the Royal Statistical Society: Series C (Applied Statistics)*, 59(2), 191–232. https://doi.org/10.1111/j.1467-9876.2009.00701.x

Henrys, P.A., Mondain-Monval, T.O. & Jarvis, S.G. (2024). Adaptive sampling in ecology: Key challenges and future opportunities. *Methods in Ecology and Evolution*, 15(9), 1483–1496. https://doi.org/10.1111/2041-210X.14393

McKeeman, W.M. (1998). Differential testing for software. *Digital Technical Journal*, 10(1), 100–107.

Seung, H.S., Opper, M. & Sompolinsky, H. (1992). Query by committee. In *Proceedings of the Fifth Annual Workshop on Computational Learning Theory*, 287–294. https://doi.org/10.1145/130385.130417

**Reference metadata remains a working list and should receive the final bibliographic audit in the submission package.**