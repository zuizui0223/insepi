"""Paired prevalence-robust development gate for V6 allocation candidates.

Pareto membership is intentionally not enough for method selection: a policy can
remain non-dominated by trading hidden-error recovery for event recovery in a way
that fails under prevalence shift. The V6 target is stronger and simpler:
relative to uniform exploration, one fixed policy should avoid material loss in
*either* recovery objective across every prevalence × budget regime while keeping
selection-induced disturbance distortion bounded.

V4 is development evidence. The numerical gate defined here becomes useful for
freezing a V6 candidate and pre-registering the future V7 one-shot validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random
from statistics import mean
from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.observer_portfolio_v6 import (
    PortfolioWeights,
    _score_selection,
    align_rows,
    sample_world,
    select_portfolio_indices,
)


@dataclass(frozen=True, slots=True)
class RobustnessRegime:
    prevalence: float
    budget_fraction: float
    candidate_event_recall: float
    uniform_event_recall: float
    candidate_hidden_error_recall: float
    uniform_hidden_error_recall: float
    event_ratio: float
    hidden_error_ratio: float
    joint_ratio: float
    candidate_tv_distance: float
    uniform_tv_distance: float
    candidate_captures_per_hidden_error: float
    uniform_captures_per_hidden_error: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RobustnessGateResult:
    weights: PortfolioWeights
    regimes: tuple[RobustnessRegime, ...]
    worst_joint_ratio: float
    mean_joint_ratio: float
    max_tv_distance: float
    max_excess_tv_over_uniform: float
    n_regimes_at_or_above_uniform: int
    passes_development_gate: bool
    ratio_floor: float
    tv_ceiling: float

    def to_dict(self) -> dict[str, object]:
        return {
            "weights": self.weights.to_dict(),
            "regimes": [row.to_dict() for row in self.regimes],
            "worst_joint_ratio": self.worst_joint_ratio,
            "mean_joint_ratio": self.mean_joint_ratio,
            "max_tv_distance": self.max_tv_distance,
            "max_excess_tv_over_uniform": self.max_excess_tv_over_uniform,
            "n_regimes_at_or_above_uniform": self.n_regimes_at_or_above_uniform,
            "passes_development_gate": self.passes_development_gate,
            "ratio_floor": self.ratio_floor,
            "tv_ceiling": self.tv_ceiling,
        }


def _uniform_indices(world_size: int, selected_n: int, seed: int) -> set[int]:
    rng = Random(seed)
    indices = list(range(world_size))
    rng.shuffle(indices)
    return set(indices[:selected_n])


def _safe_ratio(candidate: float, baseline: float) -> float:
    if baseline <= 1e-12:
        return 1.0 if candidate <= 1e-12 else float("inf")
    return candidate / baseline


def evaluate_candidate_against_uniform(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    weights: PortfolioWeights,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    world_windows: int = 2400,
    replicates: int = 100,
    seed: int = 20260821,
    ratio_floor: float = 1.00,
    tv_ceiling: float = 0.25,
) -> RobustnessGateResult:
    """Use paired worlds to compare one frozen candidate with uniform sampling."""

    pollipi = list(pollipi_rows)
    insepi = list(insepi_rows)
    aligned = align_rows(pollipi, insepi)
    regimes: list[RobustnessRegime] = []

    for prevalence in prevalences:
        for budget in budgets:
            candidate_results = []
            uniform_results = []
            for replicate in range(replicates):
                replicate_seed = seed + replicate * 1009
                world = sample_world(
                    aligned,
                    prevalence=prevalence,
                    world_windows=world_windows,
                    seed=replicate_seed,
                )
                selected_n = max(1, round(world_windows * budget))
                candidate_indices, _ = select_portfolio_indices(
                    world,
                    budget_fraction=budget,
                    weights=weights,
                    seed=replicate_seed + 7919,
                )
                uniform_indices = _uniform_indices(
                    world_windows,
                    selected_n,
                    replicate_seed + 104729,
                )
                candidate_results.append(
                    _score_selection(
                        world,
                        candidate_indices,
                        prevalence=prevalence,
                        budget_fraction=budget,
                        weights=weights,
                    )
                )
                uniform_results.append(
                    _score_selection(
                        world,
                        uniform_indices,
                        prevalence=prevalence,
                        budget_fraction=budget,
                        weights=PortfolioWeights(1.0, 0.0, 0.0, 0.0),
                    )
                )

            c_event = mean(row.true_event_recall for row in candidate_results)
            u_event = mean(row.true_event_recall for row in uniform_results)
            c_error = mean(row.hidden_error_recall for row in candidate_results)
            u_error = mean(row.hidden_error_recall for row in uniform_results)
            event_ratio = _safe_ratio(c_event, u_event)
            error_ratio = _safe_ratio(c_error, u_error)
            regimes.append(
                RobustnessRegime(
                    prevalence=prevalence,
                    budget_fraction=budget,
                    candidate_event_recall=c_event,
                    uniform_event_recall=u_event,
                    candidate_hidden_error_recall=c_error,
                    uniform_hidden_error_recall=u_error,
                    event_ratio=event_ratio,
                    hidden_error_ratio=error_ratio,
                    joint_ratio=min(event_ratio, error_ratio),
                    candidate_tv_distance=mean(row.disturbance_tv_distance for row in candidate_results),
                    uniform_tv_distance=mean(row.disturbance_tv_distance for row in uniform_results),
                    candidate_captures_per_hidden_error=mean(row.captures_per_hidden_error for row in candidate_results),
                    uniform_captures_per_hidden_error=mean(row.captures_per_hidden_error for row in uniform_results),
                )
            )

    worst_joint = min(row.joint_ratio for row in regimes)
    mean_joint = mean(row.joint_ratio for row in regimes)
    max_tv = max(row.candidate_tv_distance for row in regimes)
    max_excess_tv = max(row.candidate_tv_distance - row.uniform_tv_distance for row in regimes)
    n_at_or_above = sum(row.joint_ratio >= 1.0 for row in regimes)
    return RobustnessGateResult(
        weights=weights,
        regimes=tuple(regimes),
        worst_joint_ratio=worst_joint,
        mean_joint_ratio=mean_joint,
        max_tv_distance=max_tv,
        max_excess_tv_over_uniform=max_excess_tv,
        n_regimes_at_or_above_uniform=n_at_or_above,
        passes_development_gate=(worst_joint >= ratio_floor and max_tv <= tv_ceiling),
        ratio_floor=ratio_floor,
        tv_ceiling=tv_ceiling,
    )
