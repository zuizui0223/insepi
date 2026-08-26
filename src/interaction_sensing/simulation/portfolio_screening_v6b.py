"""Second V6 development screening after the forced-four-arm result.

The first V6 screen kept every targeted arm positive and reached the V4 Pareto
frontier in 8/9 regimes, but the no-InsePi ablation was non-dominated in all 9.
This screen asks a narrower development question without using future V7 data:

1. should calibration be allowed to set a targeted arm weight to zero?
2. can weights depend on the externally known sensing budget while remaining
   prevalence-agnostic at runtime?

V4 test is already-inspected development evidence. Results from this module are
for method development only and cannot serve as locked validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.observer_portfolio_v6 import (
    MinimaxFit,
    PortfolioWeights,
    run_portfolio_replicates,
)
from interaction_sensing.simulation.portfolio_development_v6 import (
    LEGACY_POLICIES,
    DevelopmentResult,
    _as_development,
    _legacy_replicates,
    drop_arm,
    mark_pareto,
    read_pollipi_v4_tsv,
)
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds
from interaction_sensing.simulation.portfolio_sparse_v6 import (
    BudgetPortfolioSchedule,
    fit_budget_conditioned_schedule,
    fit_sparse_minimax_portfolio,
    run_schedule_replicates,
)


@dataclass(frozen=True, slots=True)
class V6BScreeningReport:
    pollipi_source_commit: str
    world_fingerprint: str
    forced_fit: MinimaxFit
    sparse_fit: MinimaxFit
    budget_schedule: BudgetPortfolioSchedule
    results: tuple[DevelopmentResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pollipi_source_commit": self.pollipi_source_commit,
            "world_fingerprint": self.world_fingerprint,
            "forced_fit": self.forced_fit.to_dict(),
            "sparse_fit": self.sparse_fit.to_dict(),
            "budget_schedule": self.budget_schedule.to_dict(),
            "results": [row.to_dict() for row in self.results],
        }


def _unique_ablations(weights: PortfolioWeights) -> dict[str, PortfolioWeights]:
    """Return distinct sparse-arm removals; duplicate vectors are omitted."""

    rows: dict[str, PortfolioWeights] = {"v6_sparse": weights}
    for arm in ("pollipi", "insepi", "disagreement"):
        if getattr(weights, arm) <= 0.0:
            continue
        candidate = drop_arm(weights, arm)
        if candidate not in rows.values():
            rows[f"v6_sparse_no_{arm}"] = candidate
    return rows


def run_v6b_screening(
    pollipi_trace_path: str | Path,
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    fit_world_windows: int = 600,
    fit_replicates: int = 6,
    eval_world_windows: int = 2400,
    eval_replicates: int = 50,
    seed: int = 20260821,
) -> V6BScreeningReport:
    provenance, pollipi_rows = read_pollipi_v4_tsv(pollipi_trace_path)
    insepi_rows = [row.to_dict() for row in run_factorial_v4()]

    forced_fit = fit_minimax_portfolio_shared_worlds(
        pollipi_rows,
        insepi_rows,
        prevalences=prevalences,
        budgets=budgets,
        world_windows=fit_world_windows,
        replicates=fit_replicates,
        seed=seed,
    )
    sparse_fit = fit_sparse_minimax_portfolio(
        pollipi_rows,
        insepi_rows,
        prevalences=prevalences,
        budgets=budgets,
        world_windows=fit_world_windows,
        replicates=fit_replicates,
        seed=seed,
    )
    schedule = fit_budget_conditioned_schedule(
        pollipi_rows,
        insepi_rows,
        prevalences=prevalences,
        budgets=budgets,
        world_windows=fit_world_windows,
        replicates=fit_replicates,
        seed=seed,
    )

    test_pollipi = [row for row in pollipi_rows if row["split"] == "test"]
    test_insepi = [row for row in insepi_rows if row["split"] == "test"]
    methods: list[DevelopmentResult] = []
    sparse_ablations = _unique_ablations(sparse_fit.weights)

    for prevalence in prevalences:
        for budget in budgets:
            forced = run_portfolio_replicates(
                test_pollipi,
                test_insepi,
                weights=forced_fit.weights,
                prevalence=prevalence,
                budget_fraction=budget,
                world_windows=eval_world_windows,
                replicates=eval_replicates,
                seed=seed,
            )
            methods.append(_as_development("v6_forced_four_arm", forced))

            for method, weights in sparse_ablations.items():
                result = run_portfolio_replicates(
                    test_pollipi,
                    test_insepi,
                    weights=weights,
                    prevalence=prevalence,
                    budget_fraction=budget,
                    world_windows=eval_world_windows,
                    replicates=eval_replicates,
                    seed=seed,
                )
                methods.append(_as_development(method, result))

            scheduled = run_schedule_replicates(
                test_pollipi,
                test_insepi,
                schedule=schedule,
                prevalence=prevalence,
                budget_fraction=budget,
                world_windows=eval_world_windows,
                replicates=eval_replicates,
                seed=seed,
            )
            methods.append(_as_development("v6_budget_conditioned", scheduled))

            for policy in LEGACY_POLICIES:
                result = _legacy_replicates(
                    test_pollipi,
                    test_insepi,
                    policy=policy,
                    prevalence=prevalence,
                    budget_fraction=budget,
                    world_windows=eval_world_windows,
                    replicates=eval_replicates,
                    seed=seed,
                )
                methods.append(_as_development(policy, result))

    return V6BScreeningReport(
        pollipi_source_commit=provenance["source_commit"],
        world_fingerprint=provenance["world_fingerprint"],
        forced_fit=forced_fit,
        sparse_fit=sparse_fit,
        budget_schedule=schedule,
        results=tuple(mark_pareto(methods)),
    )
