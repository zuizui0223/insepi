import pytest

from interaction_sensing.v15_power import (
    ClusterPlanningAssumptions,
    EffectDirection,
    plan_binary_metric_precision,
    plan_binary_system_comparison,
)


def assumptions(*, icc: float = 0.1, windows: float = 20.0) -> ClusterPlanningAssumptions:
    return ClusterPlanningAssumptions(
        mean_windows_per_cluster=windows,
        intracluster_correlation=icc,
        alpha=0.05,
        target_power=0.80,
        cluster_unit="recording_day_x_focal_scene",
    )


def test_design_effect_is_one_without_intracluster_correlation() -> None:
    assert assumptions(icc=0.0).design_effect == 1.0
    assert assumptions(icc=0.2, windows=10).design_effect == pytest.approx(2.8)


def test_precision_plan_uses_explicit_worst_case_when_rate_is_unknown() -> None:
    worst = plan_binary_metric_precision(
        endpoint="visit_recall_on_observable_truth",
        target_half_width=0.05,
        assumptions=assumptions(),
        expected_rate=None,
    )
    known = plan_binary_metric_precision(
        endpoint="visit_recall_on_observable_truth",
        target_half_width=0.05,
        assumptions=assumptions(),
        expected_rate=0.10,
    )
    assert worst.used_worst_case_rate is True
    assert worst.expected_rate == 0.5
    assert worst.independent_window_requirement > known.independent_window_requirement
    assert worst.approximate_cluster_requirement >= known.approximate_cluster_requirement


def test_higher_icc_requires_more_clusters_for_same_precision_target() -> None:
    low = plan_binary_metric_precision(
        endpoint="unobservable_recall",
        target_half_width=0.05,
        assumptions=assumptions(icc=0.01),
    )
    high = plan_binary_metric_precision(
        endpoint="unobservable_recall",
        target_half_width=0.05,
        assumptions=assumptions(icc=0.30),
    )
    assert high.cluster_design_effect > low.cluster_design_effect
    assert high.approximate_cluster_requirement > low.approximate_cluster_requirement


def test_comparison_plan_requires_directionally_valid_effect_at_least_mesi() -> None:
    with pytest.raises(ValueError, match="must exceed"):
        plan_binary_system_comparison(
            endpoint="visit_recall_on_observable_truth",
            direction=EffectDirection.HIGHER_IS_BETTER,
            baseline_rate=0.8,
            alternative_rate=0.7,
            minimum_effect_of_scientific_interest=0.05,
            assumptions=assumptions(),
        )

    with pytest.raises(ValueError, match="smaller than the declared MESI"):
        plan_binary_system_comparison(
            endpoint="observable_false_censor_rate",
            direction=EffectDirection.LOWER_IS_BETTER,
            baseline_rate=0.20,
            alternative_rate=0.17,
            minimum_effect_of_scientific_interest=0.05,
            assumptions=assumptions(),
        )


def test_larger_planned_effect_needs_fewer_clusters_under_same_assumptions() -> None:
    small = plan_binary_system_comparison(
        endpoint="forced_missed_visit_as_absence_rate",
        direction=EffectDirection.LOWER_IS_BETTER,
        baseline_rate=0.30,
        alternative_rate=0.20,
        minimum_effect_of_scientific_interest=0.10,
        assumptions=assumptions(),
    )
    large = plan_binary_system_comparison(
        endpoint="forced_missed_visit_as_absence_rate",
        direction=EffectDirection.LOWER_IS_BETTER,
        baseline_rate=0.30,
        alternative_rate=0.10,
        minimum_effect_of_scientific_interest=0.10,
        assumptions=assumptions(),
    )
    assert large.approximate_cluster_requirement < small.approximate_cluster_requirement
    assert small.pairing_gain_assumed is False
    assert "conservative_independent_proportions" in small.method


def test_planner_requires_cluster_and_error_contract_inputs() -> None:
    with pytest.raises(ValueError, match="cluster_unit"):
        ClusterPlanningAssumptions(10, 0.1, 0.05, 0.8, "")
    with pytest.raises(ValueError, match="intracluster_correlation"):
        ClusterPlanningAssumptions(10, 1.0, 0.05, 0.8, "block")
    with pytest.raises(ValueError, match="target_half_width"):
        plan_binary_metric_precision(
            endpoint="x",
            target_half_width=0.0,
            assumptions=assumptions(),
        )
