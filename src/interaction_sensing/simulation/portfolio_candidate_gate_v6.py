"""Select the V6 development candidate by prevalence-robust regret, not Pareto count."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.observer_portfolio_v6 import MinimaxFit, PortfolioWeights
from interaction_sensing.simulation.portfolio_development_v6 import read_pollipi_v4_tsv
from interaction_sensing.simulation.portfolio_fit_v6 import fit_minimax_portfolio_shared_worlds
from interaction_sensing.simulation.portfolio_single_arm_v6 import fit_single_arm_minimax
from interaction_sensing.simulation.portfolio_sparse_v6 import fit_sparse_minimax_portfolio
from interaction_sensing.simulation.robustness_gate_v6 import (
    RobustnessGateResult,
    evaluate_candidate_against_uniform,
)


@dataclass(frozen=True, slots=True)
class CandidateGateReport:
    pollipi_source_commit: str
    world_fingerprint: str
    forced_fit: MinimaxFit
    sparse_fit: MinimaxFit
    single_arm_fit: MinimaxFit
    candidates: tuple[tuple[str, RobustnessGateResult], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pollipi_source_commit": self.pollipi_source_commit,
            "world_fingerprint": self.world_fingerprint,
            "forced_fit": self.forced_fit.to_dict(),
            "sparse_fit": self.sparse_fit.to_dict(),
            "single_arm_fit": self.single_arm_fit.to_dict(),
            "candidates": [
                {"name": name, "gate": result.to_dict()}
                for name, result in self.candidates
            ],
        }


def _candidate_sort_key(item: tuple[str, RobustnessGateResult]):
    name, result = item
    targeted_arms = sum(
        getattr(result.weights, arm) > 1e-12
        for arm in ("pollipi", "insepi", "disagreement")
    )
    # First prefer candidates that pass the hard gate, then maximise worst-case
    # joint ratio and mean ratio, then minimise TV and structural complexity.
    return (
        int(result.passes_development_gate),
        result.worst_joint_ratio,
        result.mean_joint_ratio,
        -result.max_tv_distance,
        -targeted_arms,
        result.weights.exploration,
        name,
    )


def run_candidate_gate(
    pollipi_trace_path: str | Path,
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    fit_world_windows: int = 600,
    fit_replicates: int = 6,
    gate_world_windows: int = 2400,
    gate_replicates: int = 100,
    seed: int = 20260821,
    ratio_floor: float = 1.00,
    tv_ceiling: float = 0.25,
) -> CandidateGateReport:
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
    single_fit = fit_single_arm_minimax(
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
    candidate_weights = {
        "forced_four_arm": forced_fit.weights,
        "sparse_calibration": sparse_fit.weights,
        "single_arm_calibration": single_fit.weights,
        # This conservative two-arm candidate was exposed by V4 development
        # ablation and is therefore legitimate development material, not a V7
        # result. It must be frozen before any future locked validation.
        "conservative_90_uniform_10_pollipi": PortfolioWeights(0.90, 0.10, 0.0, 0.0),
    }
    candidates = []
    for name, weights in candidate_weights.items():
        gate = evaluate_candidate_against_uniform(
            test_pollipi,
            test_insepi,
            weights=weights,
            prevalences=prevalences,
            budgets=budgets,
            world_windows=gate_world_windows,
            replicates=gate_replicates,
            seed=seed,
            ratio_floor=ratio_floor,
            tv_ceiling=tv_ceiling,
        )
        candidates.append((name, gate))

    candidates.sort(key=_candidate_sort_key, reverse=True)
    return CandidateGateReport(
        pollipi_source_commit=provenance["source_commit"],
        world_fingerprint=provenance["world_fingerprint"],
        forced_fit=forced_fit,
        sparse_fit=sparse_fit,
        single_arm_fit=single_fit,
        candidates=tuple(candidates),
    )
