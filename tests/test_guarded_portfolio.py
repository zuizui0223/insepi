from interaction_sensing.guarded_portfolio import (
    GuardedPortfolio,
    select_guarded_indices,
)
from interaction_sensing.simulation.observer_portfolio_v6 import (
    PortfolioWeights,
    arm_score,
    select_portfolio_indices,
)


def _world(repeats=7):
    states = [
        ("no_activity", 0.00, 0.00, 0.00),
        ("strong_visitation_candidate", 0.00, 0.00, 0.00),
        ("uncertain_local_activity", 0.25, 0.45, 0.10),
        ("environmental_noise", 0.80, 0.35, 0.20),
        ("no_activity", 0.10, 0.90, 0.30),
        ("strong_visitation_candidate", 0.75, 0.40, 0.65),
        ("environmental_noise", 0.70, 0.72, 0.75),
        ("no_activity", 0.00, 0.00, 0.00),
    ]
    rows = []
    for repeat in range(repeats):
        for index, (state, false_risk, missed_risk, attribution_risk) in enumerate(states):
            p = {
                "condition_id": f"r{repeat}-i{index}",
                "pollipi_state": state,
                "true_visit": bool((repeat + index) % 2),
                "disturbance_family": "clean" if index < 2 else "dummy",
            }
            i = {
                "condition_id": p["condition_id"],
                "false_event_risk": false_risk,
                "missed_event_risk": missed_risk,
                "attribution_risk": attribution_risk,
                "disturbance_family": p["disturbance_family"],
            }
            rows.append((p, i))
    return rows


def _generic_scores(world):
    return [
        {
            "evidence": arm_score("pollipi", p, i),
            "observability": arm_score("insepi", p, i),
        }
        for p, i in world
    ]


def test_frozen_v6_reference_weights_are_generic():
    portfolio = GuardedPortfolio.frozen_v6_reference()
    assert portfolio.exploration == 0.5
    assert portfolio.arms == (("evidence", 0.1), ("observability", 0.4))


def test_generic_reference_matches_frozen_v6_selection_for_zero_disagreement_policy():
    world = _world(repeats=13)
    scores = _generic_scores(world)
    frozen = PortfolioWeights(0.5, 0.1, 0.4, 0.0)
    generic = GuardedPortfolio.frozen_v6_reference()

    for budget in (0.10, 0.25, 0.50, 0.73):
        for seed in (1, 20260821, 998877):
            frozen_selected, _ = select_portfolio_indices(
                world,
                budget_fraction=budget,
                weights=frozen,
                seed=seed,
            )
            generic_selected, _ = select_guarded_indices(
                scores,
                budget_fraction=budget,
                portfolio=generic,
                seed=seed,
            )
            assert generic_selected == frozen_selected


def test_generic_selector_does_not_need_latent_truth():
    scores = [
        {"evidence": 1.0 if index % 5 == 0 else 0.0, "observability": (index % 7) / 6}
        for index in range(80)
    ]
    selected_a, _ = select_guarded_indices(
        scores,
        budget_fraction=0.25,
        portfolio=GuardedPortfolio.frozen_v6_reference(),
        seed=42,
    )
    # There is deliberately no truth vector to change: the public selector contract
    # contains acquisition scores only.
    selected_b, _ = select_guarded_indices(
        list(scores),
        budget_fraction=0.25,
        portfolio=GuardedPortfolio.frozen_v6_reference(),
        seed=42,
    )
    assert selected_a == selected_b


def test_empty_targeted_signal_spills_back_to_uniform_and_preserves_exact_budget():
    scores = [{"evidence": 0.0, "observability": 0.0} for _ in range(101)]
    selected, counts = select_guarded_indices(
        scores,
        budget_fraction=0.25,
        portfolio=GuardedPortfolio.frozen_v6_reference(),
        seed=7,
    )
    assert len(selected) == round(101 * 0.25)
    assert counts["evidence"] == 0
    assert counts["observability"] == 0
    assert counts["spillover_uniform"] > 0
