"""Finite-budget guarantees for exploration-guarded sampling.

These results complement the ideal-mixture exploration theorem. They apply to an
actual finite population of N windows when q_u slots are reserved for simple
random exploration without replacement before any targeted additions are made.
Targeted selection may add inclusion probability but cannot remove the uniform
component.
"""
from __future__ import annotations

from math import comb


def uniform_inclusion_floor(population_size: int, exploration_quota: int) -> float:
    """Minimum overall inclusion probability contributed by exploration alone."""
    if population_size <= 0:
        raise ValueError("population_size must be positive")
    if not 0 <= exploration_quota <= population_size:
        raise ValueError("exploration_quota must lie in [0, population_size]")
    return exploration_quota / population_size


def family_miss_probability(
    population_size: int,
    family_size: int,
    exploration_quota: int,
) -> float:
    """Exact probability that uniform exploration misses an entire family.

    Sampling is simple random without replacement. The probability is
    C(N-m, q_u) / C(N, q_u), with the natural zero case when q_u > N-m.
    """
    if population_size <= 0:
        raise ValueError("population_size must be positive")
    if not 0 <= family_size <= population_size:
        raise ValueError("family_size must lie in [0, population_size]")
    if not 0 <= exploration_quota <= population_size:
        raise ValueError("exploration_quota must lie in [0, population_size]")
    if exploration_quota > population_size - family_size:
        return 0.0
    return comb(population_size - family_size, exploration_quota) / comb(
        population_size, exploration_quota
    )


def max_uniform_target_weight_ratio(
    total_budget: int,
    exploration_quota: int,
) -> float:
    """Bound target-design to adaptive inclusion weighting by B / q_u.

    A simple-random target design selecting B of N windows gives each window
    inclusion probability B/N. The guarded design has overall inclusion
    probability at least q_u/N because targeted arms cannot remove exploration
    selections. Therefore (B/N)/pi_i <= B/q_u.
    """
    if total_budget <= 0:
        raise ValueError("total_budget must be positive")
    if not 0 < exploration_quota <= total_budget:
        raise ValueError("exploration_quota must lie in (0, total_budget]")
    return total_budget / exploration_quota
