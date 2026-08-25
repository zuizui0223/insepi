# Method-paper gate: contradiction-guided development of ecological sensing

## Current submission hypothesis

The paper must not claim field biological accuracy. The claim-bearing methodological hypothesis is now:

> Adaptive ecological sensing is easier to falsify and diagnose when observation programs with different scientific objectives are kept independently executable, contradictions are used to select discriminating tests rather than collapsed into a priority score, controlled interventions are used to identify failure causes, and a protected probability-sampling component is retained to audit shared blind spots and support ecological inference.

This replaces the earlier candidate claim that a particular fixed dual-observer allocation such as `50% uniform / 10% biological evidence / 40% observability risk` is generally superior. That allocation remains an important tested generation, but locked V7 rejected a general performance claim for it.

The current method has four components:

1. **independent observation hypotheses** — biological-event evidence and observation-process risk remain separate;
2. **contradiction-guided development** — agreement/disagreement patterns generate failure hypotheses but are not treated as truth;
3. **controlled causal diagnosis** — competing failure hypotheses are separated by paired interventions and their observer-response signatures;
4. **protected random audit** — a non-preferential sample remains available to detect shared blind spots and to preserve a design-valid inferential denominator.

## G1 — Independent implementations

- PolliPi and InsePi remain separately executable.
- Neither imports the other's decision logic.
- Common material is restricted to input/world contracts, canonical pixels and emitted traces.
- Agreement is never a tuning target.
- Exact frozen observer smoke tests verify module origin and cross-import separation.

**Status: PASS.**

## G2 — Same-input / independent-decision provenance

- byte-identical visual inputs are shared across observers;
- latent biological/disturbance truth is withheld during observer inference;
- source commits, pixel hashes, runtime pins and trace hashes are retained;
- post-decision comparison occurs only after both observer traces exist;
- no claim of statistically independent observer errors is made.

**Status: PASS.**

## G3 — Direct disagreement as an acquisition rule

### V3

At equal budget, direct disagreement did not outperform the strongest alternatives. This negative result was retained.

### Locked V5

A stronger fixed scalar disagreement ranking failed under prevalence shift. Complementary observer information nevertheless remained present across disturbance families, localising the failure to the scalar allocation seam rather than showing that distinct observers were useless.

**Status: REJECTED as a general acquisition rule.**

## G4 — Exploration-guarded allocation generation

V6 changed policy class rather than retuning the failed V5 scalar score. The frozen development instance was:

```text
50% protected uniform exploration
10% biological-evidence targeting
40% observability-risk targeting
 0% direct-disagreement targeting
```

Development evidence across nine prevalence × budget cells showed worst joint recovery ratio `1.00846`, mean joint ratio `1.11642`, and maximum disturbance-family TV `0.21919` relative to uniform. This established a useful development candidate, not a universal optimum.

**Status: development candidate established; universal superiority not supported.**

## G5 — Sampling-safety theory and finite-budget guarantees

For ideal mixed acquisition

```text
Q = alpha U + (1-alpha)R
```

we retain:

- `TV(Q,U) = (1-alpha) TV(R,U) <= 1-alpha`;
- `Q(A) >= alpha U(A)` for any target-supported condition set;
- `U(x)/Q(x) <= 1/alpha` on target support;
- `D_infinity(U||Q) <= log(1/alpha)`.

For finite sampling without replacement, the protected uniform quota also gives explicit minimum inclusion probability and exact rare-family miss probabilities. With a fixed target family of size `m`, population `N`, and protected simple-random quota `q_U`,

```text
P(miss family) = C(N-m, q_U) / C(N, q_U).
```

These are sampling-safety statements and do not require either observer to be accurate.

**Status: PASS; implemented and tested.**

## G6 — V7 locked validation of frozen 50/10/40

V7 was executed once using the exact frozen observer commits.

Locked result:

- gate: **FAIL**;
- claim level: **C**;
- worst joint ratio: `0.9247839629`;
- mean joint ratio: `0.9509088103`;
- maximum TV: `0.202475`;
- report SHA-256: `20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae`.

The selection-distribution safety property survived, but the frozen portfolio did not provide general unseen-world performance superiority.

**Status: general allocation-superiority claim REJECTED.**

Scientific consequence: do not make `50/10/40` the paper's central contribution.

## G7 — V8 generality map

An abstract observer-level benchmark separated the method class from one renderer and one pair of image heuristics.

Across 864 regimes varying prevalence, budget, Observer-E quality, Observer-O quality, residual correlation and disturbance prevalence:

- frozen `50U+10E+40O` achieved joint event/error recovery at or above uniform in **794/864 = 91.9%** of regimes;
- it was the best same-alpha policy in only **185/864 = 21.4%**;
- performance weakened at very common events and as observer residual correlation increased.

This shows that the portfolio is a robust compromise in many unknown regimes, not a regime-wise optimum.

**Status: PASS as generality/failure-region characterisation.**

## G8 — V9 design-based ecological inference

V9 separated targeted acquisition from the inferential denominator.

Across 57,600 finite worlds:

- protected-exploration prevalence estimator mean bias was approximately `9.1e-7`;
- 95% interval coverage was `97.75%`;
- targeted-all-sample naive estimator mean bias was approximately `+0.0426`;
- naive interval coverage fell to approximately `52.4%`;
- protected-estimator RMSE closely matched the finite-population theoretical SD (`RMSE / theoretical SD ≈ 1.01`).

The scientific interpretation is important: protected random exploration is not only an algorithmic safety valve. It preserves a probability-sample subset that can serve as the reference denominator for ecological inference and can reveal shared observer blind spots.

**Status: PASS.**

## G9 — V10 real-pixel observation-process transfer

V10 used seven byte-frozen real honeybee evaluation videos and 6,916 real-pixel conditions with preregistered perturbation families and intensity tiers. Human biological-event frame truth was unavailable, so V10 tested observation-process perturbation transfer rather than pollinator-detection accuracy.

Manual one-shot run `32693453262` produced:

- claim level **C** — `partial_or_family_specific_transfer`;
- positive high-tier perturbation families: **4/6**;
- dose-monotone families: **5/6**;
- global high-tier median paired risk delta: `0.62718017578125`;
- V6 allocation cells at or above paired uniform: **54/54**;
- overall mean paired-uniform recall ratio: `1.309028695295118`;
- report SHA-256: `f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b`;
- immutable evidence artifact digest: `8767e17ba18db106c3794c20a2f36f6b79580c785fbe58ad40a40cde6399c193`.

V10 therefore supports family-specific transfer of the observability signal to real image texture, but not universal disturbance transfer and not biological-event accuracy.

**Status: partial real-pixel transfer, claim C.**

## G10 — Static contradiction-state failure localisation

V11 tested whether a static representation of raw observer channels plus high/low contradiction states and a protected audit indicator could identify held-out failure causes across mechanism-subtype shift.

Locked result:

- claim level **D**;
- contradiction-guided held-out localisation: `0.3469`;
- wrong-module intervention rate: `0.8707`;
- shared-blind-spot discovery: `0.2511`;
- repair-positive transfer: `0.1963`.

The dominant error was collapse of true faults into `no_fault`. The meaning of the low/low state also changed strongly under held-out mechanism shift.

**Status: static contradiction taxonomy as a causal localiser REJECTED.**

Scientific consequence: contradiction must not itself be treated as a stable causal label.

## G11 — Controlled interventions restore identifiability

V12 changed the experiment instead of retuning the V11 classifier. All representations received the same intervention candidates, intervention budget and diagnostic algorithm; the representations differed only in whether observer channels were retained separately or compressed.

Canonical locked result:

- claim level **B** — `conditional_causal_identification_advantage`;
- dual-channel accuracy after two interventions: `0.9858`;
- early scalar fusion after two interventions: `0.9658`;
- dual-channel accuracy after one intervention: `0.9608`;
- early fusion after one intervention: `0.7367`;
- dual wrong-module intervention rate: `0.0159`;
- early-fusion wrong-module rate: `0.0433`;
- dual mean interventions to stable diagnosis: `1.0108`;
- early fusion: `1.2614`;
- canonical result SHA-256: `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`.

The strongest advantage of keeping channels distinct appeared in **diagnostic efficiency after the first intervention**, not in a dramatic final two-intervention accuracy margin.

**Status: conditional support for causal-intervention diagnosis, claim B.**

## G12 — Generic causal-diagnostic method

The V12 logic is extracted into an observer-agnostic API:

1. fit response signatures by failure hypothesis and intervention;
2. select the first intervention by maximin separation;
3. retain the nearest competing hypotheses;
4. select the next intervention to separate those hypotheses;
5. diagnose from the observed paired response vector.

The information boundary is explicit: if a projection maps distinct intervention-response vectors onto the same value, identifiability is lost in that projection. Keeping multiple scientifically distinct channels is useful only when the channel-specific intervention response retains separation that scalarisation destroys.

Exact parity tests reproduce V12 dual-channel centroids, intervention order and diagnoses through the generic API.

**Status: PASS as generic implementation/theory extraction.**

## G13 — V13 blinded physical intervention validation

V13 is frozen before physical acquisition. It tests the causal-diagnostic method on a physical same-stream system rather than another synthetic renderer.

Frozen design:

- 108 development blocks = 3 actual days × 3 actual scenes × 4 treatment classes × 3 replicates;
- 72 held-out blocks = 2 new days × 3 new scenes × 4 classes × 3 replicates;
- frames are repeated measurements, not replicates;
- four 10-s phases per block: placebo + three non-cumulative interventions;
- all three interventions are collected, but the primary held-out analysis replays only the algorithm-selected two;
- final uncertainty clusters by actual completed-capture `recording_date_local × physical_scene_code`;
- development and held-out days/scenes are disjoint;
- held-out predictions are SHA-committed before truth unsealing;
- protected physical QC is blinded to observer output and cannot relabel treatment post hoc.

Scientific execution freeze:

- 22 critical paths;
- digest SHA-256: `96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d`;
- exact PolliPi: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- exact InsePi: `980813bab996909020140fad5bd83b055eb3db9c`;
- all V13 pre-field, execution-freeze, exact-observer smoke and full Python 3.10/3.11 CI gates are green.

No V13 scientific result exists yet.

**Status: FIELD-READY / RESULT PENDING.**

## What the development programme has falsified

The negative generations are part of the method rather than failed side projects:

1. observer disagreement is not automatically a useful acquisition priority;
2. a fixed scalar disagreement ranking is not prevalence-robust;
3. a frozen 50/10/40 portfolio is not generally superior on an unseen locked world;
4. a static contradiction-state representation is not a transferable causal failure label;
5. retaining independent observer channels becomes useful when contradictions motivate controlled interventions that can separate competing causal hypotheses;
6. even two observers can share a blind spot, so independent probability-sample audit remains necessary.

## Current paper thesis

The strongest defensible paper is no longer an allocator paper. It is a methodology paper about **falsifiable development of ecological observation systems**:

> Keep observation programs with different scientific purposes separate long enough to expose contradictions. Do not use contradiction itself as truth or as an automatic acquisition priority. Use it to formulate competing failure hypotheses and choose controlled interventions that can distinguish them. Retain protected random exploration because observer agreement cannot rule out shared blind spots and because probability sampling preserves an inferential denominator.

The sequence

```text
independent observers
→ contradiction
→ falsified scalar allocation
→ guarded exploration
→ locked allocation failure
→ static localisation failure
→ controlled intervention diagnosis
→ blinded physical validation
```

is the claim-bearing development history.

## MEE manuscript structure

1. **Observation problem** — biological state and observation-process state are different scientific quantities.
2. **Epistemically distinct observers** — same input, independent decision contracts.
3. **Contradiction-guided development** — contradictions generate tests, not consensus or automatic priority.
4. **Failed acquisition hypotheses** — V3, V5 and V7.
5. **Protected random audit** — sampling-safety theorem, finite-budget guarantees, V8 failure map and V9 design-based inference.
6. **Why static contradiction is insufficient** — V11 locked failure.
7. **Causal intervention method** — generic intervention-response diagnosis and V12 conditional result.
8. **Real-pixel boundary evidence** — V10 partial observation-process transfer.
9. **Blinded physical validation** — V13 protocol and, when available, locked result.
10. **Scope** — no universal observer superiority, no natural-pollinator accuracy claim without appropriate truth, and no claim that disagreement itself is intrinsically informative.

## Current paper-readiness decision

**Scientifically coherent, but strong MEE version remains result-pending on V13.**

A conservative simulation-first manuscript can already be written around the falsification sequence, protected probability sampling, V8/V9 generality/inference results, V10 real-pixel partial transfer and V12 causal-identification result. However, the stronger MEE claim that contradiction-guided causal diagnosis transfers to a physical observation system should not be made until V13 is executed exactly as frozen.

No additional simulation retuning is recommended before V13. The next claim-bearing scientific work is physical acquisition under the frozen V13 protocol.