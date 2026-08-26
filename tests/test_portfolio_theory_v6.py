from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights
from interaction_sensing.simulation.portfolio_theory_v6 import (
    expected_tv_upper_bound,
    exploration_quota,
    uniform_inclusion_probability_lower_bound,
)


def test_expected_tv_bound_shrinks_monotonically_with_exploration():
    assert expected_tv_upper_bound(0.0) == 1.0
    assert expected_tv_upper_bound(0.5) == 0.5
    assert expected_tv_upper_bound(1.0) == 0.0
    assert expected_tv_upper_bound(0.7) < expected_tv_upper_bound(0.5)


def test_uniform_inclusion_lower_bound_is_strictly_positive_for_v6_candidate():
    weights = PortfolioWeights(0.5, 0.1, 0.4, 0.0)
    quota = exploration_quota(100, weights)
    assert quota == 50
    lower = uniform_inclusion_probability_lower_bound(1000, 0.10, weights)
    assert lower == 0.05


def test_targeted_spillover_cannot_reduce_the_conservative_exploration_quota():
    weights = PortfolioWeights(0.6, 0.1, 0.3, 0.0)
    assert exploration_quota(25, weights) == 15
