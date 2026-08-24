# V12 pre-result freeze — controlled causal intervention development

## Question

V11 failed to localise hidden failure causes from static observer outputs and thresholded contradiction states. V12 does not tune V11. It asks a different question:

> If the experiment actively perturbs one causal path at a time, does retaining the two observer responses separately improve failure identification across mechanism-subtype shift?

The object of evaluation is a **development experiment**, not a sensing-allocation score.

## Historical boundary

The following outcomes are retained unchanged:

- V7 locked allocation validation: **FAIL / claim C**;
- V11 static contradiction-state localisation: **FAIL / claim D**;
- V11 canonical result SHA-256: `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`;
- V6 50/10/40/0 weights are unchanged;
- V10 source, pixels and scientific protocol are unchanged.

V12 cannot rescue or reinterpret V7 or V11.

## Causal intervention design

Every episode has one latent failure class:

1. `event_module`;
2. `observability_module`;
3. `shared_representation`;
4. `no_fault`.

Development and held-out evaluation use different mechanism subtypes. The causal topology is preserved, but held-out response magnitudes use a different intensity transformation (`sqrt(intensity)` rather than `intensity`) and different response coefficients.

A mandatory placebo establishes the paired response reference. It does not count against the active intervention budget. The three active interventions are:

- `event_restore`;
- `observability_restore`;
- `shared_restore`.

All strategies may use at most **two active interventions** for the primary diagnosis. A three-intervention full battery is reported only as an identifiability ceiling.

## Four compared representations

The diagnostic algorithm is identical across strategies. Only the representation of each paired intervention response differs:

- event-only: `delta_evidence`;
- observability-only: `delta_observability`;
- early scalar fusion: `0.5*delta_evidence + 0.5*delta_observability`;
- interventional dual observer: the raw two-vector `(delta_evidence, delta_observability)`.

V12 deliberately contains **no quadrant one-hot expansion, disagreement score, or duplicated E/O-derived features**.

## Common experiment-selection algorithm

For each representation:

1. fit class-conditional intervention-response centroids using development subtypes only;
2. standardise response dimensions from development data only;
3. choose the first intervention by maximum minimum pairwise class-centroid separation;
4. after observing that paired response, rank failure hypotheses by centroid distance;
5. take the two nearest hypotheses and choose the remaining intervention that maximally separates those two development centroids;
6. diagnose by nearest centroid after two active interventions;
7. evaluate all-three-intervention diagnosis as a secondary full-battery ceiling.

All tie breaking is lexical and fixed. No hyperparameter search is permitted.

## Protected random audit

A strategy-independent hash assignment audits 25% of episodes. The audit reveals only `fault_present` versus `no_fault`; it never reveals the causal failure class. The same audit assignment is available to all four strategies before intervention selection.

This keeps the role of protected random audit distinct from causal localisation: it can prevent needless repair in a checked no-fault episode but cannot tell the method which module failed.

## Simulation freeze

- intensities: `0.35`, `0.65`, `0.95`;
- development: 300 replicates per class × intensity = 3,600 episodes;
- held-out: 300 replicates per class × intensity = 3,600 episodes;
- paired response noise SD: `0.045`;
- channel-noise correlation: `0.25`;
- runtime target: CPython 3.11.16 / NumPy 2.4.6;
- two executions under distinct `PYTHONHASHSEED` values must be byte-identical.

## Primary outcomes

- held-out localisation after two active interventions;
- full-battery localisation;
- shared-representation recall;
- no-fault false intervention;
- wrong-module intervention;
- interventions to stable correct diagnosis;
- independent held-out repair positive-transfer rate;
- relative repair-loss reduction.

The repair test uses an independent seed domain and is downstream of diagnosis.

## Claim ceiling

The A/B/C/D claim mapping is frozen in `benchmarks/v12_causal_intervention_protocol.json`. A strong claim requires the dual-channel representation to beat the best comparator by at least 0.10 after two interventions, not merely to perform well in absolute terms.

## Forbidden post-result moves

Under V12, do not:

- alter causal response coefficients;
- change intervention budget or candidate set;
- add quadrant/disagreement-derived features;
- tune centroid distance or selection criteria;
- change audit fraction;
- alter claim thresholds;
- reinterpret V7 or V11;
- call synthetic interventions a substitute for blinded physical intervention blocks.

Any redesign after the first V12 result requires a new generation.
