# V14 — Target–nuisance–observability model for visit sensing

## Why V14 exists

For visit observation, defining the world as simply `insect = signal` and
`everything else = noise` is too coarse.

A stable flower, static vegetation, sky, and substrate are non-target context,
but they are not automatically noise. A process becomes **nuisance** only when it
can alter the inference about the focal insect/visit event by creating false
evidence, hiding real evidence, or corrupting attribution.

A second distinction is equally important: **nuisance burden and observability
are not opposites**. A scene can contain strong background motion and still show
the focal interaction zone clearly enough to detect a visit. Conversely, a quiet
scene can be unobservable because a leaf covers the flower, the interaction zone
falls outside the usable frame, the image is saturated, or spatial/temporal
resolution is inadequate.

V14 therefore keeps three axes separate.

## The three axes

### 1. Target evidence — what PolliPi-like logic asks

`E` answers:

> Is there evidence for the focal insect or visit event in this window?

A high `E` is a candidate-positive signal. A low `E` is *not* automatically
biological absence.

### 2. Nuisance risk — what InsePi-like logic asks

`N` answers:

> Is a non-target process likely to mimic the event, hide it, or make attribution
> unreliable?

The reference nuisance vector remains separated into:

- false-event risk;
- missed-event risk;
- attribution risk.

The scalar `burden = max(risks)` is used only as a transparent diagnostic summary.
The three components remain available because positive and negative inference can
fail for different reasons.

### 3. Observation support — whether absence/presence is even interpretable

`O` answers the counterfactual question:

> If a visit occurred at the focal interaction zone, was the measurement channel
> sufficient to observe it?

The V14 reference support vector contains:

- target-zone coverage;
- target-zone visibility;
- spatial resolution;
- photometric sufficiency;
- temporal continuity.

The conservative observability ceiling is the minimum component. This is a
reference implementation, not a calibrated field probability.

## Generative view

The conceptual observation model is

```text
latent insect/visit process  Z
latent nuisance process      N
measurement support/channel  O
              \              |              /
               \             |             /
                    observed stream X
                         |
              +----------+----------+
              |                     |
       target observer         nuisance observer
          E = f_E(X)             R = f_N(X)
              |                     |
              +----------+----------+
                         |
                diagnostic synthesis
                         |
          observable / compromised / censored
```

The critical point is that `O` is not set to `1 - R`.

## Reference diagnostic states

| Target evidence | Nuisance | Observation support | V14 state | Meaning |
|---|---|---|---|---|
| high | low | observable | `clean_target_candidate` | retain as a strong visit candidate |
| high | high | observable/compromised | `target_nuisance_conflict` | possible visit under confounding; audit |
| high | low | compromised | `target_observability_conflict` | candidate exists but measurement support is weak |
| low | high | observable/compromised | `nuisance_dominated_or_possible_miss` | low target evidence is not safe absence |
| low | low | observable | `quiet_observable` | negative evidence is interpretable |
| low | low | compromised | `quiet_compromised` | quiet or shared miss; audit rather than call absence |
| any | any | unobservable | `unobservable_censored` | biological state is censored |
| intermediate | any | non-censored | `ambiguous` | insufficient target evidence for either sign |

## The unobservable state

`unobservable` is a measurement statement, not a biological state and not a
noise class.

A window can become unobservable when the focal interaction opportunity cannot be
resolved from the available stream. Examples include:

- focal flower/interaction zone outside usable coverage;
- severe occlusion of the interaction zone;
- severe focus/resolution loss;
- saturation or near-black photometric failure;
- loss of temporal continuity required to distinguish a visit from transient
  image change.

For an unobservable window:

- `PolliPi low` must **not** be converted to absence;
- `PolliPi high` can still trigger retention/audit, but it is not upgraded to a
  defensible visit solely because the target observer is confident;
- the window is censored from the conservative opportunity denominator;
- the cause and lost observation effort should be recorded explicitly.

This converts “we saw no insect” into two scientifically different outcomes:

```text
observable + low target evidence  -> negative evidence
unobservable + low target evidence -> unknown/censored
```

That distinction is essential for visit-rate estimation.

## Where contradiction enters development

The two algorithms are deliberately looking at different aspects of the same
stream. Their contradiction is therefore diagnostic:

- target high / nuisance high: is biological evidence being created by the
  nuisance, or is a real insect present under adverse conditions?
- target low / nuisance high: is the target observer suppressing a real event or
  correctly ignoring disturbance?
- target high / low nuisance but poor support: why did the target observer fire
  when the interaction opportunity was not adequately observable?
- target low / low nuisance: either genuine quiet or a shared blind spot; only an
  independent audit lane can distinguish these cases.

The next experiment should be chosen to discriminate these hypotheses. The
contradiction itself is not a truth label or universal acquisition priority.

## Final visit-observation architecture

The intended deployment architecture is therefore four functional lanes, not a
single score:

```text
PolliPi / target evidence
  -> enrich probable insect/visit events

InsePi / nuisance risk
  -> enrich false-event, miss-risk, and attribution-risk conditions

Observability gate
  -> decide whether presence/absence is interpretable or censored

Protected random audit
  -> sample conditions independent of all three scores, including shared misses
```

For ecological analysis, raw targeted clips and the protected probability sample
have different jobs. Targeted clips maximise useful review opportunities; the
protected sample supplies an auditable denominator and estimates how often the
system was observable, compromised, or completely censored.

## V14 development target

V14 is not yet a performance benchmark. It establishes the state model and
software contract that a later visit-validation generation must test with
independent insect/visit truth and observation-support truth.

The next validation should estimate separately:

1. target/event recovery conditional on observable opportunities;
2. nuisance false-event/missed-event/attribution recovery;
3. calibration of the observable/compromised/unobservable gate;
4. false-absence rate when the observability gate is removed;
5. visit/prevalence inference using the protected probability sample;
6. shared-blind-spot recovery from random audit;
7. whether contradictions reduce the number of interventions/audits needed to
   localise failure mechanisms.

V13 and all earlier locked generations remain unchanged. V14 begins a new
conceptual generation rather than retrospectively changing their definitions.
