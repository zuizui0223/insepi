from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds


def _rows(n=20):
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
            "false_event_risk": 0.7 if index % 5 == 0 else 0.1,
            "missed_event_risk": 0.8 if index % 4 in {2, 3} else 0.05,
            "attribution_risk": 0.6 if index % 6 == 0 else 0.05,
        })
    return pollipi, insepi


def test_shared_world_fit_is_grid_order_invariant():
    pollipi, insepi = _rows()
    grid = [
        PortfolioWeights(0.4, 0.2, 0.2, 0.2),
        PortfolioWeights(0.5, 0.2, 0.2, 0.1),
        PortfolioWeights(0.3, 0.3, 0.2, 0.2),
    ]
    forward = fit_minimax_portfolio_shared_worlds(
        pollipi,
        insepi,
        prevalences=(0.25, 0.75),
        budgets=(0.25,),
        world_windows=80,
        replicates=2,
        seed=11,
        grid=grid,
    )
    reverse = fit_minimax_portfolio_shared_worlds(
        pollipi,
        insepi,
        prevalences=(0.25, 0.75),
        budgets=(0.25,),
        world_windows=80,
        replicates=2,
        seed=11,
        grid=list(reversed(grid)),
    )
    assert forward.weights == reverse.weights
    assert forward.worst_joint_recall == reverse.worst_joint_recall
    assert forward.worst_tv_distance == reverse.worst_tv_distance
