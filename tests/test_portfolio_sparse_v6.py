from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights
from interaction_sensing.simulation.portfolio_sparse_v6 import (
    fit_budget_conditioned_schedule,
    generate_sparse_weight_grid,
)


def _rows(n=24):
    pollipi = []
    insepi = []
    for index in range(n):
        true_visit = index % 2 == 0
        state = (
            "strong_visitation_candidate"
            if index % 4 == 0
            else "uncertain_local_activity"
            if index % 4 == 1
            else "environmental_noise"
            if index % 4 == 2
            else "no_activity"
        )
        family = "clean" if index % 3 == 0 else "wind"
        pollipi.append({
            "condition_id": f"calibration-{index}",
            "split": "calibration",
            "true_visit": true_visit,
            "disturbance_family": family,
            "pollipi_state": state,
        })
        insepi.append({
            "condition_id": f"calibration-{index}",
            "split": "calibration",
            "true_visit": true_visit,
            "disturbance_family": family,
            "false_event_risk": 0.75 if index % 5 == 0 else 0.10,
            "missed_event_risk": 0.80 if index % 4 in {2, 3} else 0.05,
            "attribution_risk": 0.65 if index % 6 == 0 else 0.05,
        })
    return pollipi, insepi


def test_sparse_grid_preserves_exploration_but_can_drop_targeted_arms():
    grid = generate_sparse_weight_grid()
    assert grid
    assert all(row.exploration >= 0.30 for row in grid)
    assert any(row.pollipi == 0.0 for row in grid)
    assert any(row.insepi == 0.0 for row in grid)
    assert any(row.disagreement == 0.0 for row in grid)
    assert any(
        sum(value > 0.0 for value in (row.pollipi, row.insepi, row.disagreement)) == 1
        for row in grid
    )


def test_budget_conditioned_schedule_has_one_frozen_weight_vector_per_budget():
    pollipi, insepi = _rows()
    schedule = fit_budget_conditioned_schedule(
        pollipi,
        insepi,
        prevalences=(0.25, 0.75),
        budgets=(0.10, 0.25),
        world_windows=80,
        replicates=2,
        seed=23,
    )
    assert len(schedule.entries) == 2
    for budget in (0.10, 0.25):
        weights = schedule.weights_for(budget)
        assert isinstance(weights, PortfolioWeights)
        assert weights.exploration >= 0.30
        assert abs(sum(weights.to_dict().values()) - 1.0) < 1e-9


def test_budget_conditioned_schedule_does_not_condition_on_prevalence_at_runtime():
    pollipi, insepi = _rows()
    schedule = fit_budget_conditioned_schedule(
        pollipi,
        insepi,
        prevalences=(0.10, 0.50, 0.90),
        budgets=(0.25,),
        world_windows=60,
        replicates=1,
        seed=29,
    )
    # Runtime lookup accepts only the known sensing budget; prevalence is not an
    # argument and therefore cannot select a different portfolio after freeze.
    first = schedule.weights_for(0.25)
    second = schedule.weights_for(0.25)
    assert first == second
