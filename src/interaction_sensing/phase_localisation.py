"""Fail-closed localisation of empirical measurements on the frozen V14b grid.

This module computes the six dimensionless coordinates defined before the V14b
phase-surface measurement.  It does not run or tune either observer, classify a
visit, interpolate the frozen surface, or turn an off-grid measurement into an
in-grid result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from itertools import product
from math import isfinite

FROZEN_V14B_PHASE_SURFACE_SHA256 = (
    "1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class PhaseMeasurementProvenance:
    """Frozen measurement identity and common units for one empirical block."""

    block_id: str
    measurement_profile_sha256: str
    time_unit: str
    amplitude_unit: str
    length_unit: str

    def __post_init__(self) -> None:
        for name, value in (
            ("block_id", self.block_id),
            ("time_unit", self.time_unit),
            ("amplitude_unit", self.amplitude_unit),
            ("length_unit", self.length_unit),
        ):
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string")
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")
        if not isinstance(self.measurement_profile_sha256, str):
            raise TypeError("measurement_profile_sha256 must be a string")
        if _SHA256_RE.fullmatch(self.measurement_profile_sha256) is None:
            raise ValueError(
                "measurement_profile_sha256 must be 64 lowercase hex characters"
            )


def _require_finite(name: str, value: float, *, strictly_positive: bool) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite numeric value")
    if strictly_positive and value <= 0.0:
        raise ValueError(f"{name} must be strictly positive")
    if not strictly_positive and value < 0.0:
        raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True, slots=True)
class EmpiricalPhaseMeasurements:
    """Raw, same-unit measurements required to compute Pi1--Pi6."""

    provenance: PhaseMeasurementProvenance
    observation_window_duration: float
    target_process_timescale: float
    nuisance_or_coupled_response_timescale: float
    direct_target_motion_amplitude: float
    reference_nuisance_motion_amplitude: float
    target_driven_local_response_amplitude: float
    nuisance_spatial_correlation_length: float
    target_spatial_support_width: float
    sampling_frequency: float

    def __post_init__(self) -> None:
        for name in (
            "observation_window_duration",
            "target_process_timescale",
            "nuisance_or_coupled_response_timescale",
            "reference_nuisance_motion_amplitude",
            "nuisance_spatial_correlation_length",
            "target_spatial_support_width",
            "sampling_frequency",
        ):
            _require_finite(name, getattr(self, name), strictly_positive=True)
        for name in (
            "direct_target_motion_amplitude",
            "target_driven_local_response_amplitude",
        ):
            _require_finite(name, getattr(self, name), strictly_positive=False)


@dataclass(frozen=True, slots=True)
class DimensionlessPhaseCoordinate:
    pi1: float
    pi2: float
    pi3: float
    pi4: float
    pi5: float
    pi6: float

    def __post_init__(self) -> None:
        for name in ("pi1", "pi2", "pi5", "pi6"):
            _require_finite(name, getattr(self, name), strictly_positive=True)
        for name in ("pi3", "pi4"):
            _require_finite(name, getattr(self, name), strictly_positive=False)

    @property
    def values(self) -> tuple[float, ...]:
        return (self.pi1, self.pi2, self.pi3, self.pi4, self.pi5, self.pi6)

    def to_dict(self) -> dict[str, float]:
        return {f"pi{index}": value for index, value in enumerate(self.values, start=1)}


def compute_phase_coordinate(
    measurements: EmpiricalPhaseMeasurements,
) -> DimensionlessPhaseCoordinate:
    """Compute the prefrozen coordinate ratios without clipping or smoothing."""

    target_time = measurements.target_process_timescale
    reference_amplitude = measurements.reference_nuisance_motion_amplitude
    target_width = measurements.target_spatial_support_width
    return DimensionlessPhaseCoordinate(
        pi1=measurements.observation_window_duration / target_time,
        pi2=measurements.nuisance_or_coupled_response_timescale / target_time,
        pi3=measurements.direct_target_motion_amplitude / reference_amplitude,
        pi4=measurements.target_driven_local_response_amplitude / reference_amplitude,
        pi5=measurements.nuisance_spatial_correlation_length / target_width,
        pi6=measurements.sampling_frequency * target_time,
    )


@dataclass(frozen=True, slots=True)
class FrozenPhaseGrid:
    pi1: tuple[float, ...]
    pi2: tuple[float, ...]
    pi3: tuple[float, ...]
    pi4: tuple[float, ...]
    pi5: tuple[float, ...]
    pi6: tuple[float, ...]

    def __post_init__(self) -> None:
        for axis, values in self.axes:
            if not values or tuple(sorted(set(values))) != values:
                raise ValueError(f"{axis} grid values must be unique and increasing")

    @property
    def axes(self) -> tuple[tuple[str, tuple[float, ...]], ...]:
        values_by_axis = (self.pi1, self.pi2, self.pi3, self.pi4, self.pi5, self.pi6)
        return tuple(
            (f"pi{index}", values)
            for index, values in enumerate(values_by_axis, start=1)
        )


FROZEN_V14B_GRID = FrozenPhaseGrid(
    pi1=(0.1, 0.31622776601683794, 1.0, 3.1622776601683795, 10.0),
    pi2=(0.01, 0.1, 0.31622776601683794, 1.0, 3.1622776601683795, 10.0, 100.0),
    pi3=(0.0, 0.1, 0.31622776601683794, 1.0, 3.1622776601683795),
    pi4=(0.0, 0.1, 0.31622776601683794, 1.0, 3.1622776601683795),
    pi5=(0.01, 0.1, 0.31622776601683794, 1.0, 3.1622776601683795, 10.0, 100.0),
    pi6=(2.0, 4.0, 8.0, 16.0, 32.0),
)


class GridPosition(str, Enum):
    EXACT = "exact"
    BRACKETED = "bracketed"
    BELOW_SUPPORT = "below_support"
    ABOVE_SUPPORT = "above_support"


@dataclass(frozen=True, slots=True)
class AxisBracket:
    axis: str
    value: float
    position: GridPosition
    lower: float | None
    upper: float | None

    @property
    def within_support(self) -> bool:
        return self.position in (GridPosition.EXACT, GridPosition.BRACKETED)

    @property
    def corner_values(self) -> tuple[float, ...]:
        if self.position is GridPosition.EXACT:
            assert self.lower is not None
            return (self.lower,)
        if self.position is GridPosition.BRACKETED:
            assert self.lower is not None and self.upper is not None
            return (self.lower, self.upper)
        return ()

    def to_dict(self) -> dict[str, str | float | None]:
        return {
            "axis": self.axis,
            "value": self.value,
            "position": self.position.value,
            "lower": self.lower,
            "upper": self.upper,
        }


def _bracket(axis: str, value: float, grid_values: tuple[float, ...]) -> AxisBracket:
    if value < grid_values[0]:
        return AxisBracket(
            axis, value, GridPosition.BELOW_SUPPORT, None, grid_values[0]
        )
    if value > grid_values[-1]:
        return AxisBracket(
            axis, value, GridPosition.ABOVE_SUPPORT, grid_values[-1], None
        )
    for index, grid_value in enumerate(grid_values):
        if value == grid_value:
            return AxisBracket(axis, value, GridPosition.EXACT, grid_value, grid_value)
        if value < grid_value:
            return AxisBracket(
                axis,
                value,
                GridPosition.BRACKETED,
                grid_values[index - 1],
                grid_value,
            )
    raise AssertionError("in-support coordinate was not bracketed")


@dataclass(frozen=True, slots=True)
class PhaseGridLocation:
    block_id: str
    measurement_profile_sha256: str
    coordinate: DimensionlessPhaseCoordinate
    brackets: tuple[AxisBracket, ...]

    @property
    def within_frozen_support(self) -> bool:
        return all(bracket.within_support for bracket in self.brackets)

    @property
    def exact_grid_coordinate(self) -> bool:
        return all(bracket.position is GridPosition.EXACT for bracket in self.brackets)

    @property
    def out_of_support_axes(self) -> tuple[str, ...]:
        return tuple(
            bracket.axis for bracket in self.brackets if not bracket.within_support
        )

    @property
    def corner_coordinates(self) -> tuple[DimensionlessPhaseCoordinate, ...]:
        if not self.within_frozen_support:
            return ()
        return tuple(
            DimensionlessPhaseCoordinate(*values)
            for values in product(*(bracket.corner_values for bracket in self.brackets))
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "block_id": self.block_id,
            "measurement_profile_sha256": self.measurement_profile_sha256,
            "coordinate": self.coordinate.to_dict(),
            "brackets": [bracket.to_dict() for bracket in self.brackets],
            "within_frozen_support": self.within_frozen_support,
            "exact_grid_coordinate": self.exact_grid_coordinate,
            "out_of_support_axes": list(self.out_of_support_axes),
            "corner_count": len(self.corner_coordinates),
            "bracketing_grid_coordinates": [
                corner.to_dict() for corner in self.corner_coordinates
            ],
            "surface_interpolation_permitted": False,
        }


def localise_on_frozen_v14b_grid(
    measurements: EmpiricalPhaseMeasurements,
) -> PhaseGridLocation:
    """Compute an auditable exact/bracketed/out-of-support grid location."""

    coordinate = compute_phase_coordinate(measurements)
    brackets = tuple(
        _bracket(axis, value, grid_values)
        for (axis, grid_values), value in zip(
            FROZEN_V14B_GRID.axes, coordinate.values, strict=True
        )
    )
    return PhaseGridLocation(
        block_id=measurements.provenance.block_id,
        measurement_profile_sha256=measurements.provenance.measurement_profile_sha256,
        coordinate=coordinate,
        brackets=brackets,
    )
