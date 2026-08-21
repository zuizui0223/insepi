from interaction_sensing.simulation.frozen_portfolio_v6 import (
    V6_DEV_MAX_TV_DISTANCE,
    V6_DEV_MEAN_JOINT_RATIO,
    V6_DEV_RATIO_FLOOR,
    V6_DEV_TV_CEILING,
    V6_DEV_WORST_JOINT_RATIO,
    V6_FROZEN_WEIGHTS,
    V6_METHOD_NAME,
    select_frozen_v6_indices,
)
from interaction_sensing.simulation.portfolio_theory_v6 import expected_tv_upper_bound


def _world(n=40):
    rows = []
    for index in range(n):
        state = (
            "strong_visitation_candidate"
            if index % 4 == 0
            else "uncertain_local_activity"
            if index % 4 == 1
            else "environmental_noise"
            if index % 4 == 2
            else "no_activity"
        )
        p = {
            "condition_id": f"w-{index}",
            "true_visit": index % 2 == 0,
            "pollipi_state": state,
            "disturbance_family": "clean" if index % 3 == 0 else "wind",
        }
        i = {
            "condition_id": f"w-{index}",
            "true_visit": index % 2 == 0,
            "false_event_risk": 0.7 if index % 5 == 0 else 0.1,
            "missed_event_risk": 0.8 if index % 4 in {2, 3} else 0.05,
            "attribution_risk": 0.6 if index % 6 == 0 else 0.05,
            "disturbance_family": p["disturbance_family"],
        }
        rows.append((p, i))
    return rows


def test_frozen_v6_weights_and_claim_ceiling_are_exact():
    assert V6_METHOD_NAME == "exploration_guarded_dual_observer_portfolio_v6"
    assert V6_FROZEN_WEIGHTS.exploration == 0.50
    assert V6_FROZEN_WEIGHTS.pollipi == 0.10
    assert V6_FROZEN_WEIGHTS.insepi == 0.40
    assert V6_FROZEN_WEIGHTS.disagreement == 0.00
    assert V6_DEV_RATIO_FLOOR == 1.00
    assert V6_DEV_TV_CEILING == 0.25
    assert V6_DEV_WORST_JOINT_RATIO == 1.00846
    assert V6_DEV_MEAN_JOINT_RATIO == 1.11642
    assert V6_DEV_MAX_TV_DISTANCE == 0.21919


def test_frozen_v6_has_an_analytical_expected_tv_ceiling_from_exploration():
    assert expected_tv_upper_bound(V6_FROZEN_WEIGHTS.exploration) == 0.50


def test_frozen_v6_runtime_does_not_accept_prevalence_or_fit_weights():
    selected, by_arm = select_frozen_v6_indices(
        _world(), budget_fraction=0.25, seed=17
    )
    assert len(selected) == 10
    assert by_arm["exploration"] == 5
    assert by_arm["disagreement"] == 0


def test_frozen_v6_selection_is_unchanged_if_latent_truth_is_flipped():
    original = _world()
    flipped = []
    for p, i in original:
        p2, i2 = dict(p), dict(i)
        p2["true_visit"] = not bool(p2["true_visit"])
        i2["true_visit"] = not bool(i2["true_visit"])
        flipped.append((p2, i2))

    first, first_arms = select_frozen_v6_indices(
        original, budget_fraction=0.25, seed=19
    )
    second, second_arms = select_frozen_v6_indices(
        flipped, budget_fraction=0.25, seed=19
    )
    assert first == second
    assert first_arms == second_arms
