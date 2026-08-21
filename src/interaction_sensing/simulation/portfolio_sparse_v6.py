"""Sparse and budget-conditioned extensions of the V6 observer portfolio.

The first V6 screening showed that forcing every targeted arm to receive a
positive quota was not justified: removing the direct InsePi arm remained on the
Pareto frontier in all development regimes.  This module therefore lets
calibration choose zero weight for a targeted arm while keeping exploration
strictly positive.  It also allows weights to depend on the externally known
capture budget, but never on unknown event prevalence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.observer_portfolio_v6 import (
    MinimaxFit,
    PortfolioResult,
    PortfolioWeights,
    run_portfolio_replicates,
)
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds


def generate_sparse_weight_grid(
    *,
    step: float = 0.10,
    min_exploration: float = 0.30,
    max_targeted: float = 0.70,
) -> list[PortfolioWeights]:
    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-9:
        raise ValueError("step must divide 1 exactly")
    min_e = round(min_exploration / step)
    max_t = round(max_targeted / step)
    grid: list[PortfolioWeights] = []
    for e in range(min_e, units + 1):
        for p in range(0, max_t + 1):
            for i in range(0, max_t + 1):
                d = units - e - p - i
                if 0 <= d <= max_t:
                    grid.append(PortfolioWeights(e * step, p * step, i * step, d * step))
    return grid


def fit_sparse_minimax_portfolio(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    world_windows: int = 600,
    replicates: int = 8,
    seed: int = 20260821,
) -> MinimaxFit:
    return fit_minimax_portfolio_shared_worlds(
        pollipi_rows,
        insepi_rows,
        prevalences=prevalences,
        budgets=budgets,
        world_windows=world_windows,
        replicates=replicates,
        seed=seed,
        grid=generate_sparse_weight_grid(),
    )


@dataclass(frozen=True, slots=True)
class BudgetPortfolioEntry:
    budget_fraction: float
    fit: MinimaxFit

    def to_dict(self) -> dict[str, object]:
        return {"budget_fraction": self.budget_fraction, "fit": self.fit.to_dict()}


@dataclass(frozen=True, slots=True)
class BudgetPortfolioSchedule:
    entries: tuple[BudgetPortfolioEntry, ...]

    def weights_for(self, budget_fraction: float) -> PortfolioWeights:
        matches = [entry.fit.weights for entry in self.entries if abs(entry.budget_fraction - budget_fraction) <= 1e-9]
        if len(matches) != 1:
            raise ValueError(f"no unique frozen portfolio weights for budget {budget_fraction}")
        return matches[0]

    def to_dict(self) -> dict[str, object]:
        return {"entries": [entry.to_dict() for entry in self.entries]}


def fit_budget_conditioned_schedule(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    world_windows: int = 600,
    replicates: int = 8,
    seed: int = 20260821,
) -> BudgetPortfolioSchedule:
    """Fit one prevalence-robust portfolio per known sensing budget."""

    pollipi = list(pollipi_rows)
    insepi = list(insepi_rows)
    entries = []
    for budget in budgets:
        fit = fit_minimax_portfolio_shared_worlds(
            pollipi,
            insepi,
            prevalences=prevalences,
            budgets=(budget,),
            world_windows=world_windows,
            replicates=replicates,
            seed=seed,
            grid=generate_sparse_weight_grid(),
        )
        entries.append(BudgetPortfolioEntry(budget_fraction=budget, fit=fit))
    return BudgetPortfolioSchedule(tuple(entries))


def run_schedule_replicates(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    schedule: BudgetPortfolioSchedule,
    prevalence: float,
    budget_fraction: float,
    world_windows: int = 2400,
    replicates: int = 100,
    seed: int = 20260821,
) -> PortfolioResult:
    return run_portfolio_replicates(
        pollipi_rows,
        insepi_rows,
        weights=schedule.weights_for(budget_fraction),
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        world_windows=world_windows,
        replicates=replicates,
        seed=seed,
    )
