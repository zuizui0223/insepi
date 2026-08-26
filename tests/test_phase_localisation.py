from __future__ import annotations

import json
from math import nan
from pathlib import Path

import pytest

from interaction_sensing.phase_localisation import (
    FROZEN_V14B_GRID,
    DimensionlessPhaseCoordinate,
    EmpiricalPhaseMeasurements,
    PhaseMeasurementProvenance,
    compute_phase_coordinate,
    localise_on_frozen_v14b_grid,
)

ROOT = Path(__file__).resolve().parents[1]


def _measurements(**overrides: float) -> EmpiricalPhaseMeasurements:
    values: dict[str, float] = {
        "observation_window_duration": 10.0,
        "target_process_timescale": 1.0,
        "nuisance_or_coupled_response_timescale": 1.0,
        "direct_target_motion_amplitude": 1.0,
        "reference_nuisance_motion_amplitude": 1.0,
        "target_driven_local_response_amplitude": 1.0,
        "nuisance_spatial_correlation_length": 1.0,
        "target_spatial_support_width": 1.0,
        "sampling_frequency": 8.0,
    }
    values.update(overrides)
    return EmpiricalPhaseMeasurements(
        provenance=PhaseMeasurementProvenance(
            block_id="block-001",
            measurement_profile_sha256="a" * 64,
            time_unit="s",
            amplitude_unit="px",
            length_unit="px",
        ),
        **values,
    )


def test_raw_measurements_compute_all_six_prefrozen_ratios() -> None:
    measurements = _measurements(
        observation_window_duration=6.0,
        target_process_timescale=2.0,
        nuisance_or_coupled_response_timescale=1.0,
        direct_target_motion_amplitude=4.0,
        reference_nuisance_motion_amplitude=8.0,
        target_driven_local_response_amplitude=2.0,
        nuisance_spatial_correlation_length=9.0,
        target_spatial_support_width=3.0,
        sampling_frequency=4.0,
    )

    assert compute_phase_coordinate(measurements) == DimensionlessPhaseCoordinate(
        pi1=3.0,
        pi2=0.5,
        pi3=0.5,
        pi4=0.25,
        pi5=3.0,
        pi6=8.0,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_process_timescale", 0.0),
        ("reference_nuisance_motion_amplitude", 0.0),
        ("target_spatial_support_width", 0.0),
        ("sampling_frequency", nan),
        ("direct_target_motion_amplitude", -0.1),
    ],
)
def test_invalid_measurements_fail_without_epsilon_or_clipping(
    field: str,
    value: float,
) -> None:
    with pytest.raises(ValueError):
        _measurements(**{field: value})


def test_exact_coordinate_has_one_frozen_grid_corner() -> None:
    location = localise_on_frozen_v14b_grid(_measurements())

    assert location.within_frozen_support is True
    assert location.exact_grid_coordinate is True
    assert location.out_of_support_axes == ()
    assert len(location.corner_coordinates) == 1
    assert location.to_dict()["surface_interpolation_permitted"] is False


def test_interior_coordinate_reports_all_64_bracketing_corners() -> None:
    location = localise_on_frozen_v14b_grid(
        _measurements(
            observation_window_duration=0.2,
            nuisance_or_coupled_response_timescale=0.2,
            direct_target_motion_amplitude=0.2,
            target_driven_local_response_amplitude=0.2,
            nuisance_spatial_correlation_length=0.2,
            sampling_frequency=6.0,
        )
    )

    assert location.within_frozen_support is True
    assert location.exact_grid_coordinate is False
    assert len(location.corner_coordinates) == 64
    assert location.to_dict()["corner_count"] == 64


def test_out_of_support_coordinate_is_not_clipped_or_given_corners() -> None:
    location = localise_on_frozen_v14b_grid(
        _measurements(observation_window_duration=0.01, sampling_frequency=64.0)
    )

    assert location.within_frozen_support is False
    assert location.exact_grid_coordinate is False
    assert location.out_of_support_axes == ("pi1", "pi6")
    assert location.corner_coordinates == ()


def test_frozen_localiser_does_not_accept_a_grid_override() -> None:
    with pytest.raises(TypeError, match="unexpected keyword argument 'grid'"):
        localise_on_frozen_v14b_grid(_measurements(), grid=FROZEN_V14B_GRID)  # type: ignore[call-arg]


def test_grid_matches_prefrozen_world_protocol() -> None:
    protocol = json.loads(
        (ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    coarse = protocol["coarse_sweep"]

    for axis, values in FROZEN_V14B_GRID.axes:
        assert values == tuple(coarse[f"{axis}_values"])
