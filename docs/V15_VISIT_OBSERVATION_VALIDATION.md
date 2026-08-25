# V15 — Real visit-observation validation design

## Goal

V14 separates three questions:

1. **target evidence** — is there evidence for the focal insect/visit event?
2. **nuisance risk** — can non-target processes mimic, hide, or misattribute it?
3. **observation support** — if a visit happened, was the interaction opportunity observable at all?

V15 is the first generation intended to test whether that separation improves
actual visit observation rather than only software diagnosis or proxy transfer.

The central ecological error to prevent is:

```text
low target evidence -> biological absence
```

when the correct interpretation may be:

```text
low target evidence + poor observation support -> censored / unknown
```

## Independent truth layers

V15 requires three annotations that are conceptually independent of the algorithms.

### Biological-event truth

Human reviewers annotate an operational interaction hierarchy:

- `no_insect`;
- `insect_in_context`;
- `target_contact`;
- `visit_event`.

A `visit_event` is an observed insect interaction with the focal floral target.
It does **not** by itself establish pollen transfer or pollination effectiveness.

### Nuisance truth

Nuisance is multi-label. Reviewers or physical logs record whether a process can:

- mimic the target;
- mask the target;
- corrupt attribution;
- degrade observation support.

The same physical disturbance may have multiple effects.

### Observation-support truth

A separate annotation asks:

> If a visit occurred in the focal interaction zone during this window, was the
> available camera stream sufficient to observe it?

The label is `observable`, `compromised`, or `unobservable` and must not be
inferred from PolliPi/InsePi outputs.

## Why the three truths must be separate

A true visit can occur in an unobservable window. A nuisance process can be strong
while the visit remains observable. A visually quiet window can be unobservable
because the flower is covered or outside usable coverage.

Therefore the benchmark must permit all combinations rather than defining
observability from event or nuisance labels.

## Experimental unit and split

Frames are never treated as independent replicates.

Primary grouping is at least:

```text
recording day × focal flower/scene × recording block
```

Development data may be used to calibrate V14 reference thresholds and to inspect
contradictions. Held-out validation must use new recording days **and** new focal
scenes/flowers so consecutive frames from the same stream cannot leak across the
split.

At least 20% of truth material is independently double-annotated. Annotation
adjudication occurs before algorithm scoring. Annotators do not receive PolliPi,
InsePi, triad-state, or acquisition-policy outputs.

## Systems compared

### A. Target-only naive

PolliPi-like target evidence is used alone. Low target evidence is treated as a
negative observation. This is the baseline most vulnerable to false absence.

### B. Target + nuisance, no explicit support gate

Nuisance conflicts may trigger audit, but there is no independent
observable/compromised/unobservable censoring layer.

### C. Target + observation support, no nuisance diagnosis

This isolates the value of censoring from the value of nuisance-specific
explanation.

### D. Full target–nuisance–observability triad

The V14 state model is used. Unobservable windows are censored; high target/high
nuisance and low target/high nuisance remain explicit conflicts.

### E. Protected random reference

A probability sample is selected independently of all three scores. It is not a
competing classifier. It supplies an unbiased audit lane for shared misses and a
reference denominator for block-level inference.

## Primary metrics

### 1. Visit recall on observable truth

Among true visit events independently labelled observable, how many are retained
as target candidates?

This prevents the observability gate from appearing good merely by censoring hard
positive cases.

### 2. False-positive visit rate

How often does target evidence produce a visit candidate when biological truth is
no visit?

Nuisance-stratified versions identify whether false positives concentrate in
specific disturbance mechanisms.

### 3. False-absence rate

The key V15 metric is the rate at which a system emits interpretable negative
evidence for a window that actually contains a visit.

The full triad should only emit negative evidence for `quiet_observable` windows.
Unobservable windows are excluded from negative calls rather than silently
becoming zeros.

### 4. Unobservable recall and false censor rate

The support gate must recover independently labelled unobservable windows without
censoring large fractions of genuinely observable opportunities.

Both directions are necessary. A gate that labels everything unobservable would
trivially eliminate false absence while destroying useful observation effort.

### 5. Shared-blind-spot discovery

Among true visits or severe observation failures for which both target evidence
and nuisance risk are low, how many are recovered by the protected random audit
lane?

This directly tests the reason random audit is retained even when the two targeted
observers agree.

### 6. Review/capture burden

For each system, report the number/fraction of windows requiring high-resolution
retention or human audit. Accuracy gains are interpreted jointly with this burden,
not as a free resource improvement.

### 7. Block-level visit-rate bias and RMSE

Using full human truth as evaluation-only reference, compare visit-rate estimates
from:

- naive targeted data;
- observable opportunities selected by the full triad;
- the protected probability sample with its known inclusion design.

The purpose is not to assume perfect detection. It is to quantify how much
selection and unobservable-time censoring distort the empirical visit rate under
known benchmark truth.

## Contradiction-guided development stage

Development data are not used merely to optimise one score. Error cases are first
partitioned by the V14 diagnostic states:

```text
clean target candidate
target–nuisance conflict
target–observability conflict
nuisance dominated / possible miss
quiet observable
quiet compromised
unobservable censored
ambiguous
```

For each recurrent failure, the next diagnostic experiment should modify one
candidate mechanism at a time. Examples:

- improve temporal context if target evidence fires during camera shake;
- restore visibility or target-zone coverage for an observability conflict;
- increase context duration if nuisance and target evidence cannot be separated;
- use random-audit errors to reveal conditions where both observers are quiet.

After the development calibration rule is frozen, held-out data cannot trigger
threshold or representation changes under the same V15 generation.

## What would count as success

Before held-out scoring, V15 still needs a sample-size/power plan and numerical
claim thresholds. Those values are intentionally not invented here.

The qualitative success pattern is nevertheless fixed:

1. explicit observability censoring reduces false absence relative to target-only
   negative calls;
2. observable-window visit recall remains competitive rather than being obtained
   by censoring all hard cases;
3. nuisance information explains/recovers error families not captured by support
   alone;
4. protected random audit recovers at least some shared misses or support failures
   outside targeted attention;
5. block-level visit-rate distortion is lower when the probability-sample and
   censoring information are retained.

Failure of any component lowers the corresponding claim rather than being repaired
post hoc on the held-out split.

## Final intended product

If V15 succeeds, the visit-observation method is no longer described as “an insect
detector plus a noise detector”. It becomes an observation system with explicit
scientific semantics:

```text
biological actor evidence
+ nuisance diagnosis
+ observation-availability censoring
+ protected probability audit
```

That is the structure required for a strong visit-monitoring method because it
separates **event enrichment**, **measurement failure**, **absence validity**, and
**sampling validity** instead of forcing them into a single confidence score.
