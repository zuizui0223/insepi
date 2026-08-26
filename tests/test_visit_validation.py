import pytest

from interaction_sensing.absence_certification import TargetAbsenceEvidence
from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
)
from interaction_sensing.support_truth import PrimaryStreamSupportTruth, SupportComponentState
from interaction_sensing.target_routes import TargetRouteEvidence
from interaction_sensing.visit_validation import (
    CoupledResponseResolution,
    VisitPredictionRecord,
    VisitTruthRecord,
    VisitTruthResolution,
    VisitTruthState,
    evaluate_visit_predictions,
    prediction_from_triad,
)


def support(value: float) -> ObservationSupport:
    return ObservationSupport(value, value, value, value, value)


def truth_support(availability: ObservationAvailability) -> PrimaryStreamSupportTruth:
    if availability is ObservationAvailability.OBSERVABLE:
        return PrimaryStreamSupportTruth.fully_observable(annotation_method="synthetic_test_fixture")
    if availability is ObservationAvailability.COMPROMISED:
        return PrimaryStreamSupportTruth(
            SupportComponentState.ADEQUATE, SupportComponentState.COMPROMISED,
            SupportComponentState.ADEQUATE, SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE, "synthetic_test_fixture",
        )
    if availability is ObservationAvailability.UNOBSERVABLE:
        return PrimaryStreamSupportTruth(
            SupportComponentState.ADEQUATE, SupportComponentState.FAILED,
            SupportComponentState.ADEQUATE, SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE, "synthetic_test_fixture",
        )
    raise AssertionError(availability)


def visit_truth(window_id: str, availability: ObservationAvailability, event_id: str) -> VisitTruthRecord:
    return VisitTruthRecord(
        window_id, "b1", VisitTruthState.VISIT_EVENT, truth_support(availability), event_id=event_id
    )


def test_unobservable_high_target_is_retained_but_censored() -> None:
    triad = ObservationTriadPolicy().decide(
        TargetEvidence(0.95), NuisanceEvidence(0.05, 0.05, 0.05), support(0.10)
    )
    prediction = prediction_from_triad("w1", triad)
    assert prediction.retain_candidate is True
    assert prediction.censored is True
    assert prediction.positive_evidence is False
    assert prediction.negative_evidence is False
    assert prediction.forced_absence_call is False


def test_quiet_observable_is_not_certified_absence_without_independent_channel() -> None:
    triad = ObservationTriadPolicy().decide(
        TargetEvidence(0.05), NuisanceEvidence(0.05, 0.05, 0.05), support(0.90)
    )
    prediction = prediction_from_triad("w1", triad)
    assert prediction.negative_evidence is False
    assert prediction.forced_absence_call is True
    assert prediction.audit_priority is True
    assert prediction.unresolved is True


def test_quiet_observable_can_be_certified_by_independent_absence_channel() -> None:
    triad = ObservationTriadPolicy().decide(
        TargetEvidence(0.05), NuisanceEvidence(0.05, 0.05, 0.05), support(0.90)
    )
    absence = TargetAbsenceEvidence.independently_validated(
        source="negative_channel", validation_ref="heldout-absence-calibration"
    )
    prediction = prediction_from_triad("w1", triad, absence_evidence=absence)
    assert prediction.negative_evidence is True
    assert prediction.forced_absence_call is False
    assert prediction.absence_certification_source == "negative_channel"


def test_prediction_from_triad_preserves_direct_and_coupled_target_routes() -> None:
    routes = TargetRouteEvidence(0.10, 0.90, 0.90)
    triad = ObservationTriadPolicy().decide(
        routes.to_target_evidence(), NuisanceEvidence(0.05, 0.05, 0.05), support(0.90)
    )
    prediction = prediction_from_triad("w1", triad, target_routes=routes)
    assert prediction.direct_target_score == 0.10
    assert prediction.coupled_target_score == 0.81
    assert prediction.retain_candidate is True


def test_evaluator_separates_certified_and_forced_false_absence() -> None:
    truth = [
        visit_truth("certified-false", ObservationAvailability.OBSERVABLE, "event-1"),
        visit_truth("forced-false", ObservationAvailability.OBSERVABLE, "event-2"),
        VisitTruthRecord(
            "true-absence", "b1", VisitTruthState.NO_INSECT,
            truth_support(ObservationAvailability.OBSERVABLE),
        ),
    ]
    predictions = [
        VisitPredictionRecord("certified-false", False, False, True, False, False),
        VisitPredictionRecord(
            "forced-false", False, False, False, False, False, forced_absence_call=True
        ),
        VisitPredictionRecord("true-absence", False, False, True, False, False),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.certified_absence_calls_on_resolved_truth == 2
    assert summary.false_certified_absence_count == 1
    assert summary.false_certified_absence_rate == 0.5
    assert summary.missed_visit_as_certified_absence_rate == 0.5
    assert summary.forced_absence_calls_on_resolved_truth == 1
    assert summary.forced_false_absence_count == 1
    assert summary.forced_false_absence_rate == 1.0
    assert summary.forced_missed_visit_as_absence_rate == 0.5


def test_censoring_is_separate_from_absence_calls() -> None:
    truth = [
        visit_truth("v1", ObservationAvailability.UNOBSERVABLE, "event-1"),
        VisitTruthRecord(
            "n1", "b1", VisitTruthState.NO_INSECT,
            truth_support(ObservationAvailability.OBSERVABLE),
        ),
    ]
    predictions = [
        VisitPredictionRecord("v1", False, False, False, True, True),
        VisitPredictionRecord("n1", False, False, True, False, False),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.true_unobservable_windows == 1
    assert summary.unobservable_recall == 1.0
    assert summary.false_certified_absence_count == 0
    assert summary.observable_false_censor_rate == 0.0


def test_unresolved_reference_truth_is_excluded_from_biological_metrics_but_kept_for_support() -> None:
    truth = [
        VisitTruthRecord(
            "u1", "b1", None, truth_support(ObservationAvailability.UNOBSERVABLE),
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
            reference_truth_source="reference_camera_occluded",
            target_coupled_response_present=None,
            target_coupled_response_resolution=CoupledResponseResolution.UNRESOLVED,
        ),
        VisitTruthRecord(
            "n1", "b1", VisitTruthState.NO_INSECT,
            truth_support(ObservationAvailability.OBSERVABLE),
        ),
    ]
    predictions = [
        VisitPredictionRecord("u1", False, False, False, True, True),
        VisitPredictionRecord("n1", False, False, True, False, False),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.resolved_biological_truth_windows == 1
    assert summary.unresolved_biological_truth_windows == 1
    assert summary.reference_truth_unresolved_fraction == 0.5
    assert summary.certified_absence_calls_on_resolved_truth == 1
    assert summary.true_unobservable_windows == 1
    assert summary.unresolved_coupled_response_windows == 1


def test_unresolved_truth_cannot_smuggle_no_insect_label() -> None:
    with pytest.raises(ValueError, match="must not carry"):
        VisitTruthRecord(
            "u1", "b1", VisitTruthState.NO_INSECT,
            truth_support(ObservationAvailability.UNOBSERVABLE),
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
        )


def test_resolved_truth_requires_a_state() -> None:
    with pytest.raises(ValueError, match="requires biological_state"):
        VisitTruthRecord("u1", "b1", None, truth_support(ObservationAvailability.OBSERVABLE))


def test_positive_coupling_truth_requires_contact_or_visit() -> None:
    with pytest.raises(ValueError, match="requires target_contact or visit_event"):
        VisitTruthRecord(
            "x", "b1", VisitTruthState.NO_INSECT,
            truth_support(ObservationAvailability.OBSERVABLE),
            target_coupled_response_present=True,
        )


def test_indirect_target_rescue_is_measured_only_when_direct_route_is_weak() -> None:
    truth = [
        VisitTruthRecord(
            "coupled-visit", "b1", VisitTruthState.VISIT_EVENT,
            truth_support(ObservationAvailability.OBSERVABLE), event_id="event-c",
            target_coupled_response_present=True,
        ),
        VisitTruthRecord(
            "direct-visit", "b1", VisitTruthState.VISIT_EVENT,
            truth_support(ObservationAvailability.OBSERVABLE), event_id="event-d",
            target_coupled_response_present=False,
        ),
    ]
    predictions = [
        VisitPredictionRecord(
            "coupled-visit", True, True, False, False, False,
            target_score=0.81, nuisance_burden=0.1,
            direct_target_score=0.10, coupled_target_score=0.81,
        ),
        VisitPredictionRecord(
            "direct-visit", True, True, False, False, False,
            target_score=0.90, nuisance_burden=0.1,
            direct_target_score=0.90, coupled_target_score=0.05,
        ),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.weak_direct_coupled_visit_windows == 1
    assert summary.indirect_target_rescue_count == 1
    assert summary.indirect_target_rescue_rate == 1.0


def test_spurious_coupled_candidate_is_measured_on_no_insect_truth() -> None:
    truth = [
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, truth_support(ObservationAvailability.OBSERVABLE)),
        VisitTruthRecord("n2", "b1", VisitTruthState.NO_INSECT, truth_support(ObservationAvailability.OBSERVABLE)),
    ]
    predictions = [
        VisitPredictionRecord(
            "n1", True, True, False, False, False,
            direct_target_score=0.05, coupled_target_score=0.80,
        ),
        VisitPredictionRecord(
            "n2", False, False, True, False, False,
            direct_target_score=0.05, coupled_target_score=0.10,
        ),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.observable_no_insect_windows == 2
    assert summary.spurious_coupled_candidate_count == 1
    assert summary.spurious_coupled_candidate_rate == 0.5


def test_shared_blind_spot_requires_random_audit_to_count_as_discovered() -> None:
    truth = [
        visit_truth("v1", ObservationAvailability.OBSERVABLE, "event-1"),
        VisitTruthRecord(
            "u1", "b1", None, truth_support(ObservationAvailability.UNOBSERVABLE),
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
            target_coupled_response_present=None,
            target_coupled_response_resolution=CoupledResponseResolution.UNRESOLVED,
        ),
    ]
    predictions = [
        VisitPredictionRecord(
            "v1", False, False, False, False, False, True,
            target_score=0.1, nuisance_burden=0.1,
        ),
        VisitPredictionRecord(
            "u1", False, False, False, False, False, False,
            target_score=0.1, nuisance_burden=0.1,
        ),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.shared_blind_spot_truth_windows == 2
    assert summary.shared_blind_spot_audited == 1
    assert summary.shared_blind_spot_discovery_rate == 0.5


def test_prediction_contract_rejects_censored_or_positive_forced_absence() -> None:
    with pytest.raises(ValueError, match="censored window"):
        VisitPredictionRecord("x", False, False, False, True, False, forced_absence_call=True)
    with pytest.raises(ValueError, match="forced absence"):
        VisitPredictionRecord("x", True, True, False, False, False, forced_absence_call=True)


def test_truth_prediction_window_mismatch_fails_closed() -> None:
    truth = [
        VisitTruthRecord("a", "b", VisitTruthState.NO_INSECT, truth_support(ObservationAvailability.OBSERVABLE))
    ]
    predictions = [VisitPredictionRecord("x", False, False, True, False, False)]
    with pytest.raises(ValueError, match="window mismatch"):
        evaluate_visit_predictions(truth, predictions)
