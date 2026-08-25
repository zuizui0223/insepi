# V14a2 spatiotemporal prefreeze

## Status

V14a2 is a new closed-world development generation created after the registered V14a P3 prediction was not supported. It does **not** modify or rescue V14a. The first V14a2 scientific sweep is blocked in this PR.

## Why a new generation is required

The V14a diagnosis exposed two variables that were not independently controlled:

1. spatial separation: focal and reference channels retained a fixed coherent nuisance relationship while Pi2 changed;
2. temporal sampling: 256 samples were fixed per window while Pi1 and Pi2 varied, so samples per process timescale changed implicitly.

V14a therefore remains a valid negative result for its frozen world, but it did not isolate a general temporal-scale-collision proposition.

## New dimensionless axes

The retained coordinates are:

- Pi1 = observation window / target timescale;
- Pi2 = nuisance or coupled-response timescale / target timescale;
- Pi3 = direct target amplitude / reference nuisance amplitude;
- Pi4 = target-driven local response amplitude / reference nuisance amplitude.

V14a2 adds:

- **Pi5 = nuisance spatial correlation length / target spatial support width**;
- **Pi6 = sampling frequency x target timescale**.

Pi6 is a design coordinate, not a derived annotation: it sets the actual number of samples in the generated observation.

## Spatial generator

Space is measured in target-support-width units. The focal position is 0 and reference positions are 1, 2 and 4.

The nuisance process has one stationary mean-reverting temporal component shared at the focal position. At reference distance d,

`rho(d) = exp(-d/Pi5)`

and the reference trace is

`rho * shared + sqrt(1-rho^2) * independent_local`,

where both temporal components have the same Pi2 timescale.

Thus changing Pi5 changes statistical spatial dependence, not merely the amplitude of one identical waveform.

## Why correlation alone is prohibited

Pearson correlation is invariant to amplitude scaling. Two traces x and 0.1x have correlation one even though their spatial response magnitudes differ.

V14a2 therefore retains correlation only as one statistic and adds an amplitude-sensitive normalized structure function:

`D = RMS(focal-reference) / (RMS(focal)+RMS(reference))`.

Spatial coherence is `1-D`. These quantities are dimensionless.

## Sampling adequacy

Three explicit quantities are retained:

- target samples per timescale = Pi6;
- nuisance samples per timescale = Pi2 x Pi6;
- nuisance timescales per observation window = Pi1 / Pi2.

The registered resolved-process slice requires at least 8 samples per target timescale, at least 8 samples per nuisance timescale, at least one target timescale of window coverage, and at least one nuisance timescale of window coverage.

This slice is fixed before results. It is not created after seeing where ambiguity appears.

## Two-stage sweep

The protocol freezes two distinct sweeps.

### Coarse phase geometry

A broad six-dimensional grid maps the full response surface. Its purpose is to find where conclusions change, not to maximise one expected effect.

### Focused collision geometry

A second, already specified grid is denser around Pi2 ~= 1 and Pi5 ~= 1, restricted to weak direct/coupled target evidence and true mixed T+N regimes. Its coordinates are fixed now; they cannot be moved after the coarse result.

## Registered questions

Q1. Does undersampling increase information absence when Pi6 becomes too small?

Q2. Does Pi5 change the spatial sufficient statistics as intended? The direction of final ambiguity is **not** assumed from this construction property.

Q3. Among temporally resolved, weak-target-evidence coordinates, does ambiguity increase near Pi2 ~= 1 preferentially when Pi5 is also near 1?

This is a new **Pi2 x Pi5 interaction** prediction. It is not a rerun of V14a P3.

Q4. If that interaction is absent after explicit Pi6 control, the timescale-collision hypothesis is rejected more strongly.

Q5. Simultaneous target and nuisance support remains legitimate superposition and must not itself count as undetermined.

## Anti-tuning boundary

Before the first scientific sweep:

1. generator code, axes, feature family, thresholds and both sweep grids must be committed;
2. ordinary CI must be green;
3. the exact prefreeze commit and protocol SHA-256 must be recorded in a separate receipt;
4. only then may the first full sweep execute.

After execution, an unfavourable result is retained. Moving the ambiguity threshold, changing Pi5/Pi6 coordinates, adding another statistic, or changing the generator requires another named generation.
