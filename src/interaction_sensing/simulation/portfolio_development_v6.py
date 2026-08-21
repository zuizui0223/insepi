"""Development benchmark for V6 observer-portfolio allocation.

V4 is development evidence, not a claim-bearing locked validation.  This module
fits V6 on V4 calibration rows only and evaluates on the already-inspected V4
test split across prevalence and budget regimes.  It also compares the portfolio
against legacy scalar policies and arm-removal ablations using the same sampled
worlds and metrics.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from random import Random
from statistics import mean
from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.budget_competition import allocation_score
from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.factorial_world_v4 import suite_fingerprint
from interaction_sensing.simulation.observer_portfolio_v6 import (
    MinimaxFit,
    PortfolioResult,
    PortfolioWeights,
    _score_selection,
    align_rows,
    fit_minimax_portfolio,
    run_portfolio_replicates,
    sample_world,
    select_portfolio_indices,
)


LEGACY_POLICIES = (
    "uniform",
    "pollipi_candidate",
    "insepi_audit",
    "union",
    "intersection",
    "disagreement",
)


@dataclass(frozen=True, slots=True)
class DevelopmentResult:
    method: str
    prevalence: float
    budget_fraction: float
    true_event_recall: float
    hidden_error_recall: float
    captures_per_hidden_error: float
    disturbance_tv_distance: float
    false_event_audit_yield: float
    missed_event_audit_yield: float
    attribution_audit_yield: float
    pareto: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DevelopmentReport:
    pollipi_source_commit: str
    world_fingerprint: str
    fit: MinimaxFit
    results: tuple[DevelopmentResult, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "pollipi_source_commit": self.pollipi_source_commit,
            "world_fingerprint": self.world_fingerprint,
            "fit": self.fit.to_dict(),
            "results": [row.to_dict() for row in self.results],
        }


def read_pollipi_v4_tsv(path: str | Path) -> tuple[dict[str, str], list[dict[str, object]]]:
    """Read the compact immutable PolliPi V4 emitted-trace snapshot."""

    lines = Path(path).read_text(encoding="utf-8").splitlines()
    provenance: dict[str, str] = {}
    data_lines: list[str] = []
    for line in lines:
        if line.startswith("#"):
            key, value = line[1:].split("=", 1)
            provenance[key] = value
        elif line.strip():
            data_lines.append(line)
    if provenance.get("world_fingerprint") != suite_fingerprint():
        raise ValueError("PolliPi V4 compact trace world fingerprint mismatch")
    if not provenance.get("source_commit"):
        raise ValueError("PolliPi V4 compact trace is missing source commit")
    if not data_lines:
        raise ValueError("PolliPi V4 compact trace has no rows")

    reader = csv.DictReader(data_lines, delimiter="\t")
    rows: list[dict[str, object]] = []
    for row in reader:
        rows.append(
            {
                "condition_id": row["condition_id"],
                "split": row["split"],
                "true_visit": row["true_visit"] == "1",
                "disturbance_family": row["disturbance_family"],
                "pollipi_state": row["pollipi_state"],
            }
        )
    if len(rows) != 120:
        raise ValueError(f"expected 120 PolliPi V4 rows, found {len(rows)}")
    return provenance, rows


def _legacy_select(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    *,
    policy: str,
    budget_fraction: float,
    seed: int,
) -> set[int]:
    selected_n = max(1, round(len(world) * budget_fraction))
    rng = Random(seed)
    if policy == "uniform":
        indices = list(range(len(world)))
        rng.shuffle(indices)
        return set(indices[:selected_n])
    scored = [
        (allocation_score(policy, pollipi, insepi), rng.random(), index)
        for index, (pollipi, insepi) in enumerate(world)
    ]
    scored.sort(reverse=True)
    return {index for _, _, index in scored[:selected_n]}


def _legacy_once(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
    *,
    policy: str,
    prevalence: float,
    budget_fraction: float,
    world_windows: int,
    seed: int,
) -> PortfolioResult:
    aligned = align_rows(pollipi_rows, insepi_rows)
    world = sample_world(aligned, prevalence=prevalence, world_windows=world_windows, seed=seed)
    selected = _legacy_select(
        world,
        policy=policy,
        budget_fraction=budget_fraction,
        seed=seed + 7919,
    )
    # Weights are bookkeeping only for the shared evaluator; selection above is
    # still exactly the requested legacy policy.
    result = _score_selection(
        world,
        selected,
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        weights=PortfolioWeights(1.0, 0.0, 0.0, 0.0),
    )
    return PortfolioResult(
        policy=policy,
        prevalence=result.prevalence,
        budget_fraction=result.budget_fraction,
        world_windows=result.world_windows,
        selected=result.selected,
        exploration_share=result.exploration_share,
        pollipi_share=result.pollipi_share,
        insepi_share=result.insepi_share,
        disagreement_share=result.disagreement_share,
        true_event_recall=result.true_event_recall,
        hidden_error_recall=result.hidden_error_recall,
        false_event_audit_yield=result.false_event_audit_yield,
        missed_event_audit_yield=result.missed_event_audit_yield,
        attribution_audit_yield=result.attribution_audit_yield,
        captures_per_hidden_error=result.captures_per_hidden_error,
        disturbance_tv_distance=result.disturbance_tv_distance,
    )


def _legacy_replicates(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
    *,
    policy: str,
    prevalence: float,
    budget_fraction: float,
    world_windows: int,
    replicates: int,
    seed: int,
) -> PortfolioResult:
    rows = [
        _legacy_once(
            pollipi_rows,
            insepi_rows,
            policy=policy,
            prevalence=prevalence,
            budget_fraction=budget_fraction,
            world_windows=world_windows,
            seed=seed + replicate * 1009,
        )
        for replicate in range(replicates)
    ]
    first = rows[0]
    return PortfolioResult(
        policy=policy,
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        world_windows=world_windows,
        selected=first.selected,
        exploration_share=0.0,
        pollipi_share=0.0,
        insepi_share=0.0,
        disagreement_share=0.0,
        true_event_recall=mean(row.true_event_recall for row in rows),
        hidden_error_recall=mean(row.hidden_error_recall for row in rows),
        false_event_audit_yield=mean(row.false_event_audit_yield for row in rows),
        missed_event_audit_yield=mean(row.missed_event_audit_yield for row in rows),
        attribution_audit_yield=mean(row.attribution_audit_yield for row in rows),
        captures_per_hidden_error=mean(row.captures_per_hidden_error for row in rows),
        disturbance_tv_distance=mean(row.disturbance_tv_distance for row in rows),
    )


def drop_arm(weights: PortfolioWeights, arm: str) -> PortfolioWeights:
    """Ablate one targeted arm and conservatively return its quota to exploration."""

    if arm not in {"pollipi", "insepi", "disagreement"}:
        raise ValueError("only targeted arms can be dropped")
    removed = getattr(weights, arm)
    return PortfolioWeights(
        exploration=weights.exploration + removed,
        pollipi=0.0 if arm == "pollipi" else weights.pollipi,
        insepi=0.0 if arm == "insepi" else weights.insepi,
        disagreement=0.0 if arm == "disagreement" else weights.disagreement,
    )


def _as_development(method: str, result: PortfolioResult) -> DevelopmentResult:
    return DevelopmentResult(
        method=method,
        prevalence=result.prevalence,
        budget_fraction=result.budget_fraction,
        true_event_recall=result.true_event_recall,
        hidden_error_recall=result.hidden_error_recall,
        captures_per_hidden_error=result.captures_per_hidden_error,
        disturbance_tv_distance=result.disturbance_tv_distance,
        false_event_audit_yield=result.false_event_audit_yield,
        missed_event_audit_yield=result.missed_event_audit_yield,
        attribution_audit_yield=result.attribution_audit_yield,
    )


def _dominates(left: DevelopmentResult, right: DevelopmentResult) -> bool:
    at_least = (
        left.true_event_recall >= right.true_event_recall
        and left.hidden_error_recall >= right.hidden_error_recall
        and left.captures_per_hidden_error <= right.captures_per_hidden_error
        and left.disturbance_tv_distance <= right.disturbance_tv_distance
    )
    strict = (
        left.true_event_recall > right.true_event_recall
        or left.hidden_error_recall > right.hidden_error_recall
        or left.captures_per_hidden_error < right.captures_per_hidden_error
        or left.disturbance_tv_distance < right.disturbance_tv_distance
    )
    return at_least and strict


def mark_pareto(rows: Iterable[DevelopmentResult]) -> list[DevelopmentResult]:
    """Mark non-dominated methods within each prevalence × budget regime."""

    source = list(rows)
    output: list[DevelopmentResult] = []
    for row in source:
        peers = [
            other
            for other in source
            if other.prevalence == row.prevalence and other.budget_fraction == row.budget_fraction
        ]
        pareto = not any(_dominates(other, row) for other in peers if other is not row)
        payload = row.to_dict()
        payload["pareto"] = pareto
        output.append(DevelopmentResult(**payload))
    return output


def run_v6_development(
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

    fit = fit_minimax_portfolio(
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
