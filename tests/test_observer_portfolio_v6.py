from interaction_sensing.simulation.observer_portfolio_v6 import (
    PortfolioWeights,
    fit_minimax_portfolio,
    generate_weight_grid,
    select_portfolio_indices,
)


def _pair(index: int, *, true_visit: bool, split: str = "calibration"):
    pollipi_state = (
        "strong_visitation_candidate"
        if index % 4 == 0
        else "uncertain_local_activity"
        if index % 4 == 1
        else "environmental_noise"
        if index % 4 == 2
        else "no_activity"
    )
    pollipi = {
        "condition_id": f"{split}-{index}",
        "split": split,
        "true_visit": true_visit,
        "disturbance_family": "clean" if index % 3 == 0 else "wind",
        "pollipi_state": pollipi_state,
    }
    insepi = {
        "condition_id": f"{split}-{index}",
        "split": split,
        "true_visit": true_visit,
        "disturbance_family": pollipi["disturbance_family"],
        "false_event_risk": 0.75 if index % 5 == 0 else 0.10,
        "missed_event_risk": 0.80 if index % 4 in {2, 3} else 0.05,
        "attribution_risk": 0.65 if index % 6 == 0 else 0.05,
    }
    return pollipi, insepi


def _rows(n: int = 24, *, split: str = "calibration"):
    pairs = [_pair(index, true_visit=index % 2 == 0, split=split) for index in range(n)]
    return [p for p, _ in pairs], [i for _, i in pairs]


def test_portfolio_requires_positive_exploration():
    try:
        PortfolioWeights(0.0, 0.3, 0.3, 0.4)
    except ValueError as exc:
        assert "exploration" in str(exc)
    else:
        raise AssertionError("zero exploration must be rejected")


def test_portfolio_selection_satisfies_exact_budget_and_uniform_floor():
    pollipi, insepi = _rows(40)
    world = list(zip(pollipi, insepi, strict=True))
    weights = PortfolioWeights(0.4, 0.2, 0.2, 0.2)
    selected, by_arm = select_portfolio_indices(
        world,
        budget_fraction=0.25,
        weights=weights,
        seed=19,
    )
    assert len(selected) == 10
    assert by_arm["exploration"] == 4
    assert sum(by_arm.values()) == 10


def test_portfolio_selection_does_not_read_latent_truth():
    pollipi, insepi = _rows(32)
    original = list(zip(pollipi, insepi, strict=True))
    flipped = []
    for p, i in original:
        p2 = dict(p)
        i2 = dict(i)
        p2["true_visit"] = not bool(p2["true_visit"])
        i2["true_visit"] = not bool(i2["true_visit"])
        flipped.append((p2, i2))

    weights = PortfolioWeights(0.4, 0.2, 0.2, 0.2)
    selected_original, arms_original = select_portfolio_indices(
        original, budget_fraction=0.25, weights=weights, seed=31
    )
    selected_flipped, arms_flipped = select_portfolio_indices(
        flipped, budget_fraction=0.25, weights=weights, seed=31
    )
    assert selected_original == selected_flipped
    assert arms_original == arms_flipped


def test_default_weight_grid_keeps_all_observers_and_exploration():
    grid = generate_weight_grid()
    assert grid
    assert all(row.exploration >= 0.30 for row in grid)
    assert all(row.pollipi >= 0.10 for row in grid)
    assert all(row.insepi >= 0.10 for row in grid)
    assert all(row.disagreement >= 0.10 for row in grid)


def test_minimax_fit_ignores_test_rows():
    cal_p, cal_i = _rows(20, split="calibration")
    test_p, test_i = _rows(20, split="test")
    # Make the test split intentionally pathological. It must not alter V6 fitting.
    for row in test_p:
        row["pollipi_state"] = "strong_visitation_candidate"
        row["true_visit"] = False
    for row in test_i:
        row["false_event_risk"] = 1.0
        row["missed_event_risk"] = 1.0
        row["attribution_risk"] = 1.0
        row["true_visit"] = False

    grid = [
        PortfolioWeights(0.4, 0.2, 0.2, 0.2),
        PortfolioWeights(0.5, 0.2, 0.2, 0.1),
    ]
    fit_cal = fit_minimax_portfolio(
        cal_p,
        cal_i,
        prevalences=(0.25, 0.75),
        budgets=(0.25,),
        world_windows=80,
        replicates=2,
        seed=7,
        grid=grid,
    )
    fit_with_test = fit_minimax_portfolio(
        cal_p + test_p,
        cal_i + test_i,
        prevalences=(0.25, 0.75),
        budgets=(0.25,),
        world_windows=80,
        replicates=2,
        seed=7,
        grid=grid,
    )
    assert fit_cal.weights == fit_with_test.weights
    assert fit_cal.worst_joint_recall == fit_with_test.worst_joint_recall
