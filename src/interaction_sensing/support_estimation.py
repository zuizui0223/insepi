"""Independent primary-stream observation-support estimation for V15.

The estimator deliberately cannot consume biological target evidence, nuisance
scores, biological truth, or nuisance labels. It receives five positively
defined measurements of the measurement channel itself and answers a narrow
counterfactual question:

    If a focal visit opportunity occurred, did the primary stream preserve enough
    of the relevant zone, scale and interval to attempt biological inference?

This keeps observation support O distinct from target process T, exogenous
nuisance process N, and the V15-v2 target-absence evidence interface A-. O is a
necessary gate for safe absence certification but is never sufficient evidence of
biological absence by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observation_triad import ObservationAvailability, ObservationSupport
from .support_truth import PrimaryStreamSupportTruth, SupportTruthResolution


class SupportMeasurementProvenance(str, Enum):
    """How one primary-stream support measurement was obtained."""

    CAMERA_GEOMETRY = "camera_geometry"
    TARGET_ZONE_VISIBILITY_AUDIT = "target_zone_visibility_audit"
    IMAGE_RESOLUTION_AUDIT = "image_resolution_audit"
    PHOTOMETRIC_AUDIT = "photometric_audit"
    FRAME_TIMING_AUDIT = "frame_timing_audit"
    OTHER_PRIMARY_STREAM_MEASUREMENT = "other_primary_stream_measurement"


@dataclass(frozen=True, slots=True)
class SupportComponentMeasurement:
    """One normalised primary-stream measurement and its provenance."""

    score: float
    provenance: SupportMeasurementProvenance
    method: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("support component score must lie in [0, 1]")
        if not self.method.strip():
            raise ValueError("support measurement method cannot be empty")


@dataclass(frozen=True, slots=True)
class PrimaryStreamSupportMeasurements:
    """Five independent measurements required to estimate observation support."""

    target_zone_coverage: SupportComponentMeasurement
    target_zone_visibility: SupportComponentMeasurement
    spatial_resolution: SupportComponentMeasurement
    photometric_sufficiency: SupportComponentMeasurement
    temporal_continuity: SupportComponentMeasurement

    @property
    def component_scores(self) -> tuple[tuple[str, float], ...]:
        return (
            ("target_zone_coverage", self.target_zone_coverage.score),
            ("target_zone_visibility", self.target_zone_visibility.score),
            ("spatial_resolution", self.spatial_resolution.score),
            ("photometric_sufficiency", self.photometric_sufficiency.score),
            ("temporal_continuity", self.temporal_continuity.score),
        )

    def to_observation_support(self) -> ObservationSupport:
        return ObservationSupport(
            target_zone_coverage=self.target_zone_coverage.score,
            target_zone_visibility=self.target_zone_visibility.score,
            spatial_resolution=self.spatial_resolution.score,
            photometric_sufficiency=self.photometric_sufficiency.score,
            temporal_continuity=self.temporal_continuity.score,
            reasons=tuple(f"{name}:{value:.6f}" for name, value in self.component_scores),
        )


@dataclass(frozen=True, slots=True)
class PrimaryStreamSupportEstimate:
    availability: ObservationAvailability
    support: ObservationSupport
    limiting_component: str
    support_ceiling: float


@dataclass(frozen=True, slots=True)
class PrimaryStreamSupportEstimator:
    """Transparent estimator of O from primary-stream measurements only.

    Thresholds are development defaults, not field-calibrated detection or
    absence probabilities. They must be calibrated on development support truth
    and frozen before held-out V15 scoring.
    """

    observable_threshold: float = 0.70
    unobservable_threshold: float = 0.30

    def __post_init__(self) -> None:
        for name, value in (
            ("observable_threshold", self.observable_threshold),
            ("unobservable_threshold", self.unobservable_threshold),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.unobservable_threshold >= self.observable_threshold:
            raise ValueError("unobservable_threshold must be below observable_threshold")

    def estimate(self, measurements: PrimaryStreamSupportMeasurements) -> PrimaryStreamSupportEstimate:
        support = measurements.to_observation_support()
        ceiling = support.ceiling
        if ceiling <= self.unobservable_threshold:
            availability = ObservationAvailability.UNOBSERVABLE
        elif ceiling >= self.observable_threshold:
            availability = ObservationAvailability.OBSERVABLE
        else:
            availability = ObservationAvailability.COMPROMISED
        return PrimaryStreamSupportEstimate(
            availability=availability,
            support=support,
            limiting_component=support.limiting_component,
            support_ceiling=ceiling,
        )


@dataclass(frozen=True, slots=True)
class SupportEstimatorValidationSummary:
    n_rows: int
    resolved_truth_rows: int
    unresolved_truth_rows: int
    exact_availability_accuracy: float
    true_unobservable_rows: int
    unobservable_recall: float
    true_observable_rows: int
    observable_false_censor_rate: float
    true_compromised_rows: int
    compromised_exact_recall: float


def _ratio(num: int, den: int) -> float:
    return 0.0 if den == 0 else num / den


def evaluate_support_estimates(
    truth: list[PrimaryStreamSupportTruth],
    estimates: list[PrimaryStreamSupportEstimate],
) -> SupportEstimatorValidationSummary:
    """Evaluate O without biological-event or nuisance truth.

    Unresolved support truth remains outside support-accuracy denominators. These
    metrics validate the measurement-support estimator only; they cannot validate
    target absence.
    """

    if len(truth) != len(estimates):
        raise ValueError("support truth/estimate lengths must match")

    resolved: list[tuple[PrimaryStreamSupportTruth, PrimaryStreamSupportEstimate]] = []
    unresolved = 0
    for truth_row, estimate in zip(truth, estimates, strict=True):
        if truth_row.resolution is SupportTruthResolution.UNRESOLVED:
            unresolved += 1
        else:
            resolved.append((truth_row, estimate))

    exact = sum(t.availability is e.availability for t, e in resolved)
    true_unobservable = [(t, e) for t, e in resolved if t.availability is ObservationAvailability.UNOBSERVABLE]
    true_observable = [(t, e) for t, e in resolved if t.availability is ObservationAvailability.OBSERVABLE]
    true_compromised = [(t, e) for t, e in resolved if t.availability is ObservationAvailability.COMPROMISED]

    caught_unobservable = sum(e.availability is ObservationAvailability.UNOBSERVABLE for _, e in true_unobservable)
    false_censor_observable = sum(e.availability is ObservationAvailability.UNOBSERVABLE for _, e in true_observable)
    caught_compromised = sum(e.availability is ObservationAvailability.COMPROMISED for _, e in true_compromised)

    return SupportEstimatorValidationSummary(
        n_rows=len(truth),
        resolved_truth_rows=len(resolved),
        unresolved_truth_rows=unresolved,
        exact_availability_accuracy=_ratio(exact, len(resolved)),
        true_unobservable_rows=len(true_unobservable),
        unobservable_recall=_ratio(caught_unobservable, len(true_unobservable)),
        true_observable_rows=len(true_observable),
        observable_false_censor_rate=_ratio(false_censor_observable, len(true_observable)),
        true_compromised_rows=len(true_compromised),
        compromised_exact_recall=_ratio(caught_compromised, len(true_compromised)),
    )
