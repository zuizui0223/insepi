# V14 — Target–nuisance–observability model for visit sensing

## Why V14 exists

For visit observation, defining the world as simply `insect = signal` and
`everything else = noise` is too coarse.

A stable flower, static vegetation, sky, and substrate are non-target context,
but they are not automatically noise. A process becomes **nuisance** only when it
can alter inference about the focal insect/visit event by creating false evidence,
hiding real evidence, corrupting attribution, or degrading the measurement
channel.

A second distinction is equally important: **nuisance burden and observability
are not opposites**. A scene can contain strong background motion and still show
the focal interaction zone clearly enough to detect a visit. Conversely, a quiet
scene can be unobservable because a leaf covers the flower, the interaction zone
falls outside usable coverage, the image is saturated, or spatial/temporal
resolution is inadequate.

V14 therefore separates target evidence, exogenous nuisance, target-coupled
response, and observation support rather than forcing all image variation onto
one signal/noise axis.

## The observation variables

### 1. Target evidence — direct insect route

`E_direct` asks:

> Is there direct evidence for the focal insect or visit event in this window?

A high direct score is candidate-positive evidence. A low direct score is *not*
automatically biological absence.

### 2. Target-coupled evidence — indirect biological route

A visit can also leave a local response in the biological target, for example a
flower displacement following contact. V14 therefore keeps a second target-side
route:

`E_coupled = local target-response evidence × actor/target-link confidence`.

This route is not exogenous nuisance by definition, but arbitrary flower motion
is not automatically insect evidence. Direct and coupled routes are retained
separately before the target-side aggregate is formed.

### 3. Nuisance risk — what InsePi-like logic asks

`N` asks:

> Is an **exogenous** process likely to mimic the event, hide it, corrupt
> attribution, or degrade the measurement channel?

The reference nuisance vector remains separated into:

- false-event risk;
- missed-event risk;
- attribution risk.

A nuisance source is classified by causal effect, not by simply being “not an
insect”. Stable context therefore has zero nuisance effect, while camera shake,
vegetation motion, shadow, occlusion, blur and clutter can have different
combinations of mimic, mask, attribution and support-degradation effects.

### 4. Observation support — whether absence/presence is even interpretable

`O` asks the counterfactual question:

> If a visit occurred at the focal interaction zone, was the measurement channel
> sufficient to observe it?

The V14 reference support vector contains:

- target-zone coverage;
- target-zone visibility;
- spatial resolution;
- photometric sufficiency;
- temporal continuity.

The conservative observability ceiling is the minimum component. This is a
measurement-support quantity, not `1 - nuisance` and not a biological state.

## Latent causal view

The dimensionless V14a world distinguishes:

- `T`: focal target / visit process;
- `N`: exogenous nuisance process;
- `C`: target-driven local response, where `C => T`;
- `O`: observation support of the available measurement channel.

The closed-world process states are:

1. `T0 N0 C0` baseline;
2. `T1 N0 C0` target only;
3. `T0 N1 C0` nuisance only;
4. `T1 N0 C1` target-coupled;
5. `T1 N1 C0` target+nuisance superposition;
6. `T1 N1 C1` target+nuisance+coupling.

Target and nuisance are therefore non-exclusive. A superposed state is not an
error simply because both processes are present.

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

## Three distinct kinds of unresolved inference

V14a further distinguishes why a visit decision is unresolved:

- `information_absent`: the measurement channel does not contain enough support;
- `essential_ambiguity`: competing process hypotheses remain indistinguishable
  under the chosen sufficient statistics;
- `model_uncertainty`: information is present, but the current representation or
  decision rule does not resolve it.

These are development diagnoses and must not be collapsed into one generic
“noise” class.

## The unobservable state

`unobservable` is a measurement statement, not a biological state and not a
noise class.

Examples include:

- focal flower/interaction zone outside usable coverage;
- severe occlusion of the interaction zone;
- severe focus/resolution loss;
- saturation or near-black photometric failure;
- loss of temporal continuity required to distinguish a visit from transient
  image change.

For an unobservable window:

- low target evidence must **not** become absence;
- high target evidence may trigger retention/audit but is not automatically a
  defensible visit;
- the window is censored from the conservative opportunity denominator;
- the limiting support component and lost observation effort are retained.

This yields two scientifically different non-detections:

```text
observable + low target evidence   -> negative evidence
unobservable + low target evidence -> censored / information absent
```

## Observation-effort accounting

Recorded effort is now partitioned into three disjoint classes:

1. **denominator eligible** — the opportunity can enter conservative ecological
   visit-rate/prevalence denominators;
2. **censored unobservable** — structural measurement support is insufficient;
3. **uncertain noneligible** — not fully unobservable, but compromised support or
   high missed-event risk prevents a defensible negative interpretation.

All recorded seconds belong to exactly one of these classes. Compromised or
ambiguous effort is therefore not allowed to disappear between the observable and
unobservable bins.

## Where contradiction enters development

The algorithms deliberately attend to different aspects of the same stream. Their
contradiction is diagnostic:

- target high / nuisance high: nuisance mimic versus real target under adverse
  conditions;
- target low / nuisance high: correct suppression versus hidden target;
- target high / low nuisance but poor support: target signal without enough
  measurement support;
- target low / low nuisance: genuine quiet versus shared blind spot;
- direct target weak / coupled route strong: possible indirect visit evidence
  rather than automatic nuisance.

The next experiment should discriminate these hypotheses. Contradiction itself is
not a truth label or a universal acquisition priority.

## Intended visit-observation architecture

```text
Direct insect evidence ─┐
                        ├─ target-side evidence ─┐
Target-coupled response ┘                       │
                                                ├─ diagnostic synthesis
Exogenous nuisance risk ────────────────────────┤
Observation support ────────────────────────────┘

Protected random audit
  -> independent audit of all states, including shared misses
```

For ecological analysis, targeted clips and the protected probability sample have
different jobs. Targeted clips enrich useful review opportunities; the protected
sample supplies an auditable denominator and estimates how often the system was
observable, compromised, unresolved, or censored.

## Current development evidence

V14 is **development evidence**, not field visit validation.

The abstract visit-inference benchmark compares target-only, target+nuisance and
full triad semantics on truth-known synthetic windows. Its current deterministic
run shows:

- target-only false absence among true visits ≈ `0.2135`;
- target+nuisance false absence ≈ `0.1162`;
- triad false absence ≈ `0.00001`;
- target-only unobservable denominator contamination = `1.0`;
- target+nuisance contamination ≈ `0.8010`;
- triad contamination = `0.0`.

These values demonstrate the **logical value of an accurately measured
observation-support axis**. They do not establish that real pixels provide such a
support estimate; the simulator supplies a deliberately well-separated support
measurement.

The canonical V14a dimensionless phase sweep contains 125,440 truth-known worlds
and is byte-deterministic across Python hash seeds. Three of four preregistered
qualitative predictions were supported. The prediction that `Pi2 ≈ 1` would by
itself thicken ambiguity when other separation was weak was **not supported** and
is retained as a negative development result.

## Next validation target

The critical next question is no longer whether the ontology helps when
observability is known. It is whether **observation support can be estimated from
real visit-camera measurements without access to support truth**.

A later frozen visit-validation generation should estimate separately:

1. calibration of coverage/visibility/resolution/photometry/continuity support;
2. target/event recovery conditional on measured observable opportunities;
3. nuisance false-event/missed-event/attribution recovery;
4. false-absence rate with and without the observability gate;
5. indirect target rescue from target-coupled response;
6. visit/prevalence inference using protected probability sampling;
7. shared-blind-spot recovery from random audit;
8. whether contradiction-guided interventions reduce failure-localisation effort.

V13 and all earlier locked generations remain unchanged. V14 is a new conceptual
and development generation rather than a retrospective redefinition of them.
