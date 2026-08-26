# V15 empirical localisation on the frozen V14b surface

## Current state

V14b already measured the frozen ternary phase surface with the frozen target
and nuisance observers and the frozen family-wise nuisance threshold. V15 now
has a separate pre-data localisation layer that can convert raw empirical block
measurements into the six prefrozen dimensionless coordinates.

This layer does not rerun V14b, inspect latent truth, change an observer or
threshold, or infer values between measured surface coordinates.

## Fixed coordinate map

For each empirical block, the runner computes:

1. `Pi1 = observation_window_duration / target_process_timescale`
2. `Pi2 = nuisance_or_coupled_response_timescale / target_process_timescale`
3. `Pi3 = direct_target_motion_amplitude / reference_nuisance_motion_amplitude`
4. `Pi4 = target_driven_local_response_amplitude / reference_nuisance_motion_amplitude`
5. `Pi5 = nuisance_spatial_correlation_length / target_spatial_support_width`
6. `Pi6 = sampling_frequency * target_process_timescale`

The time, amplitude and length quantities in each ratio must use the units
declared in the input. Sampling frequency must use the inverse of the declared
time unit. A zero reference nuisance amplitude is an invalid measurement; the
runner does not introduce an epsilon denominator.

## Fail-closed location states

- `exact`: all six coordinates are frozen grid values.
- `bracketed`: all coordinates are inside frozen support, but at least one lies
  between grid values. The runner reports all bracketing corners and does not
  interpolate them.
- `out_of_support`: at least one coordinate is outside frozen support. The
  runner reports the affected axes and produces no bracketing corners. It does
  not clip to the nearest boundary.

An out-of-support block is a measurement-domain result, not evidence for or
against biological visit detection.

## Input and execution

The input schema is `insepi-v15-empirical-phase-measurements-v1`:

```json
{
  "schema": "insepi-v15-empirical-phase-measurements-v1",
  "measurement_profile_sha256": "<64 lowercase hex characters>",
  "units": {"time": "s", "amplitude": "px", "length": "px"},
  "blocks": [
    {
      "block_id": "day01-sceneA",
      "observation_window_duration": 10.0,
      "target_process_timescale": 1.0,
      "nuisance_or_coupled_response_timescale": 1.0,
      "direct_target_motion_amplitude": 1.0,
      "reference_nuisance_motion_amplitude": 1.0,
      "target_driven_local_response_amplitude": 1.0,
      "nuisance_spatial_correlation_length": 1.0,
      "target_spatial_support_width": 1.0,
      "sampling_frequency": 8.0
    }
  ]
}
```

Run:

```text
python scripts/locate_v15_on_frozen_phase_surface.py \
  --input empirical_phase_measurements.json \
  --output empirical_phase_locations.json
```

The output records the exact input-file SHA-256, the measurement-profile hash,
the frozen V14b phase-surface hash, each raw-derived coordinate, each axis
bracket, and the explicit no-interpolation/no-extrapolation flags.

## Remaining gate before held-out use

The code path is testable, but the empirical measurement profile is not frozen.
Before held-out capture, development data must fix the raw measurement
procedures, calibration references, block/exclusion rules and the resulting
profile SHA-256. Held-out empirical localisation and surface-value lookup remain
unauthorized until that commitment exists.
