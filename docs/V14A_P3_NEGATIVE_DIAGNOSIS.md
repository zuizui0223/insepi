# V14a P3 negative diagnosis and V14b boundary

## Status

This document is a **post-result diagnosis** of the completed V14a dimensionless
phase sweep. It does not change the V14a generator, thresholds, labels, emitted
surface, or the registered result.

The registered P3 prediction remains:

> `Pi2 ~= 1` should thicken essential ambiguity when the other separating
> evidence is weak.

Canonical V14a result: **not supported**.

## What the canonical surface says

Source:
- workflow run `32846060073`;
- head `00810b4ae7ca59a07ed66c4d18ba2ebc4e7296e7`;
- surface SHA-256
  `eaefa4d3a03c4af6dd9ed5ec9fc59f3d4479bfa73feafc348ca054ae8d378cc8`.

The original weak-separation slice (`Pi3 <= 0.3162`, `Pi4 <= 0.3162`) gives:

| diagnostic | `Pi2 = 1` | far `Pi2 = {0.01, 100}` |
|---|---:|---:|
| essential ambiguity | 0.02143 | 0.03259 |
| information absence | 0.79286 | 0.78482 |
| essential ambiguity, coordinates with mean support >= 0.2 | 0.10345 | 0.15145 |
| essential ambiguity, T+N mixed regimes | 0.05357 | 0.08147 |
| essential ambiguity, observable mixed coordinates | 0.27273 | 0.40110 |
| identifiability margin, mixed regimes | 0.35894 | 0.34083 |

Therefore the negative P3 result is **not explained only by information absence**.
After removing low-support coordinates, and after restricting to worlds where
target and nuisance truly coexist, `Pi2 = 1` still does not produce a thicker
ambiguity band.

The machine-readable diagnosis is
`benchmarks/v14a_p3_negative_diagnosis.json`.

## Structural diagnosis

The frozen V14a process model contains a spatial separator that was not swept:

```text
focal nuisance channel    <- coherent exogenous nuisance
neighbour reference       <- the same coherent exogenous nuisance
target coupling           <- focal only
direct actor route        <- separate target channel
```

The protocol has `Pi1`--`Pi4`, but no coordinate controlling the relative spatial
support or correlation length of target and nuisance.

Consequently, `Pi2` changes temporal scale while a strong spatial distinction
remains built into the world. In particular, the neighbour channel continues to
provide a coherent nuisance reference even when nuisance and target timescales
match.

This means two statements must remain separate:

1. **Observed result:** the registered V14a P3 prediction is negative.
2. **Diagnosis:** the V14a generator does not isolate temporal-scale collision
   from spatial separation, so the negative result is not evidence that temporal
   collision can never matter when spatial scales also overlap.

The second statement does not rescue the first.

## New-generation requirement

Do **not** tune V14a thresholds or redefine ambiguity after seeing P3.

A new closed-world generation is required with an independent spatial coordinate:

\[
\Pi_5 =
\frac{\text{nuisance spatial correlation length}}
     {\text{target spatial support width}}.
\]

Interpretation:

- `Pi5 >> 1`: nuisance is broad relative to the target; spatial separation is
  strong;
- `Pi5 ~= 1`: nuisance and target occupy comparable spatial scales;
- `Pi5 << 1`: nuisance is more local than the target support.

The next preregistered question should be an **interaction**, not a replay of P3:

> Does the ambiguity band thicken near `Pi2 ~= 1` specifically when `Pi5` also
> removes spatial-scale separation and direct/coupled evidence is weak?

If that interaction is absent in the new generation, the timescale-collision
hypothesis should be rejected more strongly.

## T+N semantic correction for V14b

A second mismatch was found between V14a components.

The dimensionless phase analyser already allowed:

```text
target support high + nuisance support high -> PRESENT + both-supported
```

because true superposition is not an error.

The historical `ObservationTriadPolicy`, however, routed the same high/high case
to `TARGET_NUISANCE_CONFLICT -> AMBIGUOUS`.

V14a is left unchanged for reproducibility. V14b introduces
`ProcessPreservingObservationTriadPolicy`:

```text
observable + target high + nuisance high
    -> TARGET_NUISANCE_SUPERPOSITION
    -> POSITIVE_CANDIDATE
    -> retain nuisance evidence and request audit/context

compromised/unobservable support
    -> remains ambiguous/censored as appropriate
```

Thus target and nuisance remain independently positive hypotheses while
observability controls whether their evidence can support ecological inference.
