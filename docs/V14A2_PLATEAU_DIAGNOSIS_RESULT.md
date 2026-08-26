# V14a2 plateau failure-source diagnosis — locked first result

## Status

This is a post-result diagnosis of the already-locked V14a2 scientific sweep. It does not change the V14a2 phase surface, Q1/Q3 results, thresholds, feature definitions, or latent labels.

Source locked result:
- V14a2 first scientific sweep run `32921177706`;
- artifact digest `sha256:11c0409e163183395410271141928777310137711f74fee7e9e0f6e500e32b72`.

Diagnostic run:
- workflow run `32925820183`;
- execution commit `e8541f39ff26d947bd4e54cb998418fc6deb36d8`;
- artifact id `9591515114`;
- artifact digest `sha256:3a3db5ed530b67c947b9c63b8225d7874c39d3463ccf4cbc26b44df22c87e738`;
- CPython 3.11.16 / NumPy 2.4.6.

## Question

The locked V14a2 surface showed a broad weak-evidence target+nuisance ambiguity plateau. The four-way contradiction protocol requires deciding whether this residual is:

1. information absence;
2. essential ambiguity;
3. representation defect;
4. legitimate process coupling/superposition.

The audit therefore asks, at the same exact dimensionless coordinate, whether target presence is still recoverable from the frozen observed signature once nuisance is already present.

## Prefrozen interpretation rule

Before the diagnostic run:
- median held-out full-signature AUC >= 0.80 -> representation-defect candidate;
- median AUC <= 0.60 -> essential-ambiguity candidate;
- otherwise -> mixed boundary;
- nuisance-support AUC >= 0.90 with recall below 0.20 at the frozen 0.55 threshold -> nuisance score-scale mismatch.

No hyperparameter search was allowed. Train and held-out seeds were disjoint.

## Result 1 — target+nuisance superposition is not intrinsically unidentifiable

For nuisance-only vs target+nuisance-superposed:

- 450 eligible coordinates;
- median current target-support AUC = **0.64966**;
- target-support AUC 10–90% = **0.54487–0.82759**;
- median held-out full-signature ridge-LDA AUC = **1.00000**;
- 10–90% full-signature AUC = **1.00000–1.00000**;
- fraction of coordinates with full-signature AUC >= 0.80 = **1.000**.

Prefrozen classification: **representation defect candidate**.

Thus the broad plateau cannot be interpreted as evidence that target and nuisance are observationally inseparable in the generated measurement. The frozen signature still contains complete held-out separation under the diagnostic linear projection; the existing target-support representation fails to extract it.

## Result 2 — the same holds when target-driven coupling is present

For nuisance-only vs target+nuisance+coupling:

- 750 eligible coordinates;
- median current target-support AUC = **0.58691**;
- target-support AUC 10–90% = **0.50684–0.77842**;
- median held-out full-signature ridge-LDA AUC = **1.00000**;
- 10–90% full-signature AUC = **1.00000–1.00000**;
- fraction with AUC >= 0.80 = **1.000**.

Prefrozen classification: **representation defect candidate**.

Coupling therefore does not by itself explain the plateau as unavoidable ambiguity in this closed world.

## Result 3 — nuisance information is present but badly scaled

For nuisance-only vs target-only, using the existing nuisance-support score:

- held-out positive nuisance worlds = 43,200;
- held-out negative worlds = 43,200;
- pooled nuisance-support AUC = **1.00000**;
- recall at the frozen 0.55 threshold = **0.015625**;
- false-positive rate at 0.55 = **0.00000**.

This satisfies the prefrozen **nuisance score-scale mismatch** criterion.

The nuisance route ranks nuisance perfectly in this closed world, but almost all true nuisance scores sit below the operational positive threshold. Therefore the near-zero `both_supported_rate` in V14a2 is not absence of nuisance information; it is primarily a score-scale/decision representation mismatch.

## Four-way contradiction classification

The V14a2 weak-evidence superposition plateau is now classified as:

> **representation defect**, not information absence and not demonstrated essential ambiguity.

Legitimate T+N coexistence remains true at the latent-process level, but the observed signature contains sufficient information to distinguish target presence from nuisance-only worlds under this diagnostic. Therefore coexistence must not be used to explain away the classification failure.

## Development consequence

V14a2 remains immutable. The next development generation may modify the observation representation, but must obey alternating freeze:

1. freeze the nuisance observer and improve the target-side representation first;
2. validate on held-out coordinates/seeds, not the development cells;
3. then freeze the target observer and repair nuisance score calibration/representation;
4. stop by contradiction-type saturation, not by forcing the residual rate downward;
5. only after both observers are frozen may a new measurement generation estimate residual response surfaces.

The per-coordinate LDA used here is a diagnostic proof of information presence, **not** the proposed production target observer. A new target observer must preserve the direct/coupled evidence-route separation and must not consume the nuisance observer's output as a shortcut.

## Claim boundary

This result supports only a closed-world representation diagnosis. It does not establish field visit accuracy, does not show that every real superposition is separable, and does not authorize retrospective repair of V14a2.
