import inspect

import pytest

from interaction_sensing.observation_triad import ObservationAvailability
from interaction_sensing.support_estimation import (
    PrimaryStreamSupportEstimator,
    PrimaryStreamSupportMeasurements,
    SupportComponentMeasurement,
    SupportMeasurementProvenance,
    evaluate_support_estimates,
)
from interaction_sensing.support_truth import (
    PrimaryStreamSupportTruth,
    SupportComponentState,
)


def measurement(
    score: float,
    provenance: SupportMeasurementProvenance = SupportMeasurementProvenance.OTHER_PRIMARY_STREAM_MEASUREMENT,
) -> SupportComponentMeasurement:
    return SupportComponentMeasurement(score, provenance, "synthetic_primary_stream_measurement")


def measurements(*, coverage=0.9, visibility=0.9, resolution=0.9, photometry=0.9, temporal=0.9):
    return PrimaryStreamSupportMeasurements(
        target_zone_coverage=measurement(coverage, SupportMeasurementProvenance.CAMERA_GEOMETRY),
        target_zone_visibility=measurement(visibility, SupportMeasurementProvenance.TARGET_ZONE_VISIBILITY_AUDIT),
        spatial_resolution=measurement(resolution, SupportMeasurementProvenance.IMAGE_RESOLUTION_AUDIT),
        photometric_sufficiency=measurement(photometry, SupportMeasurementProvenance.PHOTOMETRIC_AUDIT),
        temporal_continuity=measurement(temporal, SupportMeasurementProvenance.FRAME_TIMING_AUDIT),
    )


def truth(availability: ObservationAvailability) -> PrimaryStreamSupportTruth:
    adequate = SupportComponentState.ADEQUATE
    if availability is ObservationAvailability.OBSERVABLE:
        return PrimaryStreamSupportTruth(adequate, adequate, adequate, adequate, adequate, "synthetic_truth")
    if availability is ObservationAvailability.COMPROMISED:
        return PrimaryStreamSupportTruth(adequate, SupportComponentState.COMPROMISED, adequate, adequate, adequate, "synthetic_truth")
    return PrimaryStreamSupportTruth(adequate, SupportComponentState.FAILED, adequate, adequate, adequate, "synthetic_truth")


def unresolved_truth() -> PrimaryStreamSupportTruth:
    adequate = SupportComponentState.ADEQUATE
    return PrimaryStreamSupportTruth(
        adequate,
        SupportComponentState.UNRESOLVED,
        adequate,
        adequate,
        adequate,
        "synthetic_truth",
    )


def test_support_estimator_api_cannot_consume_target_or_nuisance_outputs() -> None:
    parameters = tuple(inspect.signature(PrimaryStreamSupportEstimator.estimate).parameters)
    assert parameters == ("self", "measurements")


def test_quiet_but_occluded_primary_stream_is_unobservable() -> None:
    result = PrimaryStreamSupportEstimator().estimate(measurements(visibility=0.10))
    assert result.availability is ObservationAvailability.UNOBSERVABLE
    assert result.limiting_component == "target_zone_visibility"
    assert result.support_ceiling == 0.10


def test_one_compromised_component_makes_support_compromised_not_unobservable() -> None:
    result = PrimaryStreamSupportEstimator().estimate(measurements(photometry=0.50))
    assert result.availability is ObservationAvailability.COMPROMISED
    assert result.limiting_component == "photometric_sufficiency"


def test_high_primary_stream_support_is_observable_without_target_evidence() -> None:
    result = PrimaryStreamSupportEstimator().estimate(measurements())
    assert result.availability is ObservationAvailability.OBSERVABLE
    assert result.support_ceiling == 0.9


def test_support_validation_uses_only_resolved_support_truth() -> None:
    estimator = PrimaryStreamSupportEstimator()
    truths = [
        truth(ObservationAvailability.OBSERVABLE),
        truth(ObservationAvailability.UNOBSERVABLE),
        truth(ObservationAvailability.COMPROMISED),
        unresolved_truth(),
    ]
    estimates = [
        estimator.estimate(measurements()),
        estimator.estimate(measurements(visibility=0.10)),
        estimator.estimate(measurements(resolution=0.50)),
        estimator.estimate(measurements()),
    ]
    summary = evaluate_support_estimates(truths, estimates)
    assert summary.n_rows == 4
    assert summary.resolved_truth_rows == 3
    assert summary.unresolved_truth_rows == 1
    assert summary.exact_availability_accuracy == 1.0
    assert summary.unobservable_recall == 1.0
    assert summary.observable_false_censor_rate == 0.0
    assert summary.compromised_exact_recall == 1.0


def test_support_validation_length_mismatch_fails_closed() -> None:
    with pytest.raises(ValueError, match="lengths must match"):
        evaluate_support_estimates([truth(ObservationAvailability.OBSERVABLE)], [])


def test_support_measurement_ranges_fail_closed() -> None:
    with pytest.raises(ValueError, match="must lie"):
        measurement(1.01)
