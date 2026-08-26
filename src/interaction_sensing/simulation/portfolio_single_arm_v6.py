"""Minimal V6 policy class: guaranteed exploration plus one exploitation arm.

V6B showed that a four-arm portfolio is not automatically preferable and that a
high-exploration PolliPi ablation remained non-dominated across all inspected V4
regimes. Before introducing online adaptation, this module asks whether the
simpler policy class is sufficient.

Calibration jointly chooses the exploitation *identity* (PolliPi, InsePi, or
structured disagreement) and its quota. Runtime never conditions on event
prevalence.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.observer_portfolio_v6 import (
    MinimaxFit,
    PortfolioWeights,
)
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds


EXPLOITATION_ARMS = ("pollipi", "insepi", "disagreement")


def generate_single_arm_grid(
    *,
    step: float = 0.05,
    max_exploitation: float = 0.50,
) -> list[PortfolioWeights]:
    """Generate uniform+one-arm portfolios, including the pure-uniform baseline."""

    units = round(1.0 / step)
    max_units = round(max_exploitation / step)
    if abs(units * step - 1.0) > 1e-9:
        raise ValueError("step must divide 1 exactly")
    grid = [PortfolioWeights(1.0, 0.0, 0.0, 0.0)]
    for arm in EXPLOITATION_ARMS:
        for exploitation_units in range(1, max_units + 1):
            q = exploitation_units * step
            weights = {
                "exploration": 1.0 - q,
                "pollipi": 0.0,
                "insepi": 0.0,
                "disagreement": 0.0,
            }
            weights[arm] = q
            grid.append(PortfolioWeights(**weights))
    return grid


def active_exploitation_arm(weights: PortfolioWeights) -> str:
    active = [
        arm
        for arm in EXPLOITATION_ARMS
        if getattr(weights, arm) > 1e-12
    ]
    if not active:
        return "uniform"
    if len(active) != 1:
        raise ValueError("weights are not a single-exploitation-arm portfolio")
    return active[0]


def fit_single_arm_minimax(
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
        grid=generate_single_arm_grid(),
    )
