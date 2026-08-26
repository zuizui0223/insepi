# V15-v2 operational ordinal calibration

## Why the field runtime should not inherit 0.25 / 0.65 / 0.60

Those values are historical development defaults in the V14/V15 software. They are not field-calibrated probabilities or scientific thresholds.

PolliPi direct target evidence is already a frozen ordinal contract:

- 0 = no positive target support retained;
- 0.5 = intermediate target support;
- 1 = strong positive target support.

V15-v2 therefore preserves that direct scale rather than applying a second arbitrary continuous threshold to it.

## Common operational scale

Continuous C and N measurements are mapped from development-only calibration onto the same support scale:

```text
0.0 = no positive support retained
0.5 = intermediate / unresolved support
1.0 = strong positive support
```

After calibration, structural decision boundaries are therefore:

```text
target high = 1
target low = 0
nuisance high = 1
```

Those are category semantics, not fitted numerical performance thresholds.

## Coupled route

The raw usable C route remains

```text
coupled_response_score * target_link_confidence
```

A development-frozen low/high boundary maps that continuous value to 0 / 0.5 / 1. The final boundary and calibration SHA are currently absent, so held-out C decisions remain blocked.

## Nuisance effects stay separate

The three positive nuisance effects are:

- false-event support;
- missed-event support;
- attribution-corruption support.

Each effect receives its own:

- selected positive exogenous-process feature;
- low/high ordinal boundary;
- development calibration SHA.

Allowed candidate features exclude target output and include reference motion, scale-sensitive spatial coherence, reference stationarity/spectrum, temporal support and the combined process index.

A single raw nuisance index cannot be copied into all three effects.

## Runtime object

`V15OperationalCalibration` has no default constructor values. A usable object must explicitly contain:

- the coupled boundary and calibration SHA;
- three effect-specific nuisance calibrations;
- the development source-manifest SHA.

`build_v15_operational_evidence()` only applies that already-frozen object. It does not fit, search or tune anything on the current window.

## Current boundary

The runtime schema is development-defined, not scientifically frozen. Final C/N values must come from development-only truth and measurement data and be committed before held-out scoring. Claim authorization thresholds remain a separate layer.
