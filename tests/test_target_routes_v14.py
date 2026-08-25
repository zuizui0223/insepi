import pytest

from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationSupport,
    ObservationTriadPolicy,
    TriadState,
)
from interaction_sensing.target_routes import TargetEvidenceRoute, TargetRouteEvidence


def test_coupled_route_can_rescue_weak_direct_insect_signal() -> None:
    evidence = TargetRouteEvidence(
        direct_insect_score=0.10,
        coupled_response_score=0.90,
        target_link_confidence=0.90,
    )
    assert evidence.coupled_target_score == pytest.approx(0.81)
    assert evidence.aggregate_score == pytest.approx(0.81)
    assert evidence.route() is TargetEvidenceRoute.COUPLED


def test_arbitrary_flower_motion_is_not_target_evidence_without_target_link() -> None:
    evidence = TargetRouteEvidence(
        direct_insect_score=0.05,
        coupled_response_score=0.95,
        target_link_confidence=0.10,
    )
    assert evidence.coupled_target_score == pytest.approx(0.095)
    assert evidence.aggregate_score == pytest.approx(0.095)
    assert evidence.route() is TargetEvidenceRoute.NONE


def test_direct_and_coupled_routes_are_preserved_when_both_are_strong() -> None:
    evidence = TargetRouteEvidence(0.90, 0.85, 0.90)
    assert evidence.route() is TargetEvidenceRoute.BOTH
    target = evidence.to_target_evidence()
    assert target.score == pytest.approx(0.90)
    assert target.source_state == "both"


def test_coupled_target_evidence_can_still_conflict_with_exogenous_nuisance() -> None:
    evidence = TargetRouteEvidence(0.10, 0.95, 0.90)
    result = ObservationTriadPolicy().decide(
        evidence.to_target_evidence(),
        NuisanceEvidence(0.80, 0.20, 0.30, dominant_source="background_vegetation_motion"),
        ObservationSupport(0.95, 0.95, 0.95, 0.95, 0.95),
    )
    assert result.state is TriadState.TARGET_NUISANCE_CONFLICT


def test_target_route_does_not_import_nuisance_decision_logic() -> None:
    # The target route is calculated entirely from target-side measurements.
    # Nuisance enters only later in the triad, preserving epistemic separation.
    evidence = TargetRouteEvidence(0.20, 0.80, 0.90)
    assert evidence.aggregate_score == pytest.approx(0.72)
    assert evidence.route() is TargetEvidenceRoute.COUPLED
