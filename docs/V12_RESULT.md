# V12 result — causal interventions recover identifiability conditionally

## Locked outcome

Canonical first run: `32702686586`  
Protocol SHA-256: `50c26e86af83e460f244c8c3b5a89bc6f62914fb043a9ff0f2738161c92935b8`  
Result SHA-256: `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`  
Artifact ZIP SHA-256: `bc34a59f298e13da36fc3d2d1333c638ce0ac5f5af274197af777247095c7d50`

The preregistered claim level is **B — conditional causal-identification advantage**.

Two full runs under `PYTHONHASHSEED=12` and `1201` were byte-identical. All 19 pre-result contract tests passed before result generation.

## Main comparison

| Representation | 2-intervention localisation | Full battery | Shared recall | Wrong module | No-fault false intervention | 1-intervention accuracy | Stable interventions | Repair+ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **dual E/O** | **0.9858** | **0.9947** | 0.9722 | **0.0159** | 0.0089 | **0.9608** | **1.0108** | **0.9963** |
| early scalar fusion | 0.9658 | 0.9911 | 0.9311 | 0.0433 | **0.0067** | 0.7367 | 1.2614 | 0.9896 |
| event-only | 0.8767 | 0.8731 | 0.9767 | 0.0885 | 0.2278 | 0.7653 | 1.5328 | 0.9663 |
| observability-only | 0.8772 | 0.8747 | **0.9778** | 0.0867 | 0.2311 | 0.7794 | 1.5108 | 0.9611 |

## Why this is claim B, not A

The dual representation was the best overall after the same two-intervention budget, but its final localisation advantage over early scalar fusion was only about **+0.020**, below the preregistered **+0.10** margin required for claim A.

Therefore V12 does **not** support a strong claim that preserving two channels is universally necessary for final diagnosis once sufficiently informative causal interventions are available.

## Where separate channels mattered most

The clearest advantage was **diagnostic efficiency** rather than the final full-battery ceiling.

After only one active intervention:

- dual E/O: **0.9608**;
- observability-only: 0.7794;
- event-only: 0.7653;
- early scalar fusion: 0.7367.

The dual representation also reached stable correct diagnosis in about **1.01 active interventions** on average, versus 1.26 for early fusion and about 1.5 for the single-channel strategies.

This matches the intended methodological interpretation: preserving the response vector can help decide *what experiment to do next* and can avoid wrong-module repair, even when a scalar summary eventually catches up after more interventions.

## Failure-class detail

Dual E/O class accuracy after two active interventions:

- event module: **0.9856**;
- observability module: **0.9944**;
- shared representation: **0.9722**;
- no fault: **0.9911**.

This is not driven solely by protected random audit. Dual accuracy was **0.9943** among audited episodes and **0.9831** among unaudited episodes.

## Intervention pattern

For the dual strategy, the development-centroid maximin rule selected `shared_restore` as the first causal probe for all non-audit-stopped held-out episodes. The second intervention was then chosen adaptively between:

- `event_restore`: 1,394 episodes;
- `observability_restore`: 1,984 episodes.

This is consistent with the fixed design: the broad shared intervention first tests whether the failure couples both channels, and the second probe discriminates the two remaining module-specific hypotheses.

## Scientific interpretation

V11 showed that static disagreement/quadrant patterns did not make causal failure class identifiable under subtype shift. V12 shows that **changing the experiment** can restore identifiability without retuning V11:

1. intervene on a defined causal path;
2. compare the paired observer response to its placebo reference;
3. retain E and O separately long enough to select the next discriminating intervention;
4. use protected audit independently to guard against unnecessary action in no-fault cases.

The result therefore supports a narrower version of contradiction-guided development:

> disagreement is not itself a diagnosis; it is useful when it motivates a controlled intervention whose response can discriminate competing failure hypotheses.

## Boundaries

V12 remains synthetic and topology-controlled. Its strong accuracy cannot be interpreted as field failure-localisation accuracy. The response topology was fixed before the first run and is a proof-of-identifiability setting, not a physical validation.

The next decisive test should use **blinded physical intervention blocks on the same video stream**, with event state and observation disturbance manipulated or annotated independently. V12 must not be retuned before that test.

Historical results remain unchanged:

- V7: **FAIL / C**;
- V11: **FAIL / D**;
- V12: **B**, conditional causal-identification advantage.
