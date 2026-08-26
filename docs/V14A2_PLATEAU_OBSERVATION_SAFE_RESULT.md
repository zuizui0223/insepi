# V14a2 corrected plateau diagnosis — observation-safe result

## Status

This document supersedes the **target-separability interpretation** of the first plateau audit while retaining that failed audit for provenance. The locked V14a2 scientific surface and its negative Q1/Q3 results remain unchanged.

Corrected run:
- workflow `32926639089`;
- execution commit `74eb7aadc2d4b84b771baf9e4ed5a540da94cf47`;
- artifact id `9591792694`;
- artifact digest `sha256:52d7c2602db0eecf826d760cf760ac868c86e02032fbbfe53b469d217fb48075`;
- CPython 3.11.16 / NumPy 2.4.6.

## Correction

The first audit's full 12-feature signature contained two latent-topology quantities:
- `entry_exit_completeness` from target truth and the known event window;
- `net_displacement_over_path_length` from the ideal actor trajectory.

The corrected audit keeps the same exact Pi coordinates, train/held-out seeds, ridge-LDA rule, and AUC decision thresholds, but uses only observation-safe fields:

1. focal-reference correlation;
2. spatial coherence;
3. spatial structure function;
4. restoration score;
5. spectral concentration;
6. local excess motion fraction;
7. direct target signal fraction.

## Result A — direct-visible T+N superposition is a representation problem

For nuisance-only vs target+nuisance-superposed:
- 450 coordinates;
- median direct-signal AUC = **1.000**;
- direct-signal AUC 10–90% = **1.000–1.000**;
- median observation-safe LDA AUC = **1.000**;
- 10–90% observation-safe LDA AUC = **1.000–1.000**;
- fraction with AUC >= 0.80 = **1.000**.

The prefrozen classification remains **representation-defect candidate**, now without latent-topology leakage.

This matters because the existing V14a2 target route performs worse than the raw direct evidence itself. The failure is therefore not lack of target information in these eligible direct-visible cells; it is the way target evidence is combined/represented downstream.

## Result B — coupling is heterogeneous, with one exact indirect-only failure type

For nuisance-only vs target+nuisance+coupling:
- 750 coordinates;
- median direct-signal AUC = **1.000**;
- median observation-safe LDA AUC = **1.000**;
- 10th percentile observation-safe LDA AUC = **0.5117**;
- fraction with AUC >= 0.80 = **0.800**.

The low-separability 20% are not diffuse. They are exactly the **150 coordinates with `Pi3=0` and `Pi4=0.316227766...`**, i.e. target inference relies entirely on the indirect local-response route.

For this indirect-only subset:
- mean observation-safe LDA AUC = **~0.5081**;
- all 150 coordinates have AUC <= 0.60;
- mean AUC varies only weakly across `Pi1` (~0.020 range), `Pi2` (~0.015), `Pi5` (~0.005), and `Pi6` (~0.015).

Thus the remaining ambiguity is **not a Pi2≈1 collision band and not a Pi5 spatial-scale transition**. It is tied to the absence of direct target evidence.

Under the prefrozen diagnostic rule, this is an **essential-ambiguity candidate under the current observation-safe sufficient-statistic family**. It must not be 'fixed' merely to reduce the residual rate.

## Result C — nuisance score scale mismatch remains valid

The nuisance calibration result reproduces exactly:
- pooled nuisance-support AUC = **1.000**;
- recall at frozen threshold 0.55 = **0.015625**;
- false-positive rate = **0.000**.

The nuisance observer therefore contains strong ranking information but its operational scale is badly mismatched to the frozen threshold.

## Revised contradiction map

The broad V14a2 plateau is not one homogeneous failure type.

### Direct-visible T+N cells
**Representation defect candidate.**

Target information is present and even the direct signal alone separates target+nuisance from nuisance-only in the eligible slice. Development may improve the target observer while freezing nuisance.

### Indirect-only target+nuisance+coupling cells (`Pi3=0`)
**Essential-ambiguity candidate under current observation-safe statistics.**

Do not force a target label. These cells remain `UNDETERMINED` unless a genuinely new, independently justified attribution channel is introduced in a later definition/representation generation.

### Nuisance score
**Representation / calibration-scale defect.**

Repair only after the target-side development step is frozen, following the alternating-observer rule.

## Development consequence

The next target-observer generation should **not** import the per-coordinate LDA as a production classifier. It should make the smallest process-consistent correction:

1. preserve direct target evidence as an independent positive route;
2. do not let an ambiguous indirect local-response score overwrite or contaminate direct evidence;
3. treat indirect-only local response as unresolved without an independent target-link signal;
4. freeze the nuisance observer during this step;
5. validate on held-out coordinate/seed strata;
6. stop by contradiction-type saturation rather than by driving `UNDETERMINED` toward zero.

Only after that target-side representation is frozen should nuisance score scaling be repaired with target held fixed.

## Claim boundary

This is a closed-world process/representation diagnosis. It does not establish field visit accuracy, does not prove that all real indirect-only events are undecidable, and does not authorize retrospective changes to V14a2.
