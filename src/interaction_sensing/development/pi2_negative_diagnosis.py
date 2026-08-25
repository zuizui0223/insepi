"""Post-result diagnosis for the negative V14a Pi2 prediction.

This module does not change, tune, or reinterpret the completed V14a phase sweep.
It asks a narrower question: did the registered ``Pi2 ~= 1`` comparison actually
isolate temporal-scale collision from the other separators and sampling limits
embedded in the closed-world generator?

The diagnosis is intentionally based on the emitted phase-surface table and the
frozen protocol only. It never changes observer thresholds or phase labels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping


MIXED_REGIMES = frozenset(
    {
        "target_nuisance_superposed",
        "target_nuisance_coupled",
    }
)


def _float(row: Mapping[str, Any], key: str) -> float:
    return float(row[key])


def _mean(rows: Iterable[Mapping[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows]
    if not values:
        return float("nan")
    return sum(values) / len(values)


def _eq(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def _coordinate_contains(protocol: Mapping[str, Any], tokens: tuple[str, ...]) -> bool:
    coordinates = protocol.get("dimensionless_coordinates", {})
    for name, definition in coordinates.items():
        text = f"{name} {definition}".lower()
        if any(token in text for token in tokens):
            return True
    return False


def _spatial_axis_present(protocol: Mapping[str, Any]) -> bool:
    return _coordinate_contains(
        protocol,
        (
            "spatial correlation",
            "correlation length",
            "spatial support",
            "spatial scale",
            "localization scale",
            "localisation scale",
        ),
    )


def _sampling_axis_present(protocol: Mapping[str, Any]) -> bool:
    return _coordinate_contains(
        protocol,
        (
            "sampling frequency",
            "sampling rate",
            "sample interval",
            "samples per",
            "frame rate",
            "fps",
        ),
    )


def _fixed_neighbor_separator(protocol: Mapping[str, Any]) -> bool:
    process = protocol.get("process_model", {})
    neighbor = str(process.get("neighbor_channel", "")).lower()
    nuisance = str(process.get("exogenous_nuisance", "")).lower()
    return "coherent" in neighbor and "nuisance" in neighbor and "coherent" in nuisance


@dataclass(frozen=True, slots=True)
class Pi2NegativeDiagnosis:
    weak_separation_max: float
    support_minimum: float
    near_pi2: float
    far_pi2: tuple[float, float]
    registered_near_ambiguity: float
    registered_far_ambiguity: float
    near_information_absence: float
    far_information_absence: float
    observable_coordinate_near_ambiguity: float
    observable_coordinate_far_ambiguity: float
    mixed_near_ambiguity: float
    mixed_far_ambiguity: float
    observable_mixed_near_ambiguity: float
    observable_mixed_far_ambiguity: float
    mixed_near_identifiability_margin: float
    mixed_far_identifiability_margin: float
    registered_prediction_supported: bool
    observable_slice_supports_prediction: bool
    mixed_slice_supports_prediction: bool
    spatial_separation_coordinate_present: bool
    fixed_neighbor_spatial_separator: bool
    sampling_density_coordinate_present: bool
    samples_per_window: int
    fast_far_samples_per_nuisance_cycle_min: float
    fast_far_samples_per_nuisance_cycle_max: float
    slow_far_observed_nuisance_cycles_min: float
    slow_far_observed_nuisance_cycles_max: float
    far_comparator_contains_temporal_resolution_limits: bool
    diagnosis: str
    next_generation_required: bool
    recommended_spatial_axis: str
    recommended_sampling_axis: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def diagnose_pi2_negative(
    rows: Iterable[Mapping[str, Any]],
    protocol: Mapping[str, Any],
    *,
    support_minimum: float = 0.20,
) -> Pi2NegativeDiagnosis:
    """Diagnose the registered P3 comparison without changing V14a.

    ``rows`` must be the aggregated phase-surface rows emitted by the canonical
    sweep. The "observable coordinate" slices use the emitted mean observation
    support as a coordinate-level filter; they are a diagnostic, not a new
    claim-bearing analysis.

    Sampling geometry is diagnosed analytically from the frozen grid. With
    ``N`` uniformly spaced samples across a dimensionless observation window
    ``Pi1``, the approximate samples per nuisance cycle are

    ``(N - 1) * Pi2 / Pi1``.

    This matters because the V14a support score does not include a temporal
    sampling-resolution term.
    """

    rows = tuple(rows)
    if not rows:
        raise ValueError("phase-surface rows cannot be empty")
    if not 0.0 <= support_minimum <= 1.0:
        raise ValueError("support_minimum must lie in [0, 1]")

    sweep = protocol["sweep"]
    pi1_values = tuple(float(v) for v in sweep["pi1_values"])
    pi2_values = tuple(float(v) for v in sweep["pi2_values"])
    if not any(_eq(v, 1.0) for v in pi2_values):
        raise ValueError("registered P3 diagnosis requires pi2=1 in the protocol")

    weak_candidates = sorted(
        {
            float(v)
            for key in ("pi3_values", "pi4_values")
            for v in sweep[key]
            if 0.0 < float(v) < 1.0
        }
    )
    if not weak_candidates:
        raise ValueError("protocol has no positive sub-unit weak-separation coordinate")
    weak_max = max(weak_candidates)

    near_pi2 = 1.0
    far_pi2 = (min(pi2_values), max(pi2_values))

    weak = tuple(
        row
        for row in rows
        if _float(row, "pi3") <= weak_max + 1e-12
        and _float(row, "pi4") <= weak_max + 1e-12
    )
    near = tuple(row for row in weak if _eq(_float(row, "pi2"), near_pi2))
    far = tuple(
        row
        for row in weak
        if any(_eq(_float(row, "pi2"), value) for value in far_pi2)
    )

    observable = tuple(
        row for row in weak if _float(row, "mean_observation_support") >= support_minimum
    )
    observable_near = tuple(
        row for row in observable if _eq(_float(row, "pi2"), near_pi2)
    )
    observable_far = tuple(
        row
        for row in observable
        if any(_eq(_float(row, "pi2"), value) for value in far_pi2)
    )

    mixed = tuple(row for row in weak if str(row["regime"]) in MIXED_REGIMES)
    mixed_near = tuple(row for row in mixed if _eq(_float(row, "pi2"), near_pi2))
    mixed_far = tuple(
        row
        for row in mixed
        if any(_eq(_float(row, "pi2"), value) for value in far_pi2)
    )

    observable_mixed = tuple(
        row for row in mixed if _float(row, "mean_observation_support") >= support_minimum
    )
    observable_mixed_near = tuple(
        row for row in observable_mixed if _eq(_float(row, "pi2"), near_pi2)
    )
    observable_mixed_far = tuple(
        row
        for row in observable_mixed
        if any(_eq(_float(row, "pi2"), value) for value in far_pi2)
    )

    reg_near = _mean(near, "essential_ambiguity_rate")
    reg_far = _mean(far, "essential_ambiguity_rate")
    obs_near = _mean(observable_near, "essential_ambiguity_rate")
    obs_far = _mean(observable_far, "essential_ambiguity_rate")
    mix_near = _mean(mixed_near, "essential_ambiguity_rate")
    mix_far = _mean(mixed_far, "essential_ambiguity_rate")
    obs_mix_near = _mean(observable_mixed_near, "essential_ambiguity_rate")
    obs_mix_far = _mean(observable_mixed_far, "essential_ambiguity_rate")
    margin_near = _mean(mixed_near, "mean_identifiability_margin")
    margin_far = _mean(mixed_far, "mean_identifiability_margin")

    registered_supported = reg_near > reg_far
    observable_supported = obs_near > obs_far
    mixed_supported = mix_near > mix_far

    spatial_axis = _spatial_axis_present(protocol)
    fixed_separator = _fixed_neighbor_separator(protocol)
    sampling_axis = _sampling_axis_present(protocol)

    samples = int(sweep.get("samples_per_window", 0))
    if samples < 2:
        raise ValueError("V14a diagnosis requires samples_per_window >= 2")
    fast_pi2, slow_pi2 = far_pi2
    fast_samples_per_cycle = tuple(
        (samples - 1) * fast_pi2 / pi1 for pi1 in pi1_values
    )
    slow_observed_cycles = tuple(pi1 / slow_pi2 for pi1 in pi1_values)

    # This flag is intentionally conservative. Fewer than two samples per cycle
    # is below the Nyquist requirement for a sinusoid, while observing less than
    # one cycle cannot establish a complete oscillatory period from that window.
    far_resolution_limits = (
        min(fast_samples_per_cycle) < 2.0
        or min(slow_observed_cycles) < 1.0
    )

    if registered_supported:
        diagnosis = "registered_P3_supported_no_negative_diagnosis_needed"
        next_generation_required = False
    elif (
        (not spatial_axis and fixed_separator)
        or (not sampling_axis and far_resolution_limits)
    ):
        diagnosis = (
            "registered_P3_not_supported_and_current_generator_does_not_isolate_"
            "timescale_collision_from_spatial_and_sampling_resolution_structure"
        )
        next_generation_required = True
    else:
        diagnosis = (
            "registered_P3_not_supported_under_current_generator_without_a_single_"
            "structural_explanation_from_protocol_metadata"
        )
        next_generation_required = True

    return Pi2NegativeDiagnosis(
        weak_separation_max=weak_max,
        support_minimum=support_minimum,
        near_pi2=near_pi2,
        far_pi2=far_pi2,
        registered_near_ambiguity=reg_near,
        registered_far_ambiguity=reg_far,
        near_information_absence=_mean(near, "information_absence_rate"),
        far_information_absence=_mean(far, "information_absence_rate"),
        observable_coordinate_near_ambiguity=obs_near,
        observable_coordinate_far_ambiguity=obs_far,
        mixed_near_ambiguity=mix_near,
        mixed_far_ambiguity=mix_far,
        observable_mixed_near_ambiguity=obs_mix_near,
        observable_mixed_far_ambiguity=obs_mix_far,
        mixed_near_identifiability_margin=margin_near,
        mixed_far_identifiability_margin=margin_far,
        registered_prediction_supported=registered_supported,
        observable_slice_supports_prediction=observable_supported,
        mixed_slice_supports_prediction=mixed_supported,
        spatial_separation_coordinate_present=spatial_axis,
        fixed_neighbor_spatial_separator=fixed_separator,
        sampling_density_coordinate_present=sampling_axis,
        samples_per_window=samples,
        fast_far_samples_per_nuisance_cycle_min=min(fast_samples_per_cycle),
        fast_far_samples_per_nuisance_cycle_max=max(fast_samples_per_cycle),
        slow_far_observed_nuisance_cycles_min=min(slow_observed_cycles),
        slow_far_observed_nuisance_cycles_max=max(slow_observed_cycles),
        far_comparator_contains_temporal_resolution_limits=far_resolution_limits,
        diagnosis=diagnosis,
        next_generation_required=next_generation_required,
        recommended_spatial_axis=(
            "Pi5 = nuisance spatial correlation length / target spatial support width"
        ),
        recommended_sampling_axis=(
            "Pi6 = sampling frequency * target timescale (samples per target timescale)"
        ),
    )
