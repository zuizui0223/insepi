# Standalone methods-paper blueprint

## Working title options

### Result-forward

**When disagreement should not drive sampling: exploration-guarded dual-observer sensing after locked falsification**

### Method-forward

**Contradiction-guided development for exploration-guarded ecological sensing**

### Question-forward

**Can independent observation programs improve adaptive ecological sensing without biasing what gets observed?**

The first title is the most distinctive if V7 supports the frozen V6 allocation.
The second is safer if V7 lowers the allocation claim ceiling but preserves the
development/falsification contribution.

## One-sentence paper question

> Can epistemically distinct observation programs be developed in parallel so that
their conflicts expose failure modes, while a finite-budget allocation policy uses
their complementary outputs without reproducing the selection bias caused by
purely targeted sensing?

## Candidate contribution statement

The paper is not about a new insect classifier. It introduces and tests a
simulation-first methodology with three separable ideas:

1. preserve two non-equivalent observation programs instead of prematurely merging
   them;
2. use structured contradiction as a falsification/development signal, not assume
   it is an optimal acquisition score;
3. after fixed disagreement allocation fails, impose a guaranteed exploration
   component around independent observer-specific exploitation quotas.

The final performance claim is conditional on locked V7. The theoretical
exploration guarantees do not depend on V7.

## Abstract skeleton

### Background/problem

Autonomous ecological sensors can reduce observation costs by preferentially
recording windows that appear biologically informative. The same adaptivity can
bias the distribution of observation conditions and make non-detection difficult
to interpret. Biological-event evidence and observation-process reliability are
different inferential problems but are often collapsed into one detector score.

### Approach

We independently developed two edge-observation programs: a biological-evidence
observer (PolliPi) and an observability/error-risk observer (InsePi). We compared
them on shared latent and byte-identical pixel simulations while preventing either
observer from importing the other's decision logic. Successive method generations
were evaluated under fixed audit budgets, prevalence shifts, disturbance mixtures,
OOD conditions and frozen falsification gates.

### Development result already known

A locked validation falsified our initial hypothesis that fixed scalar observer
disagreement provides a prevalence-robust allocation rule. The failure localised to
the allocation seam rather than loss of complementary observer information. We
therefore replaced scalar ranking with an exploration-guarded observer portfolio.
High-resolution development selected 50% uniform exploration, 10% biological-
evidence allocation and 40% observability-risk allocation, with zero direct
disagreement quota.

### Theory

For target observation distribution `U`, arbitrary targeted distribution `R`, and
`Q = alpha U + (1-alpha)R`, the exploration guard yields
`TV(Q,U)=(1-alpha)TV(R,U)`, `Q(A)>=alpha U(A)` for every condition set `A`, and
`U(x)/Q(x)<=1/alpha` on the target support.

### Locked validation placeholder

**Do not fill until V7 is inspected.** Insert the frozen V7 outcome and claim level
from `V7_CLAIM_CEILING.md` verbatim in substance.

### Scope

The paper establishes a sensing/development methodology under simulation, not
field accuracy. Empirical deployment is external validation.

## Introduction logic

### Paragraph 1 — ecological observation is a measurement process

Ecological cameras do not observe biological truth directly. They observe a scene
through wind, light, occlusion, blur, clutter, camera motion and limited storage or
power. Thus the scientific variable and the observation process must be separated.

### Paragraph 2 — adaptivity creates a second inference problem

Adaptive sensors save resources by recording informative moments, but targeted
selection changes the sampling distribution. Connect this to ecological
preferential-sampling literature and the risk that sampling decisions depend on the
process being inferred.

### Paragraph 3 — one scalar cannot automatically serve both objectives

Target-first sensing asks whether a biological event is likely. Noise-first sensing
asks whether absence/presence attribution is trustworthy. A high target score and a
high observation-risk score have different meanings and sometimes demand opposite
capture actions.

### Paragraph 4 — relevant neighbouring methods

Briefly distinguish:

- Query by Committee: disagreement as acquisition;
- N-version programming: equivalent implementations plus consensus/fault
  tolerance;
- differential testing: discrepancies as candidate faults;
- ecological preferential/adaptive sampling: bias induced by non-random effort.

### Paragraph 5 — our initial hypothesis and willingness to falsify it

State the original hypothesis explicitly: structured disagreement between an event
observer and an observability observer could identify windows worth additional
audit under finite budget. Then state that the methodology was designed so this
hypothesis could fail without collapsing the entire research programme.

### Paragraph 6 — paper objectives

1. define independent dual-observer architecture;
2. test direct disagreement allocation;
3. localise failure when the locked test fails;
4. derive an exploration-guarded alternative with analytical bias guarantees;
5. challenge the new generation under a second one-shot locked validation.

## Methods

### 2.1 Two epistemically distinct observers

Define PolliPi and InsePi by scientific objective, input/output contracts and what
each is **not** intended to infer. Emphasise non-equivalence.

### 2.2 Shared-world / independent-decision contract

Explain latent truth, same-pixel fingerprints, portable traces and prohibition on
cross-importing decision logic.

### 2.3 Contradiction taxonomy

Classify disagreements such as:

- candidate under high false/attribution risk;
- suppressed/no activity under high missed-event risk;
- environmental-noise suppression versus audit priority;
- epistemic absence versus unobservable state.

Disagreement is measured after independent decisions.

### 2.4 Method generations and frozen boundaries

A compact table should show:

| generation | question | status |
| --- | --- | --- |
| V1 | do different objectives produce structured contradictions? | development |
| V2 | do contradictions persist from identical pixels? | development |
| V3 | does direct disagreement win equal-budget allocation? | negative |
| V4 | can independent observability information be improved without merging observers? | development |
| V5 | is fixed scalar disagreement prevalence-robust? | **locked FAIL** |
| V6 | can exploration-guarded observer quotas repair the allocation failure? | frozen development candidate |
| V7 | does frozen V6 generalise to new locked worlds? | one-shot, currently unexecuted |

### 2.5 Equal-budget evaluation

Describe 3 prevalence regimes, 3 budgets, paired worlds, latent event truth,
observer-relative PolliPi detection-error recall, captures/error and disturbance TV.

### 2.6 Metric semantics

Explicitly state that hidden-error recall is observer-relative. Add
observer-independent disturbance-window recall and disturbed true-event recall as
secondary V7 diagnostics.

### 2.7 V5 falsification gate

Report the preregistered V5 design and hashes before discussing results. Make clear
that method code was not modified after V5 inspection.

### 2.8 V6 exploration-guarded allocation

Define four development arms, then explain why sparse development reduced the
final direct disagreement quota to zero. Give final frozen allocation and spillover
rule.

### 2.9 Exploration-guard theorem

State and prove:

```text
TV(Q,U) = (1-alpha)TV(R,U)
Q(A) >= alpha U(A)
U(x)/Q(x) <= 1/alpha
```

Clarify ideal-mixture versus finite quota implementation.

### 2.10 V7 one-shot protocol

Describe lock verification, deterministic seed derivation, canonical pixel
artifact, independent traces, trace-only evaluator, hard rules and claim ceiling.
No V7 result appears in Methods.

## Results structure

### 3.1 Independent observers produce reproducible complementary states

Use V1/V2 to show that the two programs do not simply duplicate each other.

### 3.2 Direct disagreement does not automatically improve allocation

Lead with V3 negative result. This prevents the paper from reading like a post-hoc
success story.

### 3.3 Same-pixel failure analysis localises missing complementary information

Show V2/V4 examples: PolliPi suppression/misses, InsePi risk detection and the
occlusion/blur feature correction.

### 3.4 Locked V5 falsifies prevalence-robust fixed disagreement allocation

Headline negative result:

- 180 conditions;
- 3 prevalences;
- 3 budgets;
- 8 policies;
- 4,800 windows x 200 replicates;
- only balanced prevalence / 25% budget met the full fixed-disagreement gate;
- rare 10/25% fell off the Pareto frontier and lost to single-view removal;
- common 25% had higher hidden-error recall under InsePi-only;
- low-budget TV could approach ~0.833;
- complementary signals nevertheless persisted across 6–7 disturbance families.

Conclude specifically that **the scalar allocation hypothesis failed**, not that
observer diversity failed.

### 3.5 V6 replaces ranking with an exploration-guarded portfolio

Show candidate-development path and why disagreement quota goes to zero.

### 3.6 High-resolution V6 development identifies the frozen candidate

Report E40/E50/E60/E70 focused comparison. Make the weak common-prevalence margin
visible rather than burying it.

### 3.7 Analytical exploration guarantees

This result is independent of the V7 performance outcome.

### 3.8 Locked V7

**Placeholder.** Insert the one-shot result without changing preceding sections.
End the subsection with the mechanically selected claim ceiling level.

## Discussion structure

### 4.1 The useful part of disagreement was diagnostic, not acquisitional

The most interesting result may be that keeping two views separate discovered why
a seemingly sensible disagreement allocation should be rejected.

### 4.2 Epistemic diversity differs from redundant ensemble diversity

Explain why the observers answer different questions and why majority vote would be
conceptually wrong.

### 4.3 Exploration is part of measurement design, not wasted budget

Connect the theorem to ecological preferential sampling and to denominator / absence
interpretation.

### 4.4 Falsification as a software-development method

Argue that method generations, frozen gates and preserved negative results reduce
benchmark overfitting in research software.

### 4.5 Generalisation beyond flower visitors

Potential domains:

- camera traps;
- nest monitoring;
- phenology cameras;
- feeding/interaction monitoring;
- acoustic event sensing;
- edge environmental anomaly monitoring.

Do not claim applicability without revalidation; describe architectural
transferability.

### 4.6 Limitations

Must include:

- simulation realism;
- observer-relative hidden-error endpoint;
- chosen disturbance families;
- simplified resource model;
- no field calibration yet;
- frozen weights may be task-specific;
- independent development does not imply statistically independent failures.

### 4.7 Empirical next step

Field data test the external validity of observers and the sampling/estimation
pipeline; they are not required to retroactively establish the simulation protocol.

## Main figures

### Figure 1 — From two observers to falsifiable development

Panel A: biological evidence vs observability axes.
Panel B: same pixels -> independent traces.
Panel C: contradiction types.
Panel D: V1->V7 generation timeline with V3/V5 failures retained.

### Figure 2 — V5 falsification surface

Heatmap/grid over prevalence x budget for fixed disagreement. Mark Pareto status,
failed gate components and TV distortion. This is the critical negative-result
figure.

### Figure 3 — Failure localisation at the allocation seam

Show complementary observer signal persisting while `allocation_score()` collapses
those signals into a prevalence-sensitive rank. This visually explains why the
observer hypothesis survives while the allocation hypothesis dies.

### Figure 4 — V6 exploration-guarded architecture and theorem

Diagram of `50% U + 10% P + 40% I`, with disagreement shown outside the allocation
path as a diagnostic channel. Beside it show the three analytical guarantees.

### Figure 5 — V6 high-resolution development comparison

Across E40/E50/E60/E70 show worst joint ratio, mean joint ratio and max TV; mark the
predefined gate and frozen E50 candidate.

### Figure 6 — V7 locked validation

One panel per prevalence, budget on x-axis, ratios to uniform, plus TV. Include
arm-removal and legacy baselines. Add claim-ceiling badge determined mechanically
from the hard gate.

## Supplementary figures/tables

- complete 180-condition V7 registry specification;
- V2/V4 same-pixel state matrices;
- family-level complementary-signal maps;
- all V5 policies/metrics;
- all V6 candidate weights tested;
- V7 observer-independent disturbance coverage metrics;
- provenance/hash ledger;
- full ablation table;
- selection-distribution plots;
- unit/CI test matrix.

## Main tables

### Table 1 — Observer contracts

Inputs, outputs, scientific question, failure mode, forbidden interpretation.

### Table 2 — Method generation ledger

Hypothesis, development data, frozen test, result, resulting method change.

### Table 3 — Locked criteria and claim consequences

Each hard V7 rule linked to the corresponding maximum claim level.

## Reproducibility statement

The paper should be reproducible from pinned source commits, byte-identical
simulated pixels, immutable emitted traces, deterministic seed derivation, explicit
scenario registries and one-command/CI report generation. V7 interpretation must
be downstream of report hashing.

## What must not appear as a claim

- “disagreement is the best acquisition strategy”;
- “the two observers fail independently”;
- “V6 is field-validated”;
- “hidden error is an observer-independent latent state”;
- “50/10/40 is universally optimal”;
- “simulation proves ecological visit-rate accuracy”.

## Submission decision after V7

Use `V7_CLAIM_CEILING.md` mechanically:

- Level A -> submit as exploration-guarded dual-observer sensing method;
- B/C -> submit as conditional/bias-control methodology if contribution remains
  sufficient;
- D -> recentre on contradiction-guided development;
- E -> recentre on locked benchmark/falsification.

The manuscript architecture is deliberately valid under all five outcomes, so V7
can remain a genuine one-shot test rather than a requirement to produce a positive
story.
