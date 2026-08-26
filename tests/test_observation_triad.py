from interaction_sensing.observation_triad import (
    InferentialStatus,
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
    TriadState,
)


def support(value: float) -> ObservationSupport:
    return ObservationSupport(
        target_zone_coverage=value,
        target_zone_visibility=value,
        spatial_resolution=value,
        photometric_sufficiency=value,
        temporal_continuity=value,
    )


def test_low_nuisance_does_not_imply_observable() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.05),
        NuisanceEvidence(0.05, 0.05, 0.05),
        support(0.10),
    )
    assert result.availability is ObservationAvailability.UNOBSERVABLE
    assert result.state is TriadState.UNOBSERVABLE_CENSORED
    assert result.inferential_status is InferentialStatus.CENSORED
    assert result.absence_interpretable is False
    assert result.denominator_eligible is False


def test_high_nuisance_does_not_imply_unobservable() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.82),
        NuisanceEvidence(0.82, 0.35, 0.30, dominant_source="background_motion"),
        support(0.90),
    )
    assert result.availability is ObservationAvailability.OBSERVABLE
    assert result.state is TriadState.TARGET_NUISANCE_CONFLICT
    assert result.inferential_status is InferentialStatus.AMBIGUOUS
    assert result.audit_priority is True
    assert result.retain_target_clip is True


def test_observable_quiet_window_can_support_negative_evidence() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.10),
        NuisanceEvidence(0.05, 0.10, 0.05),
        support(0.95),
    )
    assert result.state is TriadState.QUIET_OBSERVABLE
    assert result.inferential_status is InferentialStatus.NEGATIVE_EVIDENCE
    assert result.absence_interpretable is True
    assert result.denominator_eligible is True


def test_missed_event_risk_blocks_absence_even_when_geometry_is_observable() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.10),
        NuisanceEvidence(0.20, 0.85, 0.20, dominant_source="occlusion"),
        support(0.90),
    )
    assert result.availability is ObservationAvailability.OBSERVABLE
    assert result.state is TriadState.NUISANCE_DOMINATED_OR_POSSIBLE_MISS
    assert result.absence_interpretable is False
    assert result.denominator_eligible is False


def test_target_candidate_under_compromised_support_is_not_clean_positive() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.90),
        NuisanceEvidence(0.10, 0.10, 0.10),
        support(0.50),
    )
    assert result.availability is ObservationAvailability.COMPROMISED
    assert result.state is TriadState.TARGET_OBSERVABILITY_CONFLICT
    assert result.inferential_status is InferentialStatus.AMBIGUOUS
    assert result.retain_target_clip is True
    assert result.audit_priority is True


def test_unobservable_overrides_a_high_target_score_without_deleting_candidate() -> None:
    policy = ObservationTriadPolicy()
    result = policy.decide(
        TargetEvidence(0.95, source_state="strong_visitation_candidate"),
        NuisanceEvidence(0.05, 0.05, 0.05),
        support(0.20),
    )
    assert result.state is TriadState.UNOBSERVABLE_CENSORED
    assert result.inferential_status is InferentialStatus.CENSORED
    assert result.retain_target_clip is True
    assert result.absence_interpretable is False


def test_stable_non_target_context_is_not_automatically_nuisance() -> None:
    evidence = NuisanceEvidence(0.0, 0.0, 0.0, dominant_source="stable_context")
    assert evidence.burden == 0.0


def test_support_ceiling_is_independent_of_nuisance_risk() -> None:
    good = ObservationSupport(0.95, 0.95, 0.95, 0.95, 0.95)
    bad = ObservationSupport(0.95, 0.10, 0.95, 0.95, 0.95)
    assert good.ceiling == 0.95
    assert bad.ceiling == 0.10


def test_input_ranges_are_fail_closed() -> None:
    try:
        TargetEvidence(1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range target score must fail")

    try:
        ObservationTriadPolicy(target_low_threshold=0.8, target_high_threshold=0.7)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid threshold ordering must fail")
