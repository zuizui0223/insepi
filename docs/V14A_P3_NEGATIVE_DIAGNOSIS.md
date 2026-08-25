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

Thus the registered result is not a hidden positive effect: every inspected
slice still has lower essential ambiguity at `Pi2 = 1` than in the original far
comparison.

The support-filtered diagnostic shows that the result is not explained by the
**existing V14a support score alone**. It does **not** prove that all information
limitations have been removed, because the V14a support score omitted temporal
sampling adequacy. That omission is itself part of the diagnosis below.

The machine-readable diagnosis is
`benchmarks/v14a_p3_negative_diagnosis.json`.

## Structural diagnosis 1: spatial separation was fixed

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
remains built into the world. The neighbour channel continues to provide a
coherent nuisance reference even when nuisance and target timescales match.

There is a second representation issue hidden inside the current sufficient
statistic: Pearson correlation is insensitive to pure amplitude scaling. If a
neighbour trace is the same waveform at 0.1 times the amplitude, its correlation
can still be 1. A future spatial-scale sweep therefore needs a dimensionless
coherence or structure-function statistic that is sensitive to both phase
coherence and relative amplitude, not correlation alone.

## Structural diagnosis 2: sampling density was not an independent coordinate

V14a fixed `samples_per_window = 256` while `Pi1` varied from `0.01` to `100`.

For uniformly spaced samples, the approximate number of samples per nuisance
cycle is

\[
n_N \approx \frac{(N-1)\Pi_2}{\Pi_1}.
\]

At the fast far comparator `Pi2 = 0.01`, this ranges across the V14a `Pi1` grid
from about `255` down to only `0.0255` samples per nuisance cycle. Several cells
are therefore below the Nyquist requirement for the sinusoidal nuisance process.

At the slow far comparator `Pi2 = 100`, the number of nuisance cycles actually
contained in the observation window is

\[
n_{\mathrm{cycles}} = \frac{\Pi_1}{\Pi_2},
\]

which ranges from `0.0001` to `1.0`. Much of that far comparator therefore sees
only a small fraction of one nuisance cycle.

So the registered comparison

```text
Pi2 = 1
versus
Pi2 = 0.01 or 100
```

does not compare "same timescale" with "cleanly separated timescales" only. It
also compares against regimes in which the fast process may be under-sampled or
the slow process may be under-observed.

This is especially important because V14a's `information_absent` gate did not
contain a sampling-resolution term. Some temporally under-resolved worlds could
therefore enter the identifiability analysis instead of being classified as an
observation-information limitation.

## What can and cannot be concluded

Three statements must remain separate:

1. **Observed result:** the registered V14a P3 prediction is negative.
2. **Generator diagnosis:** V14a did not isolate temporal-scale collision from a
   fixed spatial separator.
3. **Observation-model diagnosis:** V14a did not independently control temporal
   sampling density, so the far comparator contains sampling/coverage limits.

Statements 2 and 3 do not rescue statement 1. They specify why P3 must not be
treated as a clean test of the general timescale-collision proposition.

## New-generation requirement

Do **not** tune V14a thresholds or redefine ambiguity after seeing P3.

A new closed-world generation needs at least two additional dimensionless axes.

### Spatial-scale axis

\[
\Pi_5 =
\frac{\text{nuisance spatial correlation length}}
     {\text{target spatial support width}}.
\]

Interpretation:

- `Pi5 >> 1`: nuisance is broad relative to the target;
- `Pi5 ~= 1`: nuisance and target occupy comparable spatial scales;
- `Pi5 << 1`: nuisance is more local than the target support.

The spatial sufficient statistic must also be revised from correlation alone to
a scale-sensitive quantity, for example a normalized focal-neighbour structure
function or a coherence score combining correlation with amplitude agreement.

### Sampling-density axis

\[
\Pi_6 = f_s\tau_T
\]

where `f_s` is sampling frequency and `tau_T` is the target-process timescale.

`Pi6` is the number of samples per target timescale. The effective samples per
nuisance timescale are then

\[
\Pi_6\Pi_2.
\]

This separates two questions that V14a combined:

- how long the observation window is (`Pi1`);
- how finely the process is sampled (`Pi6`).

## Next preregistered question

The next test should be an interaction, not a replay of P3:

> Conditional on both target and nuisance processes being temporally resolved,
> does ambiguity increase near `Pi2 ~= 1` when spatial-scale separation (`Pi5`)
> is also weak and direct/coupled target evidence is weak?

The preregistration should first exclude coordinates that are structurally
under-sampled or too short to characterize the compared process. Only then is
`Pi2` a clean timescale-separation test.

If the interaction is still absent after independently sweeping `Pi5` and
`Pi6`, the timescale-collision hypothesis should be rejected more strongly.

## T+N semantic correction for V14b

A separate mismatch was found between V14a components.

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
