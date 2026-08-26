"""Active V6 development screening using fair shared-world portfolio fitting."""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.observer_portfolio_v6 import run_portfolio_replicates
from interaction_sensing.simulation.portfolio_development_v6 import (
    LEGACY_POLICIES,
    DevelopmentReport,
    DevelopmentResult,
    _as_development,
    _legacy_replicates,
    drop_arm,
    mark_pareto,
    read_pollipi_v4_tsv,
)
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds


def run_v6_screening(
    pollipi_trace_path: str | Path,
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    fit_world_windows: int = 600,
    fit_replicates: int = 6,
    eval_world_windows: int = 2400,
    eval_replicates: int = 50,
    seed: int = 20260821,
) -> DevelopmentReport:
    provenance, pollipi_rows = read_pollipi_v4_tsv(pollipi_trace_path)
    insepi_rows = [row.to_dict() for row in run_factorial_v4()]

    fit = fit_minimax_portfolio_shared_worlds(
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
    ablations = {
        "observer_portfolio_v6": fit.weights,
        "v6_no_pollipi": drop_arm(fit.weights, "pollipi"),
        "v6_no_insepi": drop_arm(fit.weights, "insepi"),
        "v6_no_disagreement": drop_arm(fit.weights, "disagreement"),
    }

    for prevalence in prevalences:
        for budget in budgets:
            for method, weights in ablations.items():
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

    return DevelopmentReport(
        pollipi_source_commit=provenance["source_commit"],
        world_fingerprint=provenance["world_fingerprint"],
        fit=fit,
        results=tuple(mark_pareto(methods)),
    )
