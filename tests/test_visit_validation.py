import pytest

from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
)
from interaction_sensing.visit_validation import (
    VisitPredictionRecord,
    VisitTruthRecord,
    VisitTruthResolution,
    VisitTruthState,
    evaluate_visit_predictions,
    prediction_from_triad,
)


def support(value: float) -> ObservationSupport:
    return ObservationSupport(value, value, value, value, value)


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


def test_evaluator_counts_false_absence_separately_from_censoring() -> None:
    truth = [
        VisitTruthRecord("v1", "b1", VisitTruthState.VISIT_EVENT, ObservationAvailability.OBSERVABLE),
        VisitTruthRecord("v2", "b1", VisitTruthState.VISIT_EVENT, ObservationAvailability.UNOBSERVABLE),
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


def test_shared_blind_spot_requires_random_audit_to_count_as_discovered() -> None:
    truth = [
        VisitTruthRecord("v1", "b1", VisitTruthState.VISIT_EVENT, ObservationAvailability.OBSERVABLE),
        VisitTruthRecord(
            "u1",
            "b1",
            None,
            ObservationAvailability.UNOBSERVABLE,
            biological_truth_resolution=VisitTruthResolution.UNRESOLVED,
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
