# V15 empirical bridge v2

## Current location

V14b/V14c is now the repository main line. V15 is the empirical bridge: it asks
whether the independently defined target, target-coupled, nuisance and observation-
support quantities can be measured and validated on real visit recordings.

The historical V15 design in PR #37 already separated biological-event truth,
coupling truth, nuisance truth and support truth. V15 v2 keeps that structure but
corrects one implication exposed by V14c.

## The correction

Observation support `O` answers:

> If a focal event were present, did the primary stream preserve enough of the
> relevant zone/time/scale to attempt interpretation?

It does **not** answer:

> Was the focal biological process absent?

Likewise, the current target evidence path is positive-only. A low/zero target
score means target evidence was not retained; it is not positive evidence of
absence.

Therefore:

```text
O observable + target evidence low
            !=
certified biological absence
```

Without another channel, that state remains unresolved.

## Five quantities, not four collapsed quantities

V15 v2 uses:

- `T` — direct positive target evidence;
- `C` — positive target-coupled response evidence;
- `N` — positive exogenous nuisance evidence;
- `O` — measurement support;
- `A-` — optional independently validated target-absence evidence.

`A-` is an evidence interface, not a claimed field method. The default is
`TargetAbsenceEvidence.unavailable()`. A positive `A-` record must name a source
and an independent validation reference and cannot be created by taking
`1 - target_score` or by treating O as absence.

## Output semantics

Safe V15 outputs distinguish:

1. positive target evidence;
2. certified negative evidence, requiring `A-` plus adequate O;
3. censoring when O is unobservable;
4. unresolved inference when evidence is insufficient or attribution remains
   ambiguous.

Historical/naive comparison systems may still force a low target score into an
absence decision. V15 v2 records that separately as `forced_absence_call`. This
allows the cost of forced binarisation to be measured without calling it evidence.

## Full system

The full comparison uses `ProcessPreservingObservationTriadPolicy`, not the
historical V14a triad. Thus observable high target + high nuisance evidence is a
legitimate superposition: target evidence remains positive while nuisance audit
is retained.

For a quiet observable window, the historical triad may internally reach its old
negative state. V15 v2 translates that state as follows:

- with independently validated `A-`: certified negative evidence;
- without `A-`: unresolved + audit, not target absence.

## Validation consequences

The old generic `false_absence` metric is split into two families.

### Certified absence

- certified absence calls on resolved truth;
- false certified absence count/rate;
- visits misclassified as certified absence.

These are the quantities relevant to a future safe absence claim.

### Forced binarisation

- forced absence calls;
- forced false absence count/rate;
- visits lost by forced absence.

These quantify the cost of naive architectures and must not be presented as
calibrated negative evidence.

## Identification boundary

Until an independent absence channel is actually validated, V15 can validate
presence detection, indirect target rescue, nuisance diagnosis, O, censoring,
protected random audit and detected-event rates conditional on interpretable
exposure. It cannot tighten the safe target-presence upper bound below 1 merely
from non-detection.

This directly carries the V14c result into the empirical design rather than
quietly reintroducing `non-detection = absence` at the field-validation stage.

## Freeze boundary

Before any held-out field result is scored, freeze:

1. T/C/N/O measurement procedures and truth annotation;
2. O calibration and missing-data rules;
3. whether an `A-` channel exists at all;
4. if it exists, its measurement definition and independent held-out validation;
5. forced-versus-certified absence metrics;
6. sampling/power and cluster/exposure-time estimands;
7. numerical claim thresholds.

No V15 field result exists yet.
