# Tutorial — use the exploration guard with another sensing problem

The frozen V6 evidence comes from PolliPi and InsePi, but the allocation structure
requires only two deployment-available acquisition signals:

1. **evidence** — how strongly this moment is worth observing for the biological
   process of interest;
2. **observability** — how strongly this moment deserves audit because the
   observation process is unreliable.

The generic reference API is `interaction_sensing.guarded_portfolio`. It is not a
new V7 runtime implementation; parity tests verify that the frozen
`E=.50/P=.10/I=.40/D=0` PolliPi/InsePi policy maps exactly to this generic form on
representative worlds.

## Minimal example

```python
from interaction_sensing.guarded_portfolio import (
    GuardedPortfolio,
    select_guarded_indices,
)

scores = [
    {"evidence": 0.05, "observability": 0.10},
    {"evidence": 0.95, "observability": 0.15},
    {"evidence": 0.20, "observability": 0.90},
    {"evidence": 0.80, "observability": 0.75},
]

selected, provenance = select_guarded_indices(
    scores,
    budget_fraction=0.50,
    portfolio=GuardedPortfolio.frozen_v6_reference(),
    seed=1234,
)
```

No ground-truth event label is accepted by the selector. Ground truth belongs only
in post-selection evaluation.

## Example 1 — acoustic bird monitoring

An acoustic system could define:

```text
evidence       = probability / evidence of a focal vocalisation
observability  = risk from rain, wind, clipping, overlapping choruses or machinery
```

The allocator does not need to know the species identity or acoustic model
architecture. Half of the audit budget remains non-preferential, 10% targets
biological evidence and 40% targets observation-risk conditions under the frozen
reference proportions.

The method would still require its own simulation/calibration/validation before
those exact weights were claimed optimal for acoustics.

## Example 2 — nest camera

Possible signals:

```text
evidence       = evidence of adult arrival / prey delivery
observability  = occlusion, overexposure, condensation, camera displacement risk
```

A pure event trigger can oversample active, visually clean periods. A pure risk
trigger can spend most effort on unusable scenes. The exploration guard reserves a
known share of the observation denominator regardless of either score.

## Example 3 — phenology camera

Possible signals:

```text
evidence       = evidence of bud burst / flowering / colour transition
observability  = snow cover, fog, shadow, exposure shift, camera motion risk
```

Here the evidence and observability channels need not be classifiers; they can be
rule-based indices or calibrated continuous scores.

## Example 4 — wildlife camera trap

Possible signals:

```text
evidence       = target-animal or generic-animal evidence
observability  = vegetation motion, infrared flare, lens obstruction, blur, scene
                 shift, multi-animal attribution risk
```

This is different from active learning for image labelling. The selector allocates
future capture/audit effort over observation windows; it does not choose which
existing image receives a training label.

## User-defined weights

The generic API permits another study to define a different portfolio:

```python
portfolio = GuardedPortfolio(
    exploration=0.70,
    arms=(("evidence", 0.15), ("observability", 0.15)),
)
```

The exploration theory then applies with `alpha=0.70`:

```text
TV(Q,U) <= 0.30
Q(A) >= 0.70 U(A)
U(x)/Q(x) <= 1 / 0.70
```

Those are policy-class guarantees. They do not prove that the chosen evidence/risk
scores are scientifically useful.

## More than two exploitation signals

The public API can allocate several independent acquisition arms:

```python
portfolio = GuardedPortfolio(
    exploration=0.60,
    arms=(
        ("target_evidence", 0.15),
        ("observability", 0.15),
        ("rare_context", 0.10),
    ),
)
```

Each arm receives its own quota and ranking. There is still no single global scalar
that collapses all objectives.

Unused positive-priority capacity from any targeted arm returns to uniform
exploration rather than being donated to another targeted arm.

## When not to use a dual-observer portfolio

Prefer uniform or a simpler design when:

- there is no meaningful resource constraint;
- targeted capture cannot alter the scientific denominator;
- observability risk is negligible or already constant;
- one observer/arm strictly dominates the multi-arm design in a properly separated
  development benchmark;
- the study cannot preserve a non-preferential reference stream but requires
  unbiased population-level inference.

## What transfers across systems

The transferable object is:

```text
independent acquisition signals
+ guaranteed exploration
+ arm-specific quotas
+ exact-budget spillover
+ sampling-distortion accounting
+ locked falsification
```

The following do **not** automatically transfer:

- PolliPi thresholds;
- InsePi noise features;
- V6 50/10/40 weights;
- V7 disturbance frequencies;
- field accuracy.

This distinction is what allows the paper to argue broad methodological
applicability without pretending one flower-camera configuration is universal.
