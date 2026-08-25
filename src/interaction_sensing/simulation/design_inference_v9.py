"""Design-based inference utilities for the V9 validation generation.

V9 treats the initial guarded-portfolio exploration draw as the probability-sample
reference design. Targeted selections may improve event/error recovery, but they
are not assumed ignorable for ecological prevalence inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from math import exp, floor, lgamma, sqrt
from random import Random
from statistics import NormalDist
from typing import Sequence

from interaction_sensing.guarded_portfolio import GuardedPortfolio, select_guarded_indices
from interaction_sensing.simulation.generality_v8 import Window


@dataclass(frozen=True, slots=True)
class InferenceSelection:
    selected: frozenset[int]
    protected_exploration: frozenset[int]
    selected_by_arm: dict[str, int]


@dataclass(frozen=True, slots=True)
class Interval:
    lower: float
    upper: float

    @property
    def width(self) -> float:
        return self.upper - self.lower

    def covers(self, value: float, *, tol: float = 1e-12) -> bool:
        return self.lower - tol <= value <= self.upper + tol


def _quota_counts(total: int, portfolio: GuardedPortfolio) -> dict[str, int]:
    names = ("exploration", *(name for name, _ in portfolio.arms))
    values = (portfolio.exploration, *(weight for _, weight in portfolio.arms))
    raw = [total * value for value in values]
    counts = [floor(value) for value in raw]
    remainder = total - sum(counts)
    order = sorted(
        range(len(names)),
        key=lambda index: (raw[index] - counts[index], values[index], -index),
        reverse=True,
    )
    for index in order[:remainder]:
        counts[index] += 1
    return dict(zip(names, counts, strict=True))


def protected_exploration_indices(
    population_size: int,
    *,
    budget_fraction: float,
    seed: int,
    portfolio: GuardedPortfolio | None = None,
) -> frozenset[int]:
    """Reconstruct the initial SRSWOR draw used by the guarded selector.

    Only the initial exploration quota belongs to the reference design. Later
    uniform spillover after targeted selection is deliberately excluded because
    its candidate pool has already been altered by targeted selections.
    """
    if population_size <= 0:
        raise ValueError("population_size must be positive")
    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0, 1]")
    if portfolio is None:
        portfolio = GuardedPortfolio.frozen_v6_reference()
    selected_n = max(1, round(population_size * budget_fraction))
    quota = _quota_counts(selected_n, portfolio)["exploration"]
    order = list(range(population_size))
    Random(seed).shuffle(order)
    return frozenset(order[:quota])


def select_frozen_v6_with_reference(
    world: Sequence[Window],
    *,
    budget_fraction: float,
    seed: int,
) -> InferenceSelection:
    if not world:
        raise ValueError("world cannot be empty")
    portfolio = GuardedPortfolio.frozen_v6_reference()
    score_rows = [
        {"evidence": float(row.evidence), "observability": float(row.observability)}
        for row in world
    ]
    selected, selected_by_arm = select_guarded_indices(
        score_rows,
        budget_fraction=budget_fraction,
        portfolio=portfolio,
        seed=seed,
    )
    reference = protected_exploration_indices(
        len(world), budget_fraction=budget_fraction, seed=seed, portfolio=portfolio
    )
    if not reference.issubset(selected):
        raise AssertionError("protected exploration draw is not contained in selected set")
    if len(reference) != selected_by_arm["exploration"]:
        raise AssertionError("protected exploration size differs from selector provenance")
    return InferenceSelection(
        selected=frozenset(selected),
        protected_exploration=reference,
        selected_by_arm=dict(selected_by_arm),
    )


def finite_population_prevalence(world: Sequence[Window]) -> float:
    if not world:
        raise ValueError("world cannot be empty")
    return sum(float(row.true_event) for row in world) / len(world)


def sample_prevalence(world: Sequence[Window], indices: frozenset[int]) -> float:
    if not indices:
        raise ValueError("sample cannot be empty")
    return sum(float(world[index].true_event) for index in indices) / len(indices)


def binary_srs_variance(*, population_size: int, sample_size: int, prevalence: float) -> float:
    """Exact SRSWOR variance of a binary finite-population sample mean."""
    if not 0 < sample_size <= population_size:
        raise ValueError("sample_size must lie in [1, population_size]")
    if not 0.0 <= prevalence <= 1.0:
        raise ValueError("prevalence must lie in [0, 1]")
    if population_size == 1:
        return 0.0
    return (
        (population_size - sample_size)
        / (sample_size * (population_size - 1))
        * prevalence
        * (1.0 - prevalence)
    )


def wilson_interval(successes: int, sample_size: int, confidence: float = 0.95) -> Interval:
    """Ordinary iid-Bernoulli Wilson interval used as a naive comparator."""
    if not 0 <= successes <= sample_size or sample_size <= 0:
        raise ValueError("invalid binomial count")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie in (0,1)")
    alpha = 1.0 - confidence
    z = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = successes / sample_size
    denom = 1.0 + z * z / sample_size
    centre = (p + z * z / (2.0 * sample_size)) / denom
    half = (
        z
        * sqrt(p * (1.0 - p) / sample_size + z * z / (4.0 * sample_size * sample_size))
        / denom
    )
    return Interval(max(0.0, centre - half), min(1.0, centre + half))


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return lgamma(n + 1.0) - lgamma(k + 1.0) - lgamma(n - k + 1.0)


@lru_cache(maxsize=None)
def _hypergeom_cdf_table(population_size: int, successes: int, sample_size: int) -> tuple[float, ...]:
    """CDF table for X~Hypergeom(N,K,n), built stably around the mode."""
    n_total = population_size
    k_total = successes
    n_draw = sample_size
    if not 0 <= k_total <= n_total:
        raise ValueError("successes must lie in [0,N]")
    if not 0 <= n_draw <= n_total:
        raise ValueError("sample_size must lie in [0,N]")

    lo = max(0, n_draw - (n_total - k_total))
    hi = min(n_draw, k_total)
    probabilities = [0.0] * (n_draw + 1)
    if lo > hi:
        raise AssertionError("empty hypergeometric support")

    mode = floor((n_draw + 1) * (k_total + 1) / (n_total + 2))
    mode = max(lo, min(hi, mode))
    log_p_mode = (
        _log_choose(k_total, mode)
        + _log_choose(n_total - k_total, n_draw - mode)
        - _log_choose(n_total, n_draw)
    )
    probabilities[mode] = exp(log_p_mode)

    p = probabilities[mode]
    for x in range(mode, hi):
        denominator = (x + 1) * (n_total - k_total - n_draw + x + 1)
        p *= ((k_total - x) * (n_draw - x)) / denominator
        probabilities[x + 1] = p

    p = probabilities[mode]
    for x in range(mode, lo, -1):
        denominator = (k_total - x + 1) * (n_draw - x + 1)
        p *= (x * (n_total - k_total - n_draw + x)) / denominator
        probabilities[x - 1] = p

    total = sum(probabilities)
    if total <= 0.0:
        raise AssertionError("hypergeometric probabilities underflowed")
    running = 0.0
    cdf: list[float] = []
    for p in probabilities:
        running += p / total
        cdf.append(min(1.0, running))
    cdf[-1] = 1.0
    return tuple(cdf)


def _hypergeom_cdf(population_size: int, successes: int, sample_size: int, observed: int) -> float:
    if observed < 0:
        return 0.0
    if observed >= sample_size:
        return 1.0
    return _hypergeom_cdf_table(population_size, successes, sample_size)[observed]


def _hypergeom_tail_ge(
    population_size: int, successes: int, sample_size: int, observed: int
) -> float:
    if observed <= 0:
        return 1.0
    if observed > sample_size:
        return 0.0
    return max(
        0.0,
        1.0 - _hypergeom_cdf_table(population_size, successes, sample_size)[observed - 1],
    )


@lru_cache(maxsize=None)
def exact_hypergeometric_interval(
    population_size: int,
    sample_size: int,
    observed_successes: int,
    confidence: float = 0.95,
) -> Interval:
    """Exact equal-tailed confidence interval for finite-population prevalence.

    The interval inverts two one-sided hypergeometric tests for the unknown finite
    success count K and then divides the accepted K limits by N.
    """
    if population_size <= 0:
        raise ValueError("population_size must be positive")
    if not 0 < sample_size <= population_size:
        raise ValueError("sample_size must lie in [1,N]")
    if not 0 <= observed_successes <= sample_size:
        raise ValueError("observed_successes must lie in [0,n]")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie in (0,1)")

    alpha_tail = (1.0 - confidence) / 2.0
    feasible_low = observed_successes
    feasible_high = population_size - (sample_size - observed_successes)

    # P_K(X >= x) increases monotonically with K.
    left, right = feasible_low, feasible_high
    while left < right:
        mid = (left + right) // 2
        if _hypergeom_tail_ge(population_size, mid, sample_size, observed_successes) > alpha_tail:
            right = mid
        else:
            left = mid + 1
    lower_k = left

    # P_K(X <= x) decreases monotonically with K.
    left, right = feasible_low, feasible_high
    while left < right:
        mid = (left + right + 1) // 2
        if _hypergeom_cdf(population_size, mid, sample_size, observed_successes) > alpha_tail:
            left = mid
        else:
            right = mid - 1
    upper_k = left

    if lower_k > upper_k:
        raise AssertionError("empty exact hypergeometric confidence set")
    return Interval(lower_k / population_size, upper_k / population_size)
