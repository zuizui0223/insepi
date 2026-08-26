# When disagreement should not drive sampling: contradiction-guided development of exploration-guarded ecological sensing

**Target journal:** Methods in Ecology and Evolution  
**Status:** pre-V7 working manuscript; the locked V7 result has not been materialised or inspected.  
**Result-dependent fields:** every `[[V7_LOCKED_RESULT]]` token must remain unresolved until the one-shot V7 execution ledger exists.

## Abstract

1. Autonomous ecological sensors can conserve storage, power and human review by preferentially recording windows that appear biologically informative. Yet preferential acquisition also changes the distribution of observed conditions, potentially making non-detection and observation error difficult to interpret. Biological-event evidence and observation-process reliability are therefore distinct inferential problems, even when they are computed from the same sensor stream.

2. We developed two deliberately non-equivalent observation programs in parallel: a biological-evidence observer that prioritises candidate interaction events (PolliPi), and an observability observer that estimates false-event, missed-event and attribution risks (InsePi). The programs remained independently executable and were compared only after inference on shared latent and byte-identical visual simulations. We treated contradictions between them as falsification signals rather than requiring agreement.

3. Direct disagreement was not automatically useful for finite-budget allocation. An initial equal-budget simulation showed no advantage over the strongest alternatives, and a subsequent one-shot locked validation falsified the stronger hypothesis that a fixed scalar disagreement ranking would remain robust under event-prevalence shift. Complementary observer information nevertheless persisted across disturbance families, localising the failure to the allocation seam rather than to loss of epistemic diversity.

4. We therefore replaced scalar ranking with an exploration-guarded portfolio that reserves a non-preferential sampling component and assigns separate quotas to biological-evidence and observability-risk signals. High-resolution development selected a frozen instance with 50% uniform exploration, 10% biological-evidence allocation and 40% observability-risk allocation, with zero direct disagreement quota. Across nine inspected prevalence-by-budget development regimes, this candidate had a worst joint event/error-recovery ratio of 1.00846 relative to uniform sampling, a mean joint ratio of 1.11642 and maximum disturbance-distribution total-variation distance of 0.21919.

5. The exploration guard also has distributional guarantees independent of observer accuracy. For target sampling distribution U, arbitrary targeted distribution R and Q = αU + (1−α)R, TV(Q,U) = (1−α)TV(R,U), Q(A) ≥ αU(A) for every target-supported condition set A, and U(x)/Q(x) ≤ 1/α. Thus adaptation can be bounded without assuming that either observer is correct.

6. [[V7_LOCKED_RESULT]]

7. We present the contribution as a simulation-first methodology for developing adaptive ecological sensing systems: preserve epistemically distinct observers, use contradiction to falsify acquisition assumptions, retain guaranteed exploration in the final sampling design, and separate method development from locked validation. The study does not claim field accuracy; empirical deployment is external validation.

**Keywords:** adaptive sampling; ecological monitoring; preferential sampling; edge sensing; observability; falsification; active learning; simulation; reproducible methods

---

## 1. Introduction

Ecological sensing is a measurement problem before it is a classification problem. Cameras, microphones and other autonomous sensors do not observe biological truth directly; they observe biological processes through a changing observation process. Wind, illumination, occlusion, blur, clutter, camera movement and sensor artefacts can all alter whether an ecological event is visible, whether an apparent event is real and whether an event can be attributed to the correct object. At the same time, ecological deployments often operate under hard constraints on storage, power, bandwidth and human review. These constraints create a strong incentive to allocate observation effort adaptively.

Adaptive acquisition can improve efficiency, but it also creates a second inferential problem: the sensor begins to choose which parts of the observation process enter the scientific record. This is closely related to preferential sampling in ecology, where the sampling process depends on the process or conditions being studied and naive analysis can become biased (Diggle, Menezes & Su, 2010; Conn, Thorson & Johnson, 2017). Recent work on adaptive ecological sampling similarly emphasises that targeted data collection can make raw samples non-representative unless the changing design is accounted for (Henrys, Mondain-Monval & Jarvis, 2024). In autonomous sensing, this problem can occur upstream of statistical analysis: an acquisition rule may preferentially retain particular visual or acoustic states before the ecological dataset exists.

A common response is to concentrate effort where a detector is confident that the target is present. This target-first strategy answers an important question—*does this window contain biological evidence worth preserving?*—but it does not answer a different one—*is this window sufficiently observable for presence, absence or attribution to be trusted?* A noisy window may deserve extra audit precisely because a target-first detector suppresses it. Conversely, a biologically plausible candidate may be scientifically ambiguous if the observation process is confounded. Collapsing both objectives into one confidence score therefore risks treating distinct scientific questions as a single ranking problem.

Neighbouring methodological traditions provide useful but incomplete analogies. Query by Committee actively selects samples on which a committee of models disagrees (Seung, Opper & Sompolinsky, 1992), whereas our observers are not interchangeable predictors of the same target and disagreement need not imply that a window should receive more acquisition effort. N-version programming maintains independently developed implementations for fault tolerance, typically relying on agreement or voting among implementations intended to satisfy the same specification (Avizienis, 1985); our observers intentionally implement different scientific specifications. Differential testing exposes faults by applying the same input to multiple implementations and inspecting divergent outputs (McKeeman, 1998), which is closer to our development logic, but our divergences arise partly because the programs answer different observation questions. Finally, active learning has been used in ecological image pipelines to reduce annotation effort (e.g. Bothmann et al., 2023), but label efficiency and sampling-design validity are separate objectives.

We began from a deliberately falsifiable hypothesis: structured disagreement between a biological-evidence observer and an observability-risk observer might identify windows that deserve additional sensing or audit under finite resource budgets. Rather than merging the programs into a single detector, we kept their objectives and implementations separate and exposed both to the same simulated worlds. This separation was intended to preserve contradictions long enough to reveal failure modes. Crucially, the development programme was structured so that disagreement itself could fail as an acquisition rule without invalidating the broader idea of epistemically distinct observation programs.

The study has five objectives. First, we define a same-input, independent-decision architecture for ecological sensing. Second, we test whether direct observer disagreement is an effective finite-budget acquisition rule. Third, when locked validation falsifies that rule, we localise the failure rather than retune the same scalar ranking. Fourth, we develop an exploration-guarded portfolio that combines non-preferential exploration with independent observer-specific acquisition quotas and derive distributional safety properties of that design. Fifth, we preregister a second one-shot locked simulation (V7) to challenge the frozen portfolio on new disturbances, prevalence regimes and resource budgets. The resulting paper is therefore as much about *how adaptive sensing software is developed and falsified* as about the final allocation rule.

---

## 2. Materials and Methods

### 2.1. Two epistemically distinct observation programs

We developed two edge-oriented observation programs with intentionally different scientific objectives. The biological-evidence program, PolliPi, estimates whether local image change provides evidence for a visitation candidate. Its visual front end performs registration, brightness normalisation, residual-motion extraction and overlapping spatial aggregation before assigning states including `no_activity`, `environmental_noise`, `uncertain_local_activity` and `strong_visitation_candidate`. The program is intended to support biological-event capture decisions; it is not an estimator of whether absence is trustworthy under every observation condition.

The observability program, InsePi, characterises the observation process. It represents disturbance sources such as camera motion, vegetation motion, illumination or shadow transients, occlusion, blur, lens contamination and multi-object clutter, and maps them to false-event, missed-event and attribution risks. Its states include clean, confounded, audit-priority and unobservable conditions. InsePi is not intended to replace the biological-event detector. A high observability risk means that a window may require audit or additional context, not that a biological event is present.

This asymmetry is central to the method. The two programs are *epistemically distinct*: they are allowed to disagree because they answer different questions about the same observation. We therefore do not assume statistically independent errors, equal calibration, or a latent consensus label that both programs should approximate.

### 2.2. Shared worlds and independent decisions

The programs were compared under a same-input / independent-decision contract. Simulation generated latent event truth and visual disturbance conditions, but hidden labels were not provided to either observer during inference. For same-pixel benchmarks, the rendered arrays were protected by SHA-256 fingerprints. Each program produced a portable trace containing only its own outputs and benchmark provenance. Cross-program comparison occurred after both decisions had been emitted.

The repositories were kept independently executable. Neither observer imported the other's decision logic. Shared material was restricted to benchmark contracts, canonical simulated pixels and emitted traces. Agreement was never used as a training or tuning objective.

### 2.3. Contradiction taxonomy

Post-decision contradictions were interpreted according to their scientific meaning rather than reduced immediately to one scalar. Examples included: (i) a biological candidate occurring under high false-event or attribution risk; (ii) a suppressed or quiet biological state occurring under high missed-event risk; (iii) environmental-noise suppression by the biological observer while the observability observer requested audit; and (iv) apparent absence under an unobservable scene. These cases distinguish support for an event from support for interpreting the observation process.

### 2.4. Generational development and falsification

We organised development into explicit generations so that data used to diagnose one generation could not later be described as untouched validation of the next.

| Generation | Question | Role / outcome |
|---|---|---|
| V1 | Do the two objectives produce structured contradictions at the policy level? | Development; yes |
| V2 | Do contradictions persist when both programs receive identical rendered pixels? | Development; yes, with additional front-end failures exposed |
| V3 | Does direct disagreement improve equal-budget allocation? | Negative development result |
| V4 | Can observability information be improved without merging the observers? | Development benchmark; used to diagnose and improve local structure audit |
| V5 | Is a fixed scalar disagreement ranking robust to prevalence shift? | **One-shot locked FAIL** |
| V6 | Can an exploration guard plus separate observer quotas repair the allocation failure? | Frozen development candidate |
| V7 | Does frozen V6 generalise to a new locked world? | One-shot final simulation; `[[V7_LOCKED_RESULT]]` |

No result from V5 was used to retune the same scalar disagreement score. Instead, its failure triggered a change in policy class.

### 2.5. Equal-budget evaluation

Allocation policies were compared at identical sensing or audit budgets. The main stress dimensions were event prevalence (rare, balanced and common) and budget fraction (10%, 25% and 50%). Replicate worlds were paired across policies so that policy differences were not confounded with different sampled worlds.

Primary performance quantities were true-event recall, observer-relative hidden-error recall, captures per recovered hidden error and total-variation (TV) distance between the disturbance-family distribution in the selected sample and that in the full simulated world. Here `hidden_error_recall` refers specifically to latent-truth PolliPi detection/attribution errors recovered by the selected audit set; it is not a world-intrinsic error state. V7 additionally reports disturbance-window recall and disturbed true-event recall as observer-independent secondary coverage metrics.

### 2.6. V3 equal-budget test

The first direct allocation comparison used the V2 same-pixel conditions under a 25% budget. Policies included uniform selection, PolliPi candidate priority, InsePi audit priority, logical union, logical intersection and structured disagreement priority. This test was designed as an early falsification screen rather than a final validation.

### 2.7. V4 observation-process development

Same-pixel inspection showed that PolliPi missed or suppressed several true visits under wind, camera shake, moving shadow, clutter, occlusion and blur, while the first InsePi pixel front end did not provide independent warning for some of these conditions. We therefore improved the observability front end using a local high-frequency structure-loss measure. A first absolute/intensity-correlation version recovered disturbances but generated excessive false risk on clean visits and was rejected. The retained version used local gradient correlation after alignment, with its occlusion threshold calibrated only on the V4 calibration split.

Because V4 test output was inspected during this development, V4 was explicitly downgraded from a final holdout to development evidence.

### 2.8. Locked V5 validation of scalar disagreement

V5 was defined before result inspection as a one-shot test of fixed scalar disagreement allocation. It contained 180 conditions, three event-prevalence regimes, three budget regimes and eight competing allocation policies. Each regime used 4,800 windows and 200 Monte Carlo replicates. Method code was frozen before execution and remained unchanged after inspection. The V5 world fingerprint was `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`; the PolliPi trace and cross-report were separately hashed and retained in the validation ledger.

The tested claim was narrow: *a fixed scalar ranking derived from independent-observer disagreement is a prevalence-robust allocation policy*. Failure of this claim did not imply that the observer outputs lacked complementary information.

### 2.9. V6 exploration-guarded observer portfolio

After V5, we replaced the global scalar ranking with an exact-budget portfolio. During development, the total budget B was decomposed into four possible quotas:

\[
B = B_U + B_P + B_I + B_D,
\]

where U denotes uniform exploration, P biological-evidence priority, I observability-risk priority and D direct disagreement priority. Uniform exploration was always positive. Each targeted arm ranked windows independently; quotas were interleaved so that no arm could overwrite another through a global score. When a targeted arm exhausted positive unique candidates, unused quota returned to uniform exploration rather than being transferred to another targeted observer.

Weights were fitted only on development/calibration worlds using paired minimax comparisons across prevalence and budget. Importantly, sparse fitting was allowed to assign zero weight to any targeted arm. Repeated development selected zero direct disagreement allocation. A focused high-resolution comparison then evaluated four nearby sparse portfolios, all with PolliPi quota 0.10 and disagreement quota 0:

- U=.40, P=.10, I=.50: event/error recovery remained favourable but maximum TV=.26567 exceeded the predefined .25 ceiling;
- **U=.50, P=.10, I=.40:** passed all nine development regimes, worst joint ratio=1.00846, mean joint ratio=1.11642, maximum TV=.21919;
- U=.60, P=.10, I=.30: passed, with lower TV=.17222 but slightly lower worst and mean joint ratios (1.00832 and 1.10303);
- U=.70, P=.10, I=.20: failed because hidden-error recovery fell below uniform under common prevalence (worst joint ratio=.98329).

The prespecified lexicographic development rule selected U=.50, P=.10, I=.40, D=0 and froze its implementation at commit `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`. These weights are an evaluated instance, not universal defaults.

### 2.10. Analytical properties of the exploration guard

Let U be a target or non-preferential observation distribution, R an arbitrary targeted acquisition distribution and α ∈ (0,1] the guaranteed exploration share. The ideal mixed acquisition distribution is

\[
Q = \alpha U + (1-\alpha)R.
\]

The TV distance from the target distribution contracts exactly:

\[
TV(Q,U) = (1-\alpha)TV(R,U) \le 1-\alpha.
\]

For every measurable condition set A,

\[
Q(A) \ge \alpha U(A),
\]

so any condition with positive target support retains a minimum fraction of that support under the adaptive design. Pointwise on the target support,

\[
\frac{U(x)}{Q(x)} \le \frac{1}{\alpha},
\]

which also implies \(D_\infty(U\Vert Q)\le\log(1/\alpha)\). At α=.5, the ideal target-to-adaptive importance ratio is bounded by 2. These are sampling-design properties and do not require either observer to be accurate or independently failing. The finite exact-quota implementation approaches this mixture while retaining deterministic budget accounting and spillover to exploration.

### 2.11. Generic guarded-portfolio API

To separate the method from the PolliPi/InsePi development instance, we implemented a generic guarded-portfolio reference API that accepts deployment-available acquisition scores under arbitrary arm names. Exact-selection parity tests confirm that an `evidence=.10`, `observability=.40`, `exploration=.50` representation reproduces the frozen V6 selector on representative worlds. The same acquisition contract can therefore be instantiated in camera traps, acoustic monitoring, nest cameras or phenology sensing, although transfer of any specific score or weight requires independent validation.

### 2.12. Locked V7 protocol

V7 is designed as a second one-shot validation generation. Before any final pixel is materialised, the protocol freezes the observer commits, allocator, generator, baseline registry, metrics, hard pass/fail rules and claim ceiling. The final seed is derived deterministically only after the two exact frozen observer commits are externally reachable and compatibility smoke tests pass.

The seed-independent V7 generator specifies 180 conditions: 15 disturbance families × three intensity tiers × two replicate slots × visit absence/presence. In addition to familiar disturbances, V7 includes sensor banding, glare and framing drift as OOD stressors not used in V4 development. The generator specification has SHA-256 `9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3`.

A single canonical pixel artifact is generated once and then read independently by both frozen observers. Latent event and disturbance metadata are attached only after each observer decision. A trace-only evaluator compares nine frozen policies: uniform; PolliPi-only; InsePi-only; legacy scalar disagreement; logical OR; logical AND; frozen V6; V6 without the PolliPi allocation arm; and V6 without the InsePi allocation arm. The baseline registry SHA-256 is `94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975`.

The strong V6 claim passes only if: (i) every prevalence-by-budget regime has joint event/error ratio ≥.98 relative to uniform; (ii) mean joint ratio >1; (iii) maximum disturbance TV≤.25; (iv) V6 worst-case robustness is not materially below a legacy targeted comparator; (v) neither observer-arm removal strictly dominates full V6; and (vi) leakage/provenance invariants pass. Scientific failure does not make the execution pipeline fail: the complete report is preserved and a preregistered claim ceiling (A–E) determines the strongest permitted interpretation.

At the time of this draft, V7 remains unmaterialised because the exact V5 observer commits have not yet been made publicly reachable. No V7 master seed, world fingerprint or pixel artifact has been generated.

---

## 3. Results

### 3.1. Independent objectives generated reproducible complementary states

At the policy level (V1), the two observation programs produced structured rather than random contradictions. Clean visits yielded biological candidate evidence under low observation risk, whereas broad environmental motion could produce biological suppression together with high audit risk. Occlusion and blur produced complementary caution in which weak biological evidence coincided with elevated missed-event concern.

When the comparison was moved from latent feature templates to identical rendered pixels (V2), several conflicts became stronger. PolliPi recovered a clean visit as a strong candidate but classified true visits under vegetation-like motion, camera shake, moving shadow and clutter as environmental noise. Occluded and blurred visits could fall to `no_activity`. These failures were scientifically useful because they showed that front-end measurement, not only the final state machine, determined the disagreement structure.

### 3.2. Direct disagreement did not automatically improve finite-budget allocation

The V3 equal-budget comparison rejected the first naive expectation that disagreement itself would be the strongest acquisition rule. At a 25% budget, hidden-error recall was approximately .251 for uniform sampling, InsePi-only audit allocation and disagreement allocation. PolliPi candidate priority achieved higher event recall (~.325) but much lower hidden-error recall (~.100), while union and intersection policies exhibited different event/error trade-offs. Thus disagreement was informative about observer conflict but did not by itself establish superior allocation efficiency.

### 3.3. Same-pixel failure analysis improved observability without merging observers

V2 showed an important missing complement: the initial InsePi visual front end treated several occlusion, blur and clutter cases as clean, so it could not warn when PolliPi missed the same events. An intensity-correlation audit was first tested and rejected because it flagged approximately half of clean test windows as risky. Replacing it with local gradient-correlation preserved smooth biological intensity changes while responding to disruption of scene structure.

On the inspected V4 development test split, the retained observability front end produced zero false-risk calls on clean conditions and a disturbance-risk recall of .875. Risk recall was .75 for occlusion and clutter, 1.0 for blur, occlusion+blur, wind, shadow, shake and the tested broad mixed disturbances, while the lens OOD family remained missed. The retained lens failure was not tuned away. PolliPi candidate recovery on the same V4 pixels remained low for several disturbance families, preserving a complementary-error structure for allocation testing.

### 3.4. Locked V5 falsified prevalence-robust scalar disagreement allocation

The one-shot V5 validation produced a clear negative result. Across 180 conditions, three prevalence regimes, three budgets, eight policies and 4,800-window worlds evaluated over 200 replicates, the fixed scalar disagreement policy passed the complete predefined gate only under balanced prevalence at the 25% budget. Under rare-event prevalence, the 10% and 25% cases fell outside the Pareto frontier and were beaten by a single-view removal. Under common prevalence at 25% budget, InsePi-only allocation achieved higher hidden-error recall. At the 10% budget, disturbance-distribution TV could reach approximately .833, revealing severe concentration of the selected observation conditions.

Importantly, the observer complementarity itself did not disappear. Complementary signals remained detectable in approximately six to seven disturbance families within each prevalence setting. We therefore localised the locked failure to the mapping from multiple observer outputs into one fixed scalar ranking. V5 falsified the *allocation rule*, not the usefulness of epistemically distinct observation programs.

### 3.5. V6 development removed disagreement from direct allocation

The V6 policy class replaced one global ranking with independent quotas plus guaranteed exploration. The first forced four-arm fit reduced the extreme V5-style distributional concentration but still lost hidden-error recall relative to uniform in several balanced or common-prevalence regimes. Allowing sparse portfolios caused calibration to assign zero weight to the direct disagreement arm. This result was retained rather than overridden to preserve the original hypothesis.

A medium-resolution paired robustness gate then identified an exploration-dominant sparse portfolio as the only tested candidate that avoided losses in both event and hidden-error recovery across all nine prevalence-by-budget regimes while satisfying TV≤.25. Focused high-resolution development confirmed a narrow admissible region rather than a broad optimum.

### 3.6. High-resolution V6 development froze a 50/10/40 portfolio

In the final development sweep, U=.40/P=.10/I=.50 failed only the predefined TV ceiling, whereas U=.70/P=.10/I=.20 failed common-prevalence hidden-error robustness. Both U=.50/P=.10/I=.40 and U=.60/P=.10/I=.30 passed all nine regimes. The prespecified selection rule chose U=.50/P=.10/I=.40 because it had the slightly larger worst joint ratio (1.00846 versus 1.00832) and mean joint ratio (1.11642 versus 1.10303), while retaining maximum TV=.21919.

The weakest margin was intentionally retained in the headline evidence: under common event prevalence, event-recall ratios relative to uniform were only approximately 1.008–1.009. V6 was therefore frozen as a candidate to be challenged, not treated as confirmed from development data.

### 3.7. Exploration provided guarantees independent of the performance result

The exploration component yielded an analytical result separate from the empirical choice of observer weights. Mixing any targeted acquisition distribution with an α share of the target distribution contracts total-variation distortion by exactly 1−α, retains at least an α fraction of target support for every condition set and bounds target-to-acquisition importance ratios by 1/α. Consequently, even if the targeted observers are poorly calibrated, the exploration share limits how completely the adaptive system can remove target-supported observation states.

### 3.8. Locked V7 validation

[[V7_LOCKED_RESULT]]

This subsection will be populated only from the immutable V7 execution ledger. It must report the scientific gate result, all failed rules (if any), worst and mean joint ratios, maximum TV, observer-arm ablations, observer-independent coverage metrics, world/trace/report hashes and the mechanically assigned claim level A–E. No preceding method or development result may be edited to accommodate the outcome.

---

## 4. Discussion

### 4.1. The useful role of disagreement was diagnostic rather than acquisitional

The central development result was not that disagreement became a better ranking score. It was the opposite. Keeping the observers separate made it possible to discover that a plausible disagreement-priority rule failed under changes in event prevalence and finite sensing budget. V5 then localised the failure to scalar allocation while complementary observer signals remained. In the frozen V6 policy, disagreement therefore has zero direct acquisition quota.

This does not make disagreement irrelevant. It changes its role. Contradiction identifies incompatible assumptions, exposes where one observer lacks warning for the other's failure, and determines what should be falsified next. In this sense, disagreement functions more like differential testing for scientific measurement software than like Query by Committee acquisition. The desired endpoint is not maximum disagreement; it is a better-specified observation design.

### 4.2. Epistemic diversity is different from redundant ensemble diversity

The two observers are not exchangeable models estimating one label. A biological-evidence observer asks whether a candidate event is supported; an observability observer asks whether the measurement conditions permit reliable interpretation. Agreement can be reassuring, but disagreement can also be the expected consequence of asking non-equivalent questions. Majority voting would erase this distinction. The method therefore preserves outputs until the acquisition layer, where each targeted signal receives an independently controlled quota.

This distinction matters for transfer. An acoustic implementation could pair a species-call evidence score with an observability score for wind, overlap or recorder saturation. A phenology camera could pair a flowering-state score with a visibility score for snow, obstruction or illumination. The software objects can change while the acquisition contract remains the same.

### 4.3. Exploration is measurement design, not wasted budget

Adaptive sensing is often framed as a competition between informative selection and inefficient random sampling. The preferential-sampling perspective suggests a different interpretation. A non-preferential component preserves information about the denominator: the observation conditions in which events could have occurred but were not preferentially retained. This matters for interpreting absence, detecting changes in the observation process and correcting the selected sample toward a target design.

The exploration theorem formalises a limited but useful guarantee. It does not show that 50% exploration is universally optimal, nor that any particular targeted observer is beneficial. Instead, it states what targeted acquisition *cannot do* once α exploration is protected: it cannot increase TV distortion beyond the contracted mixture, eliminate target-supported conditions entirely, or create arbitrarily large target-to-acquisition importance ratios. The frozen 50% share is an empirical V6 instance inside this broader design class.

### 4.4. Locked falsification can reduce benchmark overfitting in research software

Simulation-rich method development carries a familiar danger: every failure can become another opportunity to tune against the same benchmark. Our generation structure attempts to make those decisions visible. V3 was retained as a negative early result; V4 was explicitly demoted from final holdout after it informed feature development; V5 was executed once under a frozen method and its failure was not repaired under the same generation; V6 changed the policy class; and V7 is prevented by code from materialising until exact frozen inputs are externally reachable.

This workflow is deliberately stricter than ordinary software testing. Unit tests establish implementation correctness, whereas locked simulation tests establish which scientific claims the implementation is allowed to support. Preserving both creates an auditable separation between “the code behaves as specified” and “the scientific hypothesis survived its test.”

### 4.5. Relation to active learning and preferential sampling

Our method should not be read as a new version of disagreement-based active learning. Query by Committee selects cases because predictors disagree; V5 directly shows why an analogous fixed disagreement rule can be problematic for this ecological measurement setting. Nor do we claim that uniform exploration itself is novel. The contribution is the combination of contradiction-guided generational development, non-equivalent observer roles, explicit sampling-distribution safeguards and no-peek validation.

This design also complements rather than replaces model-based treatments of preferential sampling. The exploration guard changes data acquisition upstream; statistical correction for preferential effort may still be required downstream. A field deployment should retain acquisition probabilities or quota metadata so that ecological estimators can account for the design.

### 4.6. Limitations

First, the present evidence is simulation-based. The disturbance operators are deliberately diverse but cannot reproduce the full distribution of real field scenes, and the final V7 OOD set is still finite. Second, the primary hidden-error endpoint is observer-relative: it measures recovery of PolliPi detection or attribution errors under known simulation truth. We therefore include observer-independent disturbance coverage measures but do not redefine hidden error as an intrinsic property of the world. Third, the resource model represents finite acquisition or audit budgets rather than device-specific energy and storage curves. Fourth, the frozen 50/10/40 weights may be specific to the development observers and disturbance mix. The transferable result is the guarded-portfolio architecture and its sampling properties, not the numeric vector. Fifth, maintaining separate programs does not imply statistically independent failure modes. Finally, no simulation result establishes real-world species classification, visit-rate estimation, power consumption or ecological effect sizes.

### 4.7. Implications conditional on V7

[[V7_LOCKED_RESULT]]

If V7 reaches claim level A, the main performance conclusion will be that the frozen exploration-guarded dual-observer portfolio survived a second locked prevalence/budget challenge. If the result is B or C, the manuscript will retain the conditional or bias-control claim without describing the allocator as generally superior. If arm removal or broader allocation failures produce level D, the paper will recentre on contradiction-guided software development and observer complementarity. A level E outcome will be reported as a reproducible benchmark/falsification result. These interpretation rules were fixed before V7 materialisation.

### 4.8. Empirical next step

Field data should test external validity, not rescue the simulation method post hoc. A deployment can ask whether the biological-evidence observer retains event recall, whether the observability observer's risks are calibrated against human audit, whether the exploration component supports unbiased or design-aware ecological estimation, and whether the resource gains justify the extra computation. Those are empirical questions that begin after the present simulation methodology is frozen.

---

## 5. Software and reproducibility

The development programme is recorded in two separately executable repositories, with shared information restricted to benchmark contracts, canonical pixel artifacts and portable traces. V6 development evidence, V5 falsification hashes, the V7 seed-independent world specification, baseline registry, hard gate and claim ceiling are versioned before final V7 execution. The V7 one-shot workflow distinguishes execution integrity from scientific success: a scientifically negative result is still a successful reproducible execution and must preserve its complete evidence bundle.

The public allocation reference implementation is the generic guarded-portfolio API rather than the PolliPi/InsePi-specific development wiring. The exact frozen observer commits, canonical artifact SHA-256, emitted trace hashes, evaluator provenance and final report hash will be supplied in this section after V7.

`[[V7_LOCKED_RESULT:REPRODUCIBILITY_LEDGER]]`

---

## 6. Data availability

All data used for method development are simulated or generated from deterministic benchmark specifications. No empirical ecological dataset is required for the claims in this manuscript. The final V7 canonical artifact and/or a deterministic regeneration contract, together with its provenance hashes, will be archived with the software release after locked execution.

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

**Reference metadata remains a working list and must receive a final bibliographic audit before submission.**
