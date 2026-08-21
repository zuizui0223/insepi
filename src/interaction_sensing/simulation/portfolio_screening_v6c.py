"""V6C development screen for the minimal exploration+one-arm policy class."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.observer_portfolio_v6 import MinimaxFit, run_portfolio_replicates
from interaction_sensing.simulation.portfolio_development_v6 import (
    LEGACY_POLICIES,
    DevelopmentResult,
    _as_development,
    _legacy_replicates,
    mark_pareto,
    read_pollipi_v4_tsv,
)
from interaction_sensing.simulation.portfolio_single_arm_v6 import (
    active_exploitation_arm,
    fit_single_arm_minimax,
)


@dataclass(frozen=True, slots=True)
class V6CScreeningReport:
    pollipi_source_commit: str
    world_fingerprint: str
    fit: MinimaxFit
    exploitation_arm: str
    results: tuple[DevelopmentResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pollipi_source_commit": self.pollipi_source_commit,
            "world_fingerprint": self.world_fingerprint,
            "fit": self.fit.to_dict(),
            "exploitation_arm": self.exploitation_arm,
            "results": [row.to_dict() for row in self.results],
        }


def run_v6c_screening(
    pollipi_trace_path: str | Path,
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    fit_world_windows: int = 600,
    fit_replicates: int = 6,
    eval_world_windows: int = 2400,
    eval_replicates: int = 50,
    seed: int = 20260821,
) -> V6CScreeningReport:
    provenance, pollipi_rows = read_pollipi_v4_tsv(pollipi_trace_path)
    insepi_rows = [row.to_dict() for row in run_factorial_v4()]
    fit = fit_single_arm_minimax(
        pollipi_rows,
        insepi_rows,
        prevalences=prevalences,
        budgets=budgets,
        world_windows=fit_world_windows,
        replicates=fit_replicates,
        seed=seed,
    )
    arm = active_exploitation_arm(fit.weights)

    test_pollipi = [row for row in pollipi_rows if row["split"] == "test"]
    test_insepi = [row for row in insepi_rows if row["split"] == "test"]
    results: list[DevelopmentResult] = []
    for prevalence in prevalences:
        for budget in budgets:
            fitted = run_portfolio_replicates(
                test_pollipi,
                test_insepi,
                weights=fit.weights,
                prevalence=prevalence,
                budget_fraction=budget,
                world_windows=eval_world_windows,
                replicates=eval_replicates,
                seed=seed,
            )
            results.append(_as_development("v6_single_arm", fitted))
            for policy in LEGACY_POLICIES:
                baseline = _legacy_replicates(
                    test_pollipi,
                    test_insepi,
                    policy=policy,
                    prevalence=prevalence,
                    budget_fraction=budget,
                    world_windows=eval_world_windows,
                    replicates=eval_replicates,
                    seed=seed,
                )
                results.append(_as_development(policy, baseline))

    return V6CScreeningReport(
        pollipi_source_commit=provenance["source_commit"],
        world_fingerprint=provenance["world_fingerprint"],
        fit=fit,
        exploitation_arm=arm,
        results=tuple(mark_pareto(results)),
    )
