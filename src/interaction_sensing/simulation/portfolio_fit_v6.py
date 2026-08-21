"""Fair development-only fitter for V6 observer portfolio weights.

Every candidate weight vector is evaluated on exactly the same sampled worlds.
This avoids giving different candidates different Monte Carlo draws and makes the
fit invariant to the order of the candidate grid.
"""
from __future__ import annotations

from statistics import mean
from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.observer_portfolio_v6 import (
    MinimaxFit,
    PortfolioResult,
    PortfolioWeights,
    generate_weight_grid,
    run_portfolio_replicates,
)


def fit_minimax_portfolio_shared_worlds(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    world_windows: int = 600,
    replicates: int = 8,
    seed: int = 20260821,
    grid: Sequence[PortfolioWeights] | None = None,
) -> MinimaxFit:
    pollipi = [row for row in pollipi_rows if str(row.get("split", "calibration")) == "calibration"]
    insepi = [row for row in insepi_rows if str(row.get("split", "calibration")) == "calibration"]
    candidates = list(grid) if grid is not None else generate_weight_grid()
    if not candidates:
        raise ValueError("portfolio weight grid is empty")

    best: MinimaxFit | None = None
    best_key: tuple[float, float, float, float, float, float, float] | None = None
    for weights in candidates:
        regime_results: list[PortfolioResult] = []
        for prevalence in prevalences:
            for budget in budgets:
                regime_results.append(
                    run_portfolio_replicates(
                        pollipi,
                        insepi,
                        weights=weights,
                        prevalence=prevalence,
                        budget_fraction=budget,
                        world_windows=world_windows,
                        replicates=replicates,
                        seed=seed,
                    )
                )
        worst_joint = min(min(row.true_event_recall, row.hidden_error_recall) for row in regime_results)
        worst_tv = max(row.disturbance_tv_distance for row in regime_results)
        mean_joint = mean(0.5 * (row.true_event_recall + row.hidden_error_recall) for row in regime_results)
        # Final deterministic tie-break uses the weight vector itself, not grid
        # position, so reversing the input grid cannot change the fitted result.
        key = (
            worst_joint,
            -worst_tv,
            mean_joint,
            weights.exploration,
            weights.pollipi,
            weights.insepi,
            weights.disagreement,
        )
        if best_key is None or key > best_key:
            best_key = key
            best = MinimaxFit(
                weights=weights,
                worst_joint_recall=worst_joint,
                worst_tv_distance=worst_tv,
                mean_joint_recall=mean_joint,
                regimes=len(regime_results),
            )
    assert best is not None
    return best
