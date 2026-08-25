# V14: target, nuisance, observability, and the measurable undecidable region

## Central proposition

The purpose of the discrimination system is not to force every deviation across a binary boundary. It is to localise and measure the region in which the boundary is not supported by the observation.

Ignorance is therefore an output, not automatically a software failure.

The ecological application remains visitation sensing, but the framework is written first as a general observation model and only then instantiated for insect visits.

## 1. Three logical layers

The framework must not place `target`, `nuisance`, and `unobservable` in one exclusive ontology. Doing so would contradict the fact that target and nuisance can coexist.

### 1.1 Generative world

A world is either a baseline or a deviation.

```text
baseline
  no deviation; no discrimination question is triggered

deviation
  target process: absent / present
  nuisance process: absent / present
  coupling: absent / present or continuous strength
```

Target and nuisance are positively defined latent processes and are **not mutually exclusive**.

The coupled state is scientifically important. It is not an error state. A visit can itself move the flower or scene and therefore generate a process that resembles the nuisance channel.

### 1.2 Observation / information layer

Observability asks a counterfactual question:

> If a target event occurred in this window, did the measurement contain enough information to support a defensible presence/absence statement?

Observability is not `1 - nuisance`.

Examples:

- strong wind can coexist with a clearly visible large insect: high nuisance, still observable;
- a quiet scene can have the interaction zone hidden behind a leaf: low nuisance, unobservable;
- a tiny insect can be directly unresolved but induce a focal-flower response that provides an indirect route to target evidence.

### 1.3 Inferential output

The downstream ecological result remains three-valued:

```text
PRESENT
ABSENT
UNDETERMINED
```

Internal diagnostics remain richer and retain target support, nuisance support, coupling evidence, observability support, and the reason for indeterminacy.

A coupled target+nuisance world may still yield `PRESENT` when target support is adequate. Coupling must not be forced into `UNDETERMINED` merely because both channels are active.

## 2. Three distinct reasons for UNDETERMINED

They must never be merged during development.

### 2.1 Information absent

The measurement channel did not contain enough evidence to determine the target state. Examples are an insufficient observation window, unresolved spatial scale, total occlusion, or another hard measurement limitation.

This is not repaired by making the classifier more confident.

### 2.2 Essential ambiguity

The observation contains evidence, but two or more causal/process hypotheses remain observationally indistinguishable under the available window and sufficient statistics.

The primary quantity should be a continuous **identifiability margin**. A categorical ambiguity threshold is a downstream operational decision, not a claim that nature contains a sharp boundary.

### 2.3 Model uncertainty

The observation is in principle informative, but the current representation/classifier cannot exploit that information reliably.

This is the category that can legitimately motivate model improvement or active learning.

## 3. Contradiction taxonomy

Contradiction is classified before intervention.

| Cause | Action |
|---|---|
| definition defect | revise the definition; do not tune the observer to preserve the old definition |
| representation defect | improve the relevant observer while freezing the other observer |
| information absent | do not guess; preserve `UNDETERMINED` and route the limitation to sensor/window design |
| process coupling | do not force agreement; target and nuisance may both be true |

The last two rows are the methodological core. A system that tries to predict labels for observations containing no discriminating information will fill the gap with learned prior structure rather than evidence from the current observation.

## 4. Alternating frozen development

The target-focused and nuisance-focused systems must not be allowed to co-adapt continuously on the same contradictions.

Recommended cycle:

```text
freeze nuisance observer
  -> expose target-observer failures
  -> revise target representation only

freeze target observer
  -> expose nuisance-observer failures
  -> revise nuisance representation only

repeat until contradiction *types* saturate
```

The stop rule is saturation of contradiction classes, not zero contradiction rate.

A continuously falling residual rate after apparent type saturation is a warning that ambiguous observations may be getting absorbed into one positive class.

## 5. Dimensionless visitation world

Absolute seconds, pixels, wind speed, or insect size are intentionally excluded from V14a.

The target-process timescale is the reference unit.

- `Pi1 = observation-window duration / target-process timescale`
- `Pi2 = nuisance/flower-response timescale / target-process timescale`
- `Pi3 = direct-target motion amplitude / nuisance-motion amplitude`
- `Pi4 = target-driven local response amplitude / nuisance-motion amplitude`

The first broad sweep uses logarithmic values from `10^-2` to `10^2`.

Later empirical measurements do not define this response surface. They locate a physical deployment on an already-defined surface.

## 6. Visitation process definitions

### 6.1 Target process

A visit is modelled as a localised, non-stationary transit with an entry and exit on the target timescale.

The direct target channel represents insect-like local motion.

### 6.2 Nuisance process

The first closed-world nuisance family is a restorative, spatially coherent scene process. It captures the process type of wind-driven/background motion without defining nuisance by an endless list of causes.

Harmless static non-target context is baseline context, not nuisance.

### 6.3 Coupling

A target event may drive a local flower/scene response. The focal location receives this response; neighbouring locations receive the coherent nuisance process but not target-triggered coupling.

This creates a second possible route to target evidence:

> weak direct insect evidence + strong focal-only target-driven response.

V14 explicitly measures whether a rescue region exists in the `Pi3 × Pi4` plane.

## 7. Sufficient-statistic family

Features are derived from process definitions rather than collected opportunistically.

The V14a process signatures include:

- net displacement / path length: restoration versus transit;
- focal-neighbour motion correlation: global coherence versus local excess;
- normalised autocorrelation / spectral concentration: stationarity or oscillatory structure;
- entry/exit completeness: transient structure;
- local excess-motion fraction: focal response beyond shared scene motion;
- direct target-signal fraction: strength of the direct local actor route.

All are ratios, correlations, logical events, or normalised spectral summaries.

## 8. Pre-sweep predictions

These are predictions, not truths embedded into the labels.

1. decreasing `Pi1` should increase information absence;
2. decreasing `Pi3` should weaken the direct target route;
3. `Pi2 ≈ 1` should thicken the essential-ambiguity region **only where other separating evidence is weak**;
4. increasing `Pi4` should create an indirect-rescue region at low `Pi3`;
5. increasing `Pi4` should also increase legitimate target+nuisance both-supported states.

If the predicted qualitative transitions do not appear, the process generator or the chosen sufficient statistics are themselves falsified and should be revised in a new development generation.

## 9. Closed-world / open-world loop

V14a begins in a closed world because structural ambiguity can only be evaluated against a generator whose latent processes are known.

Open-world data have a different role:

```text
closed world
  -> establish lower-bound process vocabulary and phase geometry
open world
  -> discover missing process vocabulary
return to closed world
  -> encode the new process with truth-known generation
```

Real backgrounds or degradation can later be combined with synthetic target truth to import realistic failure texture without abandoning known latent truth.

## 10. Development and measurement phases

### V14a — world/phase-map infrastructure

Freeze the dimensionless closed-world generator, sufficient-statistic family, and phase coordinates. Do not optimise PolliPi or InsePi against the resulting surface.

### V14b — contradiction-guided alternating development

Use the phase map to deliberately sample predicted break regions. Freeze one observer while changing the other. Every contradiction is entered into the four-way cause ledger.

### V14c — frozen measurement

When contradiction *types* saturate, freeze both observers. Then estimate:

- `R_undetermined(Pi1,Pi2,Pi3,Pi4)`;
- information-absence surface;
- essential-ambiguity surface;
- both-supported/coupled surface;
- indirect-rescue surface.

The residual is now a measurement. Its size is not a development score to minimise.

## 11. Final visitation-study connection

For ecological visit-frequency estimation:

- `PRESENT` contributes a detected visit;
- `ABSENT` contributes observed effort only when absence is interpretable;
- `UNDETERMINED` is carried forward as censored/missing observation effort with its reason code.

The rate of `UNDETERMINED` becomes an estimand itself as a function of observation conditions.

The final method is therefore stronger than a detector that simply labels insects versus everything else. It separates:

1. evidence for the focal insect/visit process;
2. evidence for nuisance processes that can corrupt that inference;
3. whether the target state was observable at all;
4. whether the two physical processes were genuinely coupled;
5. whether remaining uncertainty is structural or merely model-limited.
