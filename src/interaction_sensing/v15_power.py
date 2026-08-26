"""Parameterized cluster-level planning helpers for V15-v2.

The purpose of this module is to turn the previously unset ``sampling_power_plan``
into an explicit calculation contract **without inventing a final sample size**.
All quantities that materially determine the plan -- MESI, baseline/alternative
rates, cluster size, ICC, alpha and target power -- must be supplied or, for a
single-rate precision calculation, explicitly replaced by the mathematical
worst-case Bernoulli variance p=0.5.

The comparison calculation uses a conservative independent-proportions normal
approximation before applying the standard equal-cluster design effect. V15
systems are evaluated on the same windows/clusters, so positive pairing would
usually improve precision; that gain is deliberately not assumed until a
pre-data pilot supplies a defensible paired-correlation model.

These helpers are development planning tools, not a scientifically frozen power
analysis and not a replacement for the final cluster-level uncertainty model.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import ceil, sqrt
from statistics import NormalDist


class EffectDirection(str, Enum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


@dataclass(frozen=True, slots=True)
class ClusterPlanningAssumptions:
    mean_windows_per_cluster: float
    intracluster_correlation: float
    alpha: float
    target_power: float
    cluster_unit: str

    def __post_init__(self) -> None:
        if self.mean_windows_per_cluster <= 0:
            raise ValueError("mean_windows_per_cluster must be positive")
        if not 0.0 <= self.intracluster_correlation < 1.0:
            raise ValueError("intracluster_correlation must lie in [0, 1)")
        if not 0.0 < self.alpha < 1.0:
            raise ValueError("alpha must lie in (0, 1)")
        if not 0.0 < self.target_power < 1.0:
            raise ValueError("target_power must lie in (0, 1)")
        if not self.cluster_unit.strip():
            raise ValueError("cluster_unit cannot be empty")

    @property
    def design_effect(self) -> float:
        """Equal-cluster approximation ``1 + (m-1) * ICC``."""

        return 1.0 + (self.mean_windows_per_cluster - 1.0) * self.intracluster_correlation


@dataclass(frozen=True, slots=True)
class PrecisionPlan:
    endpoint: str
    expected_rate: float
    used_worst_case_rate: bool
    confidence_level: float
    target_half_width: float
    independent_window_requirement: int
    cluster_design_effect: float
    approximate_cluster_requirement: int
    cluster_unit: str
    method: str = "normal_binomial_precision_with_equal_cluster_design_effect"


@dataclass(frozen=True, slots=True)
class ComparisonPowerPlan:
    endpoint: str
    direction: EffectDirection
    baseline_rate: float
    alternative_rate: float
    minimum_effect_of_scientific_interest: float
    planned_absolute_effect: float
    alpha: float
    target_power: float
    independent_windows_per_system: int
    cluster_design_effect: float
    approximate_cluster_requirement: int
    cluster_unit: str
    method: str = "conservative_independent_proportions_normal_approximation_with_equal_cluster_design_effect"
    pairing_gain_assumed: bool = False


def _validate_probability(name: str, value: float) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")
    return value


def _clusters_for_windows(required_windows: float, assumptions: ClusterPlanningAssumptions) -> int:
    adjusted_windows = required_windows * assumptions.design_effect
    return max(2, int(ceil(adjusted_windows / assumptions.mean_windows_per_cluster)))


def plan_binary_metric_precision(
    *,
    endpoint: str,
    target_half_width: float,
    assumptions: ClusterPlanningAssumptions,
    expected_rate: float | None = None,
) -> PrecisionPlan:
    """Approximate clusters needed for a binary-metric confidence half-width.

    ``expected_rate=None`` is not silently imputed from prior results. It invokes
    the explicit Bernoulli worst case ``p=0.5``, which maximizes ``p(1-p)`` and
    therefore gives the largest normal-approximation sample requirement.
    """

    if not endpoint.strip():
        raise ValueError("endpoint cannot be empty")
    if not 0.0 < target_half_width < 1.0:
        raise ValueError("target_half_width must lie in (0, 1)")

    if expected_rate is None:
        p = 0.5
        worst_case = True
    else:
        p = _validate_probability("expected_rate", expected_rate)
        worst_case = False

    z = NormalDist().inv_cdf(1.0 - assumptions.alpha / 2.0)
    raw_required = (z * z * p * (1.0 - p)) / (target_half_width * target_half_width)
    n_windows = max(1, int(ceil(raw_required)))
    n_clusters = _clusters_for_windows(raw_required, assumptions)

    return PrecisionPlan(
        endpoint=endpoint,
        expected_rate=p,
        used_worst_case_rate=worst_case,
        confidence_level=1.0 - assumptions.alpha,
        target_half_width=target_half_width,
        independent_window_requirement=n_windows,
        cluster_design_effect=assumptions.design_effect,
        approximate_cluster_requirement=n_clusters,
        cluster_unit=assumptions.cluster_unit,
    )


def plan_binary_system_comparison(
    *,
    endpoint: str,
    direction: EffectDirection,
    baseline_rate: float,
    alternative_rate: float,
    minimum_effect_of_scientific_interest: float,
    assumptions: ClusterPlanningAssumptions,
) -> ComparisonPowerPlan:
    """Conservative pre-data power approximation for one binary endpoint.

    The calculation intentionally ignores any efficiency gain from observing the
    two systems on the same windows. It is therefore a planning baseline, not the
    final paired/clustered inferential model. A future freeze may replace it only
    using development-only estimates committed before held-out scoring.
    """

    if not endpoint.strip():
        raise ValueError("endpoint cannot be empty")
    p0 = _validate_probability("baseline_rate", baseline_rate)
    p1 = _validate_probability("alternative_rate", alternative_rate)
    mesi = float(minimum_effect_of_scientific_interest)
    if not 0.0 < mesi <= 1.0:
        raise ValueError("minimum_effect_of_scientific_interest must lie in (0, 1]")

    if direction is EffectDirection.HIGHER_IS_BETTER and p1 <= p0:
        raise ValueError("higher-is-better alternative_rate must exceed baseline_rate")
    if direction is EffectDirection.LOWER_IS_BETTER and p1 >= p0:
        raise ValueError("lower-is-better alternative_rate must be below baseline_rate")

    delta = abs(p1 - p0)
    if delta + 1e-15 < mesi:
        raise ValueError("planned alternative effect is smaller than the declared MESI")

    pbar = 0.5 * (p0 + p1)
    z_alpha = NormalDist().inv_cdf(1.0 - assumptions.alpha / 2.0)
    z_power = NormalDist().inv_cdf(assumptions.target_power)
    variance_null = 2.0 * pbar * (1.0 - pbar)
    variance_alt = p0 * (1.0 - p0) + p1 * (1.0 - p1)
    numerator = z_alpha * sqrt(max(0.0, variance_null)) + z_power * sqrt(max(0.0, variance_alt))
    raw_required = (numerator * numerator) / (delta * delta)
    n_windows = max(1, int(ceil(raw_required)))
    n_clusters = _clusters_for_windows(raw_required, assumptions)

    return ComparisonPowerPlan(
        endpoint=endpoint,
        direction=direction,
        baseline_rate=p0,
        alternative_rate=p1,
        minimum_effect_of_scientific_interest=mesi,
        planned_absolute_effect=delta,
        alpha=assumptions.alpha,
        target_power=assumptions.target_power,
        independent_windows_per_system=n_windows,
        cluster_design_effect=assumptions.design_effect,
        approximate_cluster_requirement=n_clusters,
        cluster_unit=assumptions.cluster_unit,
    )
