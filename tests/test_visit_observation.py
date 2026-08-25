from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
)
from interaction_sensing.visit_observation import (
    DiagnosticAction,
    VisitObservationStatus,
    summarise_visit_observations,
    visit_record_from_interpretation,
)


def support(value: float) -> ObservationSupport:
    return ObservationSupport(value, value, value, value, value)


def make_record(window_id: str, target: float, nuisance: NuisanceEvidence, support_value: float):
    interpretation = ObservationTriadPolicy().decide(
        TargetEvidence(target), nuisance, support(support_value)
    )
    return visit_record_from_interpretation(window_id, 10.0, interpretation)


def test_quiet_observable_is_negative_evidence_not_censoring() -> None:
    row = make_record("w1", 0.1, NuisanceEvidence(0.05, 0.05, 0.05), 0.9)
    assert row.status is VisitObservationStatus.OBSERVABLE_NONDETECTION
    assert row.denominator_eligible is True
    assert row.absence_interpretable is True
    assert row.actions == (DiagnosticAction.NO_EXTRA_ACTION,)


def test_quiet_unobservable_is_censored_not_zero_visit() -> None:
    row = make_record("w2", 0.1, NuisanceEvidence(0.05, 0.05, 0.05), 0.1)
    assert row.status is VisitObservationStatus.CENSORED_UNOBSERVABLE
    assert row.denominator_eligible is False
    assert row.absence_interpretable is False
    assert DiagnosticAction.RESTORE_OBSERVABILITY in row.actions
    assert DiagnosticAction.CENSOR_FROM_DENOMINATOR in row.actions
    assert DiagnosticAction.PROTECTED_RANDOM_AUDIT in row.actions


def test_high_target_high_nuisance_routes_to_audit_without_erasing_target() -> None:
    row = make_record("w3", 0.9, NuisanceEvidence(0.9, 0.2, 0.2), 0.9)
    assert row.status is VisitObservationStatus.CONFLICT_AUDIT
    assert DiagnosticAction.RETAIN_TARGET_CLIP in row.actions
    assert DiagnosticAction.AUDIT_NUISANCE in row.actions


def test_high_target_compromised_support_requests_support_restoration() -> None:
    row = make_record("w4", 0.9, NuisanceEvidence(0.1, 0.1, 0.1), 0.5)
    assert row.status is VisitObservationStatus.CONFLICT_AUDIT
    assert DiagnosticAction.RETAIN_TARGET_CLIP in row.actions
    assert DiagnosticAction.RESTORE_OBSERVABILITY in row.actions
    assert DiagnosticAction.PROTECTED_RANDOM_AUDIT in row.actions


def test_low_target_high_miss_risk_is_not_negative_evidence() -> None:
    row = make_record("w5", 0.1, NuisanceEvidence(0.1, 0.9, 0.1), 0.9)
    assert row.status is VisitObservationStatus.CONFLICT_AUDIT
    assert row.denominator_eligible is False
    assert row.absence_interpretable is False
    assert DiagnosticAction.AUDIT_NUISANCE in row.actions


def test_limiting_support_component_is_preserved() -> None:
    interpretation = ObservationTriadPolicy().decide(
        TargetEvidence(0.1),
        NuisanceEvidence(0.05, 0.05, 0.05),
        ObservationSupport(0.95, 0.10, 0.95, 0.95, 0.95),
    )
    row = visit_record_from_interpretation("occluded", 10.0, interpretation)
    assert row.status is VisitObservationStatus.CENSORED_UNOBSERVABLE
    assert row.observability_limiting_component == "target_zone_visibility"


def test_summary_separates_observed_effort_from_censored_effort() -> None:
    rows = [
        make_record("positive", 0.9, NuisanceEvidence(0.1, 0.1, 0.1), 0.9),
        make_record("negative", 0.1, NuisanceEvidence(0.1, 0.1, 0.1), 0.9),
        make_record("censored", 0.1, NuisanceEvidence(0.1, 0.1, 0.1), 0.1),
    ]
    result = summarise_visit_observations(rows)
    assert result.n_windows == 3
    assert result.total_seconds == 30.0
    assert result.eligible_windows == 2
    assert result.eligible_seconds == 20.0
    assert result.censored_windows == 1
    assert result.censored_seconds == 10.0
    assert result.uncertain_noneligible_windows == 0
    assert result.uncertain_noneligible_seconds == 0.0
    assert result.visit_candidate_windows == 1
    assert result.observable_nondetection_windows == 1
    assert result.observable_fraction == 2 / 3
    assert result.censored_fraction == 1 / 3
    assert result.uncertain_noneligible_fraction == 0.0
    assert result.censored_limiting_components == (("target_zone_coverage", 1),)


def test_summary_does_not_drop_compromised_or_high_miss_effort() -> None:
    rows = [
        make_record("eligible", 0.1, NuisanceEvidence(0.1, 0.1, 0.1), 0.9),
        make_record("censored", 0.1, NuisanceEvidence(0.1, 0.1, 0.1), 0.1),
        make_record("compromised", 0.1, NuisanceEvidence(0.1, 0.1, 0.1), 0.5),
        make_record("high_miss", 0.1, NuisanceEvidence(0.1, 0.9, 0.1), 0.9),
    ]
    result = summarise_visit_observations(rows)
    assert result.n_windows == 4
    assert result.total_seconds == 40.0
    assert result.eligible_windows == 1
    assert result.censored_windows == 1
    assert result.uncertain_noneligible_windows == 2
    assert result.eligible_seconds == 10.0
    assert result.censored_seconds == 10.0
    assert result.uncertain_noneligible_seconds == 20.0
    assert result.observable_fraction == 0.25
    assert result.censored_fraction == 0.25
    assert result.uncertain_noneligible_fraction == 0.50
    assert (
        result.observable_fraction
        + result.censored_fraction
        + result.uncertain_noneligible_fraction
        == 1.0
    )


def test_record_contract_rejects_censored_denominator_entry() -> None:
    from interaction_sensing.visit_observation import VisitObservationRecord
    from interaction_sensing.observation_triad import TriadState

    try:
        VisitObservationRecord(
            window_id="bad",
            opportunity_seconds=10,
            status=VisitObservationStatus.CENSORED_UNOBSERVABLE,
            denominator_eligible=True,
            absence_interpretable=False,
            target_score=0.0,
            nuisance_burden=0.0,
            observability_ceiling=0.0,
            observability_limiting_component="target_zone_visibility",
            triad_state=TriadState.UNOBSERVABLE_CENSORED,
            actions=(DiagnosticAction.CENSOR_FROM_DENOMINATOR,),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("censored windows must never enter the denominator")
