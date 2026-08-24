# V12 causal physical validation — design draft after V11 falsification

**Status: design-draft, not preregistered and not executable yet.**

V12 is not a tuned continuation of V11. V11 showed that raw separate observer outputs plus four high/low diagnostic states do not by themselves identify failure cause across mechanism shift. V12 therefore changes the *experimental source of identifiability*: causes are independently randomised before images are produced.

## Scientific question

When biological-event and observation-process causes are manipulated independently in the same visual stream, does keeping their observer outputs separate provide interpretable causal response contrasts that support correct event capture, observation audit and shared-failure diagnosis on fully held-out physical blocks?

The target is not a global winner score. The target is a response matrix with separately interpretable ecological and observation-process axes.

## Causal response matrix

For a block, let `Z_E` be the randomised event intervention and `Z_D` the randomised disturbance intervention. Let `E` be PolliPi biological-evidence output and `O` be InsePi observability-risk output.

Use the 2 × 2 factorial intervention to estimate:

```text
J = [ Δ_event E    Δ_disturbance E ]
    [ Δ_event O    Δ_disturbance O ]
```

where each main-effect contrast averages over the other factor. Also retain the event × disturbance interaction separately for both observers.

Expected controls are not assumed to be exact orthogonality. Instead:

- a functioning biological-evidence channel should have a reproducible positive own-response to `Z_E`;
- a functioning observability channel should have a reproducible positive own-response to `Z_D`;
- cross-responses are reported as effects, not discarded;
- a contradiction is a violation of a predeclared causal-response expectation, not simply a large numerical difference between `E` and `O`.

Examples:

- event intervention present, event-evidence response absent, disturbance-risk response stable → event-module blind-spot hypothesis;
- disturbance intervention present, disturbance-risk response absent while event evidence changes → observability blind-spot hypothesis;
- both own-responses collapse only under a common optical degradation → shared representation / observability boundary hypothesis;
- both outputs low without an intervention log → unresolved quiet-versus-shared-miss state, requiring protected random audit rather than inference from agreement.

## Physical causal bench

### Experimental unit

The unit of replication is a **physical clip/block**, never an individual video frame. Frames within a clip are repeated measurements of the same treatment unit.

A provisional clip structure is:

- 2 s untreated baseline;
- 8 s randomised treatment interval;
- 2 s recovery/context.

The exact duration is frozen only after a no-output engineering pilot confirms actuator timing and camera stability.

### Biological-event intervention

Use a preprogrammed insect-sized physical target passing through the focal flower/ROI on a motorised path. Its presence/absence, path id and start time are written by the controller before observer execution. The target is a **measurement proxy**, not evidence of field biological-identification accuracy.

A later locked field component uses real pollinator visits with blinded human annotation; the proxy bench cannot substitute for that external-validity step.

### Observation-process interventions

Interventions are physically generated and independently logged. Candidate families are:

1. fan-induced non-rigid vegetation/flower motion — latent wind-like disturbance;
2. camera vibration — global rigid displacement, independently logged by IMU;
3. controlled moving shadow / luminance attenuation — independently logged by light sensor or actuator state;
4. fixed-geometry partial occlusion — same position/shape, preregistered coverage tiers;
5. fixed-position glare — same lamp/angle/geometry, preregistered intensity tiers;
6. optical blur/focus degradation — preregistered optical setting.

External sensors or actuator logs are **truth channels only**. They are never inputs to PolliPi or InsePi.

For occlusion, glare and other spatial interventions, geometry is held fixed within a family while intensity alone changes whenever physically possible. This separates dose response from geometry changes.

## Randomisation and blocks

Treatments are randomised within `day × camera × background/scene` blocks.

Minimum factorial core per disturbance family and intensity:

```text
Z_E=0, Z_D=0
Z_E=1, Z_D=0
Z_E=0, Z_D=1
Z_E=1, Z_D=1
```

Treatment order is determined before observer output. The same raw clip is passed to every compared analysis strategy.

A complete **day and scene combination** is reserved before development as the locked physical test. No frame, clip or block from that test partition can be used to choose thresholds, nuisance features or diagnostic rules.

## Two independent truth streams

1. `event_truth`: physical event-controller log in the causal bench; blinded human annotation for real pollinator field clips.
2. `disturbance_truth`: treatment randomisation + actuator/sensor log.

Annotators for the field component must not see PolliPi/InsePi outputs or downstream diagnostic labels.

## Diagnostic strategies to compare

All strategies receive the same raw stream and identical truth access only at evaluation time.

### Event-only

Uses biological-evidence response only.

### Observability-only

Uses observation-risk response only.

### Early fusion

Uses a single preregistered scalar representation of the two outputs. If included, its formula must be fixed before the physical locked test.

### Causal separate-response diagnosis

Keeps `E` and `O` separate and interprets the preregistered factorial response contrasts and interactions. It does **not** use the V11 quadrant classifier and does not learn a post-result mapping from response pattern to cause.

### Protected random audit

A fixed probability sample of clips is audited independently of all observer scores. This estimates shared misses and provides the probability-sample ecological/reference denominator already supported by V9.

## Outcomes — no global winner score

Report a Pareto-style set of outcomes rather than collapsing them:

### Biological-event objective
- event recall / event enrichment at fixed capture budget;
- event false-capture rate;
- event own-response contrast `Δ_event E`.

### Observation-process objective
- disturbance recall / audit enrichment at fixed audit budget;
- disturbance false-audit rate;
- observability own-response contrast `Δ_disturbance O`.

### Diagnostic objective
- correct causal intervention selection;
- event-module miss localisation;
- observability-module miss localisation;
- shared-failure detection;
- no-fault false intervention.

### Sampling/inference objective
- protected-audit inclusion probability;
- source/block representation distortion;
- design-based interval coverage for quantities estimated from the protected probability sample.

## Analysis scale

Inferential uncertainty is computed at the randomised clip/block level with block effects for day/camera/scene. Do not treat frames as independent replicates.

Effect sizes and uncertainty are primary. The question is whether causal response contrasts transfer across held-out physical blocks, not whether a very large number of frames produces small p-values.

## Lock sequence

1. engineering pilot checks only hardware timing, file integrity and intervention non-degeneracy;
2. V11 failure audit is completed and frozen as descriptive history;
3. exact physical families, dose tiers, clip duration, block counts and actuator logs are fixed;
4. analysis code and causal-response rules are frozen;
5. a complete day/scene test partition is sealed;
6. development/calibration blocks are run;
7. no rule change is allowed;
8. locked test blocks are executed once;
9. all favourable, null and adverse outcomes are preserved.

## Existing evidence this design must not overwrite

- V5: fixed scalar disagreement allocation failed;
- V7: frozen 50/10/40 allocation failed locked validation (claim C);
- V11: naive contradiction-state localisation failed (claim D);
- V9: protected random exploration retained design-valid ecological inference in its frozen finite-population study;
- V10: separate real-pixel perturbation-transfer generation, not a source of biological-event truth.

## MEE-facing rationale

This structure follows current ecological-method guidance that simulation studies should be planned and transparently reported as controlled experiments, and that causal experimental claims require controls, replication and randomisation. It also aligns with adaptive-sampling work stressing that targeted data collection and inferential validity are distinct design problems.

Relevant method-design anchors include Williams et al. (2024, *Methods in Ecology and Evolution*, DOI `10.1111/2041-210X.14415`), Popovic et al. (2024, DOI `10.1111/2041-210X.14270`), Henrys et al. (2024, DOI `10.1111/2041-210X.14393`) and camera-trap quality-control guidance by Silva-Rodríguez et al. (2025, DOI `10.1111/1365-2664.70010`).

## Current boundary

This file is intentionally a design draft. It is not yet a V12 preregistration and must not be used to claim that contradiction-guided development works. The frozen V11 failure audit should determine which diagnostic ambiguities must be explicitly resolved before this draft is promoted to a locked protocol.
