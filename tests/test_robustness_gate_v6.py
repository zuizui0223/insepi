from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights
from interaction_sensing.simulation.robustness_gate_v6 import evaluate_candidate_against_uniform


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
            "condition_id": f"test-{index}",
            "split": "test",
            "true_visit": true_visit,
            "disturbance_family": family,
            "pollipi_state": state,
        })
        insepi.append({
            "condition_id": f"test-{index}",
            "split": "test",
            "true_visit": true_visit,
            "disturbance_family": family,
            "false_event_risk": 0.7 if index % 5 == 0 else 0.1,
            "missed_event_risk": 0.8 if index % 4 in {2, 3} else 0.05,
            "attribution_risk": 0.6 if index % 6 == 0 else 0.05,
        })
    return pollipi, insepi


def test_robustness_gate_covers_every_requested_regime_and_budget_exactly():
    pollipi, insepi = _rows()
    result = evaluate_candidate_against_uniform(
        pollipi,
        insepi,
        weights=PortfolioWeights(0.8, 0.2, 0.0, 0.0),
        prevalences=(0.25, 0.75),
        budgets=(0.10, 0.25),
        world_windows=80,
        replicates=3,
        seed=41,
        ratio_floor=0.0,
        tv_ceiling=1.0,
    )
    assert len(result.regimes) == 4
    assert {(row.prevalence, row.budget_fraction) for row in result.regimes} == {
        (0.25, 0.10),
        (0.25, 0.25),
        (0.75, 0.10),
        (0.75, 0.25),
    }
    assert result.passes_development_gate is True
    assert 0 <= result.n_regimes_at_or_above_uniform <= 4


def test_tv_ceiling_is_a_hard_gate():
    pollipi, insepi = _rows()
    result = evaluate_candidate_against_uniform(
        pollipi,
        insepi,
        weights=PortfolioWeights(0.5, 0.5, 0.0, 0.0),
        prevalences=(0.5,),
        budgets=(0.25,),
        world_windows=80,
        replicates=3,
        seed=43,
        ratio_floor=0.0,
        tv_ceiling=0.0,
    )
    assert result.max_tv_distance >= 0.0
    assert result.passes_development_gate is (result.max_tv_distance <= 0.0)
