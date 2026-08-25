import pytest

from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
)
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


def visit_truth(window_id: str, support_truth: ObservationAvailability, event_id: str) -> VisitTruthRecord:
    return VisitTruthRecord(
        window_id,
        "b1",
        VisitTruthState.VISIT_EVENT,
        support_truth,
        event_id=event_id,
    )


def test_unobservable_high_target_is_retained_but_not_interpretable_positive() -> None:
    triad = ObservationTriadPolicy().decide(
        TargetEvidence(0.95),
        NuisanceEvidence(0.05, 0.05, 0.05),
        support(0.10),
    )
    prediction = prediction_from_triad("w1", triad)
    assert prediction.retain_candidate is True
    assert prediction.censored is True
    assert prediction.positive_evidence is False
    assert prediction.negative_evidence is False


def test_quiet_observable_becomes_negative_evidence_not_censoring() -> None:
    triad = ObservationTriadPolicy().decide(
        TargetEvidence(0.05),
        NuisanceEvidence(0.05, 0.05, 0.05),
        support(0.90),
    )
    prediction = prediction_from_triad("w1", triad)
    assert prediction.negative_evidence is True
    assert prediction.censored is False


def test_prediction_from_triad_preserves_direct_and_coupled_target_routes() -> None:
    routes = TargetRouteEvidence(0.10, 0.90, 0.90)
    triad = ObservationTriadPolicy().decide(
        routes.to_target_evidence(),
        NuisanceEvidence(0.05, 0.05, 0.05),
        support(0.90),
    )
    prediction = prediction_from_triad("w1", triad, target_routes=routes)
    assert prediction.direct_target_score == 0.10
    assert prediction.coupled_target_score == 0.81
    assert prediction.retain_candidate is True


def test_evaluator_counts_false_absence_separately_from_censoring() -> None:
    truth = [
        visit_truth("v1", ObservationAvailability.OBSERVABLE, "event-1"),
        visit_truth("v2", ObservationAvailability.UNOBSERVABLE, "event-2"),
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
        VisitTruthRecord("n2", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.UNOBSERVABLE),
    ]
    predictions = [
        VisitPredictionRecord("v1", True, True, False, False, False, target_score=0.9, nuisance_burden=0.1),
        VisitPredictionRecord("v2", False, False, False, True, True, target_score=0.1, nuisance_burden=0.1),
        VisitPredictionRecord("n1", False, False, True, False, False, target_score=0.1, nuisance_burden=0.1),
        VisitPredictionRecord("n2", False, False, False, True, True, target_score=0.1, nuisance_burden=0.1),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.visit_recall_on_observable_truth == 1.0
    assert summary.false_absence_count == 0
    assert summary.false_absence_rate == 0.0
    assert summary.unobservable_recall == 1.0
    assert summary.observable_false_censor_rate == 0.0
    assert summary.reference_truth_unresolved_fraction == 0.0


def test_evaluator_detects_naive_false_absence_when_reference_truth_resolves_visit() -> None:
    truth = [
        VisitTruthRecord(
            "v1",
            "b1",
            VisitTruthState.VISIT_EVENT,
            ObservationAvailability.UNOBSERVABLE,
            reference_truth_source="reference_camera",
            event_id="event-1",
        ),
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
    ]
    predictions = [
        VisitPredictionRecord("v1", False, False, True, False, False),
        VisitPredictionRecord("n1", False, False, True, False, False),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.negative_calls_on_resolved_truth == 2
    assert summary.false_absence_count == 1
    assert summary.false_absence_rate == 0.5
    assert summary.missed_visit_as_absence_rate == 1.0


def test_unresolved_reference_truth_is_excluded_from_biological_metrics_but_kept_for_support() -> None:
    truth = [
        VisitTruthRecord(
            "u1",
            "b1",
            None,
            ObservationAvailability.UNOBSERVABLE,
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
            reference_truth_source="reference_camera_occluded",
            target_coupled_response_present=None,
            target_coupled_response_resolution=CoupledResponseResolution.UNRESOLVED,
        ),
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
    ]
    predictions = [
        VisitPredictionRecord("u1", False, False, False, True, True),
        VisitPredictionRecord("n1", False, False, True, False, False),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.resolved_biological_truth_windows == 1
    assert summary.unresolved_biological_truth_windows == 1
    assert summary.reference_truth_unresolved_fraction == 0.5
    assert summary.negative_calls_on_resolved_truth == 1
    assert summary.false_absence_count == 0
    assert summary.true_unobservable_windows == 1
    assert summary.unobservable_recall == 1.0
    assert summary.unresolved_coupled_response_windows == 1


def test_unresolved_truth_cannot_smuggle_no_insect_label() -> None:
    with pytest.raises(ValueError, match="must not carry"):
        VisitTruthRecord(
            "u1",
            "b1",
            VisitTruthState.NO_INSECT,
            ObservationAvailability.UNOBSERVABLE,
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
        )


def test_resolved_truth_requires_a_state() -> None:
    with pytest.raises(ValueError, match="requires biological_state"):
        VisitTruthRecord("u1", "b1", None, ObservationAvailability.OBSERVABLE)


def test_positive_coupling_truth_requires_contact_or_visit() -> None:
    with pytest.raises(ValueError, match="requires target_contact or visit_event"):
        VisitTruthRecord(
            "x",
            "b1",
            VisitTruthState.NO_INSECT,
            ObservationAvailability.OBSERVABLE,
            target_coupled_response_present=True,
        )


def test_indirect_target_rescue_is_measured_only_when_direct_route_is_weak() -> None:
    truth = [
        VisitTruthRecord(
            "coupled-visit",
            "b1",
            VisitTruthState.VISIT_EVENT,
            ObservationAvailability.OBSERVABLE,
            event_id="event-c",
            target_coupled_response_present=True,
        ),
        VisitTruthRecord(
            "direct-visit",
            "b1",
            VisitTruthState.VISIT_EVENT,
            ObservationAvailability.OBSERVABLE,
            event_id="event-d",
            target_coupled_response_present=False,
        ),
    ]
    predictions = [
        VisitPredictionRecord(
            "coupled-visit",
            True,
            True,
            False,
            False,
            False,
            target_score=0.81,
            nuisance_burden=0.1,
            direct_target_score=0.10,
            coupled_target_score=0.81,
        ),
        VisitPredictionRecord(
            "direct-visit",
            True,
            True,
            False,
            False,
            False,
            target_score=0.90,
            nuisance_burden=0.1,
            direct_target_score=0.90,
            coupled_target_score=0.05,
        ),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.weak_direct_coupled_visit_windows == 1
    assert summary.indirect_target_rescue_count == 1
    assert summary.indirect_target_rescue_rate == 1.0


def test_spurious_coupled_candidate_is_measured_on_no_insect_truth() -> None:
    truth = [
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
        VisitTruthRecord("n2", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
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
            "u1",
            "b1",
            None,
            ObservationAvailability.UNOBSERVABLE,
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
            target_coupled_response_present=None,
            target_coupled_response_resolution=CoupledResponseResolution.UNRESOLVED,
        ),
        VisitTruthRecord("n1", "b1", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE),
    ]
    predictions = [
        VisitPredictionRecord(
            "v1", False, False, False, False, False, True, target_score=0.1, nuisance_burden=0.1
        ),
        VisitPredictionRecord(
            "u1", False, False, False, False, False, False, target_score=0.1, nuisance_burden=0.1
        ),
        VisitPredictionRecord(
            "n1", False, False, True, False, False, False, target_score=0.1, nuisance_burden=0.1
        ),
    ]
    summary = evaluate_visit_predictions(truth, predictions)
    assert summary.shared_blind_spot_truth_windows == 2
    assert summary.shared_blind_spot_audited == 1
    assert summary.shared_blind_spot_discovery_rate == 0.5


def test_prediction_contract_rejects_censored_negative() -> None:
    with pytest.raises(ValueError, match="censored window"):
        VisitPredictionRecord("x", False, False, True, True, False)


def test_truth_prediction_window_mismatch_fails_closed() -> None:
    truth = [VisitTruthRecord("a", "b", VisitTruthState.NO_INSECT, ObservationAvailability.OBSERVABLE)]
    predictions = [VisitPredictionRecord("x", False, False, True, False, False)]
    with pytest.raises(ValueError, match="window mismatch"):
        evaluate_visit_predictions(truth, predictions)
