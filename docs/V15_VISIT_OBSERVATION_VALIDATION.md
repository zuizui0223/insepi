# V15 — Real visit-observation validation design

## Goal

V14 rejects `insect = signal / everything else = noise` and separates four things that matter for visit observation:

1. **direct target evidence** — evidence for the insect/actor itself;
2. **target-coupled response** — a local flower/target response causally attributable to the insect interaction;
3. **exogenous nuisance risk** — non-target processes that can mimic, hide, or misattribute the event;
4. **observation support** — whether the primary interaction opportunity was measurable well enough that presence/absence can be interpreted.

The second item is essential. Flower movement is not automatically nuisance. Wind-driven flower motion is exogenous nuisance; insect-driven flower response is an indirect target route. V15 is designed to distinguish them with independent truth rather than by relabelling whichever signal helps the detector.

The central ecological error to prevent remains:

```text
low target evidence -> biological absence
```

when the correct interpretation may be:

```text
weak direct insect evidence
+ target-coupled flower response -> indirect visit evidence
```

or

```text
low target evidence
+ poor observation support -> censored / unknown
```

## Two observation channels are required for validation

The **primary stream** is the stream under test and is the only image stream available to the target/nuisance/observability algorithms.

A separate synchronised **reference truth stream** is required for biological validation. It may be a higher-quality/wider-angle reference camera, direct human observation, or another independently justified observation channel. It is used only to establish truth and is never supplied to the algorithms under test.

This separation is essential. If the primary stream is truly `unobservable`, a human inspecting that same stream cannot establish that a hidden visit did or did not occur. Without an independent truth channel, false absence under unobservability is logically untestable.

If the reference truth stream also cannot resolve the biological state, the window is labelled `truth_unresolved`. It is **not** relabelled `no_insect`. Such windows are excluded from biological-accuracy denominators but retained when evaluating the primary stream's observability/support gate and recording burden.

## Four independent truth layers

### 1. Biological-event truth

Reference-channel reviewers annotate:

- `no_insect`;
- `insect_in_context`;
- `target_contact`;
- `visit_event`;
- or `truth_unresolved` when the reference channel itself is insufficient.

A `visit_event` is an observed insect interaction with the focal floral target. It does **not** by itself establish pollen transfer or pollination effectiveness.

### 2. Target-coupled response truth

Reference-channel reviewers separately annotate whether a local response of the focal flower/target can be causally attributed to the insect interaction.

The coupling label is:

- `present`;
- `absent`;
- or `unresolved` when causal attribution cannot be supported.

A resolved `present` label requires resolved `target_contact` or `visit_event` biological truth. If the flower moved but the reference channel cannot establish that the insect caused it, coupling remains unresolved rather than being upgraded to target evidence.

This truth layer directly tests the V14 prediction:

```text
weak direct insect signal + target-linked local response -> possible indirect visit rescue
```

### 3. Exogenous nuisance truth

Nuisance is multi-label and excludes target-driven coupling by definition. Reviewers or physical logs record whether a non-target process can:

- mimic the target;
- mask the target;
- corrupt attribution;
- degrade observation support.

Wind-driven target motion, camera shake, moving shadow, occlusion, blur and similar processes may therefore be nuisance. A flower response caused by an insect contact is not moved into this category simply because its pixel signature resembles motion noise.

### 4. Primary-stream observation-support truth

A separate annotation of the **primary stream** asks:

> If a visit occurred in the focal interaction zone during this window, was the primary camera stream sufficient to observe it?

The label is `observable`, `compromised`, or `unobservable` and must not be inferred from target/nuisance outputs or from the biological label. A primary-stream window may therefore be unobservable while the independent reference stream still resolves a true visit.

## Why all four truths must be separate

The system must permit all of the following:

- true visit + no target-coupled response;
- true visit + target-coupled response;
- true visit + exogenous nuisance;
- target-coupled response + exogenous nuisance simultaneously;
- strong nuisance while the visit remains observable;
- quiet scene while the visit opportunity is unobservable;
- unresolved reference biological truth while primary-stream observability remains measurable.

The validation cannot define one layer from another without circularity.

## Target-side routes under test

### Direct route

Evidence for the insect/actor itself: visible transit, local actor motion or other target-focused signal.

### Coupled route

Evidence for a local response at the focal biological target. The operational coupled score is retained separately from the direct route and requires target-link evidence. It is not computed from InsePi nuisance output.

### Aggregate target evidence

The acquisition/runtime layer may combine direct and coupled target routes, but V15 preserves both component scores in the prediction ledger. This permits two opposite evaluations:

- **indirect rescue:** true visit, observable opportunity, resolved coupled response, weak direct route, strong coupled route;
- **spurious rescue:** resolved no-insect truth but strong coupled route causes a retained candidate.

The method is successful only if rescue is gained without uncontrolled spurious coupling calls.

## Experimental unit and split

Frames are never treated as independent replicates. Primary grouping is at least:

```text
recording day × focal flower/scene × recording block
```

Development data may be used to calibrate reference thresholds and inspect contradictions. Held-out validation must use new recording days **and** new focal scenes/flowers so consecutive frames from the same stream cannot leak across the split.

At least 20% of truth material is independently double-annotated. Annotation adjudication occurs before algorithm scoring. Annotators do not receive target scores, nuisance scores, target-route labels, triad states or acquisition-policy outputs. Reference-stream footage is never input to the tested algorithms.

## Systems compared

### A. Direct target-only naive

Only the direct insect route is used. Low direct evidence is treated as a negative observation.

### B. Direct + coupled target, no nuisance/support

Both target routes are available, isolating the value and risk of indirect target rescue without nuisance diagnosis or censoring.

### C. Target + nuisance, no explicit support gate

Target evidence and exogenous nuisance conflicts may trigger audit, but there is no independent observable/compromised/unobservable censoring layer.

### D. Target + support, no nuisance diagnosis

This isolates the value of censoring from the value of nuisance-specific explanation.

### E. Full direct/coupled-target–nuisance–observability triad

The complete V14 state model is used. Unobservable windows are censored; target/nuisance conflicts remain explicit; direct and coupled target routes remain separately auditable.

### F. Protected random reference

A probability sample is selected independently of all algorithmic scores. It is not a competing classifier. It supplies an audit lane for shared misses and a reference denominator for block-level inference.

## Primary metrics

### 1. Visit recall on observable, resolved truth

Among true visit events resolved by the independent reference channel and labelled observable in the primary stream, how many are retained as target candidates?

### 2. False-positive visit rate on resolved truth

How often does the system retain a visit candidate when resolved biological truth is no visit/no insect?

### 3. False-absence rate on resolved truth

The key V15 metric remains the rate at which a system emits interpretable negative evidence for a window in which the independent reference channel resolves a true visit.

### 4. Unobservable recall and false censor rate

The support gate must recover independently labelled unobservable primary windows without censoring large fractions of genuinely observable opportunities.

### 5. Indirect target-rescue rate

Among observable resolved visits where:

- target-coupled response truth is resolved `present`;
- direct target score is below the frozen low threshold;
- a route-specific coupled target score is available;

measure the fraction retained by a strong coupled route. This quantifies whether local flower response rescues visits whose insect image is weak.

### 6. Spurious coupled-candidate rate

Among observable windows with resolved `no_insect` truth, measure the fraction retained with a high coupled-target score. This is the essential guardrail against calling arbitrary flower motion an insect interaction.

### 7. Reference-truth unresolved fractions

Report biological-truth unresolved fraction and target-coupling unresolved fraction separately. Neither is silently converted to absence.

### 8. Shared-blind-spot discovery

Among true visits or severe primary support failures for which both target evidence and nuisance risk are low, how many are recovered by protected random audit?

### 9. Review/capture burden

Report the fraction of windows requiring high-resolution retention or human audit for every comparison system.

### 10. Block-level visit-rate bias and RMSE

Using resolved independent biological truth as evaluation-only reference, compare visit-rate estimates from naive targeted data, observable triad opportunities and the protected probability sample. Censored and unresolved time remain explicit rather than implicit zero visits.

## Contradiction-guided development

Development contradictions are not optimised away blindly. Each recurrent contradiction is first classified as one of:

- definition defect;
- target representation defect;
- nuisance representation defect;
- observation-support failure;
- information absence;
- essential ambiguity;
- legitimate target+nuisance superposition;
- legitimate target-coupled response.

The next diagnostic intervention or observation should discriminate these possibilities. Examples include increasing temporal context, adding a second view, restoring visibility, comparing focal-versus-neighbour flower motion, or using protected random-audit examples where all targeted signals were quiet.

The goal is not zero contradiction. The goal is to reduce *unexplained* contradiction while preserving legitimate multi-process states.

## What would count as success

Before held-out scoring, V15 still requires a sample-size/power plan, frozen calibration rule, cluster-level uncertainty model and numerical claim thresholds. Those values are deliberately not invented here.

The qualitative success pattern is fixed:

1. explicit observability censoring reduces false absence;
2. observable-window visit recall remains competitive;
3. exogenous nuisance information explains error families not captured by support alone;
4. coupled target response rescues some weak-direct true visits;
5. spurious coupled rescue on no-insect truth remains controlled;
6. protected random audit recovers shared misses/support failures outside targeted attention;
7. block-level visit-rate distortion decreases when censoring and probability-sample information are retained;
8. unresolved biological or coupling truth remains explicit.

Failure lowers the corresponding claim rather than triggering repair on the held-out split.

## Final intended product

If V15 succeeds, the method is not “an insect detector plus a noise detector”. It is an observation system with explicit scientific semantics:

```text
direct insect evidence
+ target-coupled local response
+ exogenous nuisance diagnosis
+ observation-availability censoring
+ protected probability audit
+ independent reference truth for validation
```

That is the structure needed for strong visit monitoring because it separates **direct event evidence**, **indirect interaction evidence**, **measurement confounding**, **absence validity**, and **sampling validity** rather than forcing all variation into one confidence score.
