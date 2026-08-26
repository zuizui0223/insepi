from interaction_sensing.simulation.portfolio_single_arm_v6 import (
    active_exploitation_arm,
    generate_single_arm_grid,
)


def test_single_arm_grid_contains_only_uniform_or_one_targeted_arm():
    grid = generate_single_arm_grid(step=0.10, max_exploitation=0.50)
    assert grid
    assert any(active_exploitation_arm(weights) == "uniform" for weights in grid)
    observed = {active_exploitation_arm(weights) for weights in grid}
    assert observed == {"uniform", "pollipi", "insepi", "disagreement"}
    for weights in grid:
        active = sum(
            getattr(weights, arm) > 1e-12
            for arm in ("pollipi", "insepi", "disagreement")
        )
        assert active <= 1
        assert weights.exploration >= 0.50


def test_single_arm_grid_never_conditions_on_prevalence():
    # The grid has no prevalence argument. The exact same candidate policies are
    # considered regardless of the deployment prevalence regime.
    first = generate_single_arm_grid(step=0.10, max_exploitation=0.50)
    second = generate_single_arm_grid(step=0.10, max_exploitation=0.50)
    assert first == second
