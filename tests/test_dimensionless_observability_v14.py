import json
from pathlib import Path

from interaction_sensing.simulation.dimensionless_observability_v14 import (
    DimensionlessPoint,
    IndeterminacyReason,
    LatentRegime,
    VisitInference,
    analyse_phase_point,
    counterfactual_observation_support,
)


ROOT = Path(__file__).resolve().parents[1]


def test_protocol_closes_valid_target_nuisance_coupling_world() -> None:
    protocol = json.loads((ROOT / "benchmarks/v14_dimensionless_world_protocol.json").read_text())
    assert protocol["schema"] == "insepi-v14-dimensionless-world-protocol-v3"
    assert protocol["closed_world_states"] == [
        "baseline: T=0,N=0,C=0",
        "target_only: T=1,N=0,C=0",
        "nuisance_only: T=0,N=1,C=0",
        "target_coupled: T=1,N=0,C=1",
        "target_nuisance_superposed: T=1,N=1,C=0",
        "target_nuisance_coupled: T=1,N=1,C=1",
    ]
    assert protocol["sweep"]["expected_coordinate_count"] == 3136
    assert protocol["sweep"]["expected_deviation_world_count"] == 125440


def test_baseline_is_outside_the_discrimination_question() -> None:
    result = analyse_phase_point(
        DimensionlessPoint(1.0, 1.0, 1.0, 1.0),
        LatentRegime.BASELINE,
    )
    assert result.inference is VisitInference.NO_QUERY
    assert result.indeterminacy_reason is IndeterminacyReason.NONE
    assert result.target_truth is False
    assert result.exogenous_nuisance_truth is False
    assert result.coupling_truth is False


def test_low_nuisance_does_not_imply_observable() -> None:
    point = DimensionlessPoint(pi1=0.01, pi2=1.0, pi3=0.0, pi4=0.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_ONLY)
    assert result.exogenous_nuisance_support == 0.0
    assert result.observation_support < 0.20
    assert result.inference is VisitInference.UNDETERMINED
    assert result.indeterminacy_reason is IndeterminacyReason.INFORMATION_ABSENT


def test_target_driven_local_response_is_not_exogenous_nuisance_by_definition() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=1.0, pi3=0.0, pi4=10.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_COUPLED, seed=4)
    assert result.target_truth is True
    assert result.exogenous_nuisance_truth is False
    assert result.coupling_truth is True
    assert result.indirect_target_route > result.direct_target_route
    assert result.exogenous_nuisance_support == 0.0


def test_target_only_does_not_silently_receive_coupling_when_pi4_is_large() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=1.0, pi3=0.0, pi4=100.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_ONLY, seed=2)
    assert result.coupling_truth is False
    assert result.indirect_target_route == 0.0
    assert result.observation_support == 0.0
    assert result.indeterminacy_reason is IndeterminacyReason.INFORMATION_ABSENT


def test_superposition_truth_is_nonexclusive() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=0.1, pi3=10.0, pi4=0.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_NUISANCE_SUPERPOSED, seed=7)
    assert result.target_truth is True
    assert result.exogenous_nuisance_truth is True
    assert result.coupling_truth is False
    assert result.target_support > 0.0
    assert result.exogenous_nuisance_support > 0.0


def test_coupled_superposition_keeps_all_three_truth_components() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=1.0, pi3=1.0, pi4=1.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_NUISANCE_COUPLED, seed=9)
    assert (result.target_truth, result.exogenous_nuisance_truth, result.coupling_truth) == (
        True,
        True,
        True,
    )


def test_pi2_equal_one_is_not_hardcoded_as_ambiguity_truth() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=1.0, pi3=100.0, pi4=0.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_ONLY, seed=1)
    assert result.observation_support > 0.9
    assert result.indeterminacy_reason is not IndeterminacyReason.INFORMATION_ABSENT
    # Essential ambiguity, if present, must come from prototype overlap rather
    # than the coordinate pi2 == 1 itself. Strong direct evidence should remain
    # available to the phase analyser.
    assert result.direct_target_route > 0.9


def test_indirect_route_can_exist_when_direct_target_amplitude_is_zero() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=0.5, pi3=0.0, pi4=10.0)
    result = analyse_phase_point(point, LatentRegime.TARGET_COUPLED, seed=0)
    assert result.direct_target_route == 0.0
    assert result.indirect_target_route > 0.55
    assert result.observation_support > 0.55


def test_counterfactual_support_is_not_one_minus_nuisance() -> None:
    point = DimensionlessPoint(pi1=10.0, pi2=1.0, pi3=10.0, pi4=0.0)
    support = counterfactual_observation_support(point, coupling_available=False)
    nuisance_world = analyse_phase_point(point, LatentRegime.NUISANCE_ONLY, seed=5)
    assert support > 0.9
    assert nuisance_world.exogenous_nuisance_support > 0.0
    assert nuisance_world.observation_support > 0.9


def test_identifiability_margin_is_bounded_and_seed_reproducible() -> None:
    point = DimensionlessPoint(pi1=3.0, pi2=1.0, pi3=1.0, pi4=1.0)
    a = analyse_phase_point(point, LatentRegime.TARGET_NUISANCE_COUPLED, seed=123)
    b = analyse_phase_point(point, LatentRegime.TARGET_NUISANCE_COUPLED, seed=123)
    assert a == b
    assert 0.0 <= a.identifiability_margin <= 1.0


def test_shorter_window_reduces_direct_counterfactual_support() -> None:
    short = counterfactual_observation_support(
        DimensionlessPoint(0.1, 1.0, 1.0, 0.0), coupling_available=False
    )
    long = counterfactual_observation_support(
        DimensionlessPoint(10.0, 1.0, 1.0, 0.0), coupling_available=False
    )
    assert short < long
