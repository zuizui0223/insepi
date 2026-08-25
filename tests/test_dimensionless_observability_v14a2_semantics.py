from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    observation_support,
    signature_for,
)


def test_direct_actor_signal_does_not_leak_into_coupled_scene_route() -> None:
    point = SpatiotemporalPoint(3.0, 1.0, 3.0, 0.0, 1.0, 16.0)
    signature = signature_for(point, LatentRegime.TARGET_ONLY, seed=1)
    assert signature.direct_target_signal_fraction > 0.99
    assert signature.local_excess_motion_fraction == 0.0


def test_unrealised_coupling_does_not_rescue_target_only_observation_support() -> None:
    point = SpatiotemporalPoint(3.0, 1.0, 0.0, 10.0, 1.0, 16.0)
    assert observation_support(point, coupling_available=False) == 0.0
    assert observation_support(point, coupling_available=True) > 0.0


def test_coupling_enters_observed_spatial_signature_instead_of_being_truth_subtracted() -> None:
    point = SpatiotemporalPoint(3.0, 1.0, 0.0, 1.0, 1.0, 16.0)
    uncoupled = signature_for(point, LatentRegime.TARGET_ONLY, seed=2)
    coupled = signature_for(point, LatentRegime.TARGET_COUPLED, seed=2)
    assert uncoupled.spatial_structure_function == 0.0
    assert uncoupled.local_excess_motion_fraction == 0.0
    assert coupled.spatial_structure_function > 0.0
    assert coupled.local_excess_motion_fraction > 0.0
