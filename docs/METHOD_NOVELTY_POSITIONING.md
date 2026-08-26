# Method novelty positioning — what this is, and what it is not

This note fixes the conceptual neighbourhood of the pre-empirical methods paper.
The individual ingredients have substantial prior art. The candidate contribution
is their specific combination and falsification-driven development logic for
finite-budget ecological sensing.

## 1. Not query-by-committee active learning

Query by Committee (QBC) selects new labels where a committee of learners disagrees
most strongly. The classic formulation explicitly uses maximal committee
disagreement as the query principle (Seung, Opper & Sompolinsky 1992,
DOI:10.1145/130385.130417). Modern QBC work continues to refine disagreement
acquisition functions, for example using robust divergences (Hino & Eguchi 2022,
DOI:10.1007/s41884-022-00081-x).

Our development initially approached that logic, then **falsified it**. Locked V5
showed that a fixed scalar disagreement ranking was not robust to event-prevalence
shift and could strongly distort the sampled disturbance distribution. V6
therefore assigns **zero direct disagreement quota**.

The distinction is central:

```text
QBC:
model disagreement -> acquisition priority

V6/V7 method:
observer disagreement -> falsification / failure localisation
independent observer outputs + guaranteed exploration -> allocation
```

The paper must not sell V6 as a novel disagreement acquisition function. Its result
is almost the opposite: disagreement was useful enough to discover that direct
disagreement acquisition should be removed from the final policy.

## 2. Not N-version programming or majority voting

N-version programming independently develops multiple functionally equivalent
programs, executes them in parallel, and typically reconciles outputs by voting or
another consensus mechanism. Classic experiments also showed that independently
developed software failures cannot safely be assumed statistically independent
(Knight & Leveson 1986, IEEE Transactions on Software Engineering,
DOI:10.1109/TSE.1986.6312924).

PolliPi and InsePi are intentionally **not functionally equivalent versions** of the
same specification:

- PolliPi asks for biological-event evidence / capture value;
- InsePi asks whether the observation process is trustworthy and what error mode is
  plausible.

There is no majority vote. One observer is not treated as a replica of the other.
Their non-equivalence is preserved because it produces complementary failure
information.

This also means V7 should not claim statistical independence of observer failures.
Complementarity is measured empirically by disturbance family and ablation, not
assumed from independent development.

## 3. Related to differential testing, but the discrepancy is not itself a bug

Differential testing feeds the same input to multiple implementations and treats
output discrepancies as potential semantic bugs. The development programme here
shares the same-input comparison principle.

The difference is that PolliPi/InsePi disagreement may be **legitimate** because the
programs answer different observation questions. A discrepancy is therefore typed
as evidence about representation, objective, policy, temporal or epistemic
conflict, then tested against latent simulation truth.

The workflow is closer to:

```text
same input
-> intentionally different epistemic observers
-> structured contradiction
-> falsification / failure localisation
-> revise policy family
-> new locked validation generation
```

rather than cross-implementation equality checking.

## 4. Directly connected to preferential/adaptive sampling bias in ecology

Ecological monitoring literature has repeatedly shown that preferential site or
effort selection can bias status, trend and spatial inference. Examples include
Gelfand, Sahu & Holland (2012) on preferential sampling in spatial prediction,
Conn et al. (2017) on preferential sampling in population distributions,
McClure et al. (2023) on site-selection bias in population monitoring, and a 2024
Ecological Modelling study showing that preferential sampling can bias population
mean estimation and that bias depends on the covariance between sample inclusion
and the process of interest.

Recent work also develops adaptive ecological monitoring designs explicitly from
biased prior data (Pescott 2025, Oikos, DOI:10.1002/oik.11115).

V6 contributes at a different layer: within an autonomous sensing stream, targeted
capture itself creates a selection process over observation conditions. V5 made
that problem visible as large disturbance-distribution TV under fixed ranking.
V6 therefore makes uniform exploration structural rather than treating unbiased
coverage as an afterthought.

For exploration share `alpha`, the expected selected-condition distribution obeys

```text
Q = alpha U + (1-alpha) R
TV(Q,U) <= 1-alpha,
```

so targeted sensing receives an explicit distortion bound. This is a bridge from
preferential-sampling concerns to edge sensing policy design.

## 5. Distinct from camera-trap active learning

Active learning has been applied to camera-trap image labelling/detector training,
including uncertainty/diversity selection of informative images. That problem asks
which existing observations should receive labels or enter training.

The current method asks a different question:

> Under a finite future sensing/audit budget, which moments should receive extra
> observation effort when biological evidence and observation-process risk are
> distinct signals?

The target is the **observation stream and its sampling distribution**, not only
training-set efficiency.

## 6. Candidate contribution if V7 passes

A defensible strong contribution would be the combination of:

1. **epistemic design diversity**: maintain biological-evidence and
   observability-risk observers as non-equivalent programs;
2. **contradiction-guided development**: use their conflicts to localise failure
   seams instead of immediately merging or voting;
3. **generational falsification**: preserve negative locked results (V3, V5) and
   change the policy class rather than tune the failed test;
4. **exploration-guarded allocation**: combine independent observer quotas with a
   guaranteed prevalence-agnostic exploration floor;
5. **selection-bias accounting**: evaluate both recovery and distortion, with an
   analytical TV bound from the exploration mixture;
6. **canonical same-pixel validation**: both observers receive byte-identical
   materialised inputs and are evaluated only after independent trace emission;
7. **claim-ceiling preregistration**: validation failure automatically narrows the
   paper claim rather than initiating same-generation retuning.

The novelty claim should be about this methodology/architecture, not about any one
threshold, disturbance detector, disagreement formula, or portfolio weight.

## 7. If V7 fails

The novelty does not disappear automatically. The paper can move down the frozen
claim ceiling:

- allocation success -> exploration-guarded dual-observer sensing method;
- allocation failure but bias control -> safe-exploration result;
- allocation failure but repeatable contradictions -> contradiction-guided
  development methodology;
- broad failure -> locked benchmark/falsification paper.

This is important because the scientific object is the sequence of hypotheses and
falsification boundaries, not a requirement that the initial disagreement idea win.

## Reference anchors for manuscript drafting

- Seung HS, Opper M, Sompolinsky H. 1992. Query by Committee. COLT.
  DOI:10.1145/130385.130417.
- Knight JC, Leveson NG. 1986. An experimental evaluation of the assumption of
  independence in multiversion programming. IEEE TSE. DOI:10.1109/TSE.1986.6312924.
- Hino H, Eguchi S. 2022. Active learning by query by committee with robust
  divergences. Information Geometry. DOI:10.1007/s41884-022-00081-x.
- Gelfand AE, Sahu SK, Holland DM. 2012. On the Effect of Preferential Sampling in
  Spatial Prediction.
- Conn PB et al. 2017. Confronting preferential sampling when analysing population
  distributions: diagnosis and model-based triage. Methods in Ecology and
  Evolution. DOI:10.1111/2041-210X.12803.
- McClure CJW et al. 2023. Pitfalls arising from site selection bias in population
  monitoring defy simple heuristics. Methods in Ecology and Evolution.
  DOI:10.1111/2041-210X.14120.
- Pescott OL. 2025. Adaptive sampling for ecological monitoring using biased data:
  a stratum-based approach. Oikos. DOI:10.1002/oik.11115.

Before manuscript submission, bibliographic metadata should be checked against the
publisher/Crossref records and expanded to the final reference style.
