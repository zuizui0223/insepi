from interaction_sensing.observation_triad import (
    InferentialStatus,
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
    ObservationTriadPolicy,
    ProcessPreservingObservationTriadPolicy,
    TargetEvidence,
    TriadState,
)
from interaction_sensing.visit_observation import (
    DiagnosticAction,
    VisitObservationStatus,
    visit_record_from_interpretation,
)


def support(value: float) -> ObservationSupport:
    return ObservationSupport(value, value, value, value, value)


def test_v14a_policy_is_retained_for_reproducibility() -> None:
    result = ObservationTriadPolicy().decide(
        TargetEvidence(0.90),
        NuisanceEvidence(0.90, 0.20, 0.20),
        support(0.90),
    )
    assert result.state is TriadState.TARGET_NUISANCE_CONFLICT
    assert result.inferential_status is InferentialStatus.AMBIGUOUS


def test_v14b_preserves_observable_target_nuisance_superposition() -> None:
    result = ProcessPreservingObservationTriadPolicy().decide(
        TargetEvidence(0.90),
        NuisanceEvidence(0.90, 0.20, 0.20, dominant_source="background_motion"),
        support(0.90),
    )
    assert result.availability is ObservationAvailability.OBSERVABLE
    assert result.state is TriadState.TARGET_NUISANCE_SUPERPOSITION
    assert result.inferential_status is InferentialStatus.POSITIVE_CANDIDATE
    assert result.audit_priority is True
    assert result.retain_target_clip is True
    assert result.nuisance_burden == 0.90


def test_superposition_remains_positive_downstream_without_dropping_nuisance_metadata() -> None:
    interpretation = ProcessPreservingObservationTriadPolicy().decide(
        TargetEvidence(0.90, source_state="target_observer_high"),
        NuisanceEvidence(0.85, 0.20, 0.30, dominant_source="coherent_sway"),
        support(0.90),
    )
    record = visit_record_from_interpretation("superposed", 10.0, interpretation)
    assert record.status is VisitObservationStatus.VISIT_CANDIDATE
    assert record.triad_state is TriadState.TARGET_NUISANCE_SUPERPOSITION
    assert record.nuisance_burden == 0.85
    assert DiagnosticAction.RETAIN_TARGET_CLIP in record.actions
    assert DiagnosticAction.RECORD_HIGH_RES_CONTEXT in record.actions


def test_compromised_support_takes_precedence_over_superposition() -> None:
    result = ProcessPreservingObservationTriadPolicy().decide(
        TargetEvidence(0.90),
        NuisanceEvidence(0.90, 0.20, 0.20),
        support(0.50),
    )
    assert result.availability is ObservationAvailability.COMPROMISED
    assert result.state is TriadState.TARGET_OBSERVABILITY_CONFLICT
    assert result.inferential_status is InferentialStatus.AMBIGUOUS
