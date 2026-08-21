"""Cross-repository V4 competition from an emitted PolliPi trace artifact.

This module never imports PolliPi. It verifies the PolliPi artifact provenance,
recomputes InsePi decisions locally from the shared V4 pixels, and then runs the
pre-registered equal-budget policies on matching condition IDs.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

from interaction_sensing.simulation.budget_competition import (
    CORE_POLICIES,
    SINGLE_VIEW_ABLATIONS,
    BudgetResult,
    run_budget_competition,
)
from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.factorial_world_v4 import suite_fingerprint

SCHEMA = "pollipi-insepi-factorial-v4"
REPORT_SCHEMA = "pollipi-insepi-factorial-cross-v4-report"
DEFAULT_BUDGETS = (0.10, 0.25, 0.50)
CROSS_POLICIES = CORE_POLICIES + SINGLE_VIEW_ABLATIONS
# The preregistered frontier answers the central allocation trade-off. Error-type
# yields and disturbance TV distance remain reported guardrails; treating every
# diagnostic as a Pareto axis would make almost every policy trivially non-dominated.
PARETO_MAXIMIZE = (
    "true_event_recall",
    "hidden_error_recall",
)
PARETO_MINIMIZE = ("captures_per_hidden_error",)


@dataclass(frozen=True, slots=True)
class BudgetGridPoint:
    budget_fraction: float
    results: tuple[BudgetResult, ...]
    pareto_policies: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "budget_fraction": self.budget_fraction,
            "pareto_policies": list(self.pareto_policies),
            "results": [row.to_dict() for row in self.results],
        }


@dataclass(frozen=True, slots=True)
class FactorialCrossV4Report:
    pollipi_provenance: Mapping[str, object]
    insepi_source_commit: str
    evaluation_split: str
    evaluated_conditions: int
    world_windows: int
    replicates: int
    seed: int
    budgets: tuple[BudgetGridPoint, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": REPORT_SCHEMA,
            "world_fingerprint": suite_fingerprint(),
            "pollipi_provenance": dict(self.pollipi_provenance),
            "insepi_source_commit": self.insepi_source_commit,
            "evaluation_split": self.evaluation_split,
            "evaluated_conditions": self.evaluated_conditions,
            "world_windows": self.world_windows,
            "replicates": self.replicates,
            "seed": self.seed,
            "budgets": [point.to_dict() for point in self.budgets],
        }


def read_pollipi_factorial_trace(path: str | Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not all(isinstance(row, dict) for row in records):
        raise ValueError("PolliPi V4 trace records must be JSON objects")
    unknown = [row for row in records if row.get("record_type") not in {"provenance", "result"}]
    if unknown:
        raise ValueError("PolliPi V4 trace contains an unknown record type")
    provenance = [row for row in records if row.get("record_type") == "provenance"]
    results = [row for row in records if row.get("record_type") == "result"]
    if len(provenance) != 1:
        raise ValueError("PolliPi V4 trace needs exactly one provenance record")
    prov = provenance[0]
    if prov.get("schema") != SCHEMA:
        raise ValueError("unexpected PolliPi V4 schema")
    if prov.get("world_fingerprint") != suite_fingerprint():
        raise ValueError("PolliPi/InsePi V4 world fingerprint mismatch")
    if not prov.get("source_commit"):
        raise ValueError("PolliPi V4 trace is missing source_commit provenance")
    if not results:
        raise ValueError("PolliPi V4 trace has no result records")
    return prov, results


def _index_unique(rows: Sequence[Mapping[str, object]], *, observer: str) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        condition_id = str(row.get("condition_id", ""))
        if not condition_id:
            raise ValueError(f"{observer} V4 row is missing condition_id")
        if condition_id in indexed:
            raise ValueError(f"duplicate {observer} V4 condition_id: {condition_id}")
        indexed[condition_id] = row
    return indexed


def _validate_and_select_rows(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
    *,
    evaluation_split: str,
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    if evaluation_split not in {"calibration", "test"}:
        raise ValueError("evaluation_split must be calibration or test")
    pollipi = _index_unique(pollipi_rows, observer="PolliPi")
    insepi = _index_unique(insepi_rows, observer="InsePi")
    if set(pollipi) != set(insepi):
        raise ValueError("PolliPi/InsePi V4 condition IDs differ")
    for condition_id in sorted(pollipi):
        p_row, i_row = pollipi[condition_id], insepi[condition_id]
        if p_row.get("schema") != SCHEMA:
            raise ValueError(f"unexpected PolliPi V4 result schema: {condition_id}")
        for key in ("split", "true_visit", "disturbance_family"):
            if p_row.get(key) != i_row.get(key):
                raise ValueError(f"PolliPi/InsePi V4 {key} mismatch: {condition_id}")
    selected_ids = [
        condition_id
        for condition_id in sorted(pollipi)
        if pollipi[condition_id].get("split") == evaluation_split
    ]
    if not selected_ids:
        raise ValueError(f"V4 trace has no {evaluation_split} conditions")
    return (
        [pollipi[condition_id] for condition_id in selected_ids],
        [insepi[condition_id] for condition_id in selected_ids],
    )


def dominates(
    candidate: BudgetResult,
    other: BudgetResult,
    *,
    maximize: Sequence[str] = PARETO_MAXIMIZE,
    minimize: Sequence[str] = PARETO_MINIMIZE,
    tolerance: float = 1e-12,
) -> bool:
    candidate_values = [float(getattr(candidate, name)) for name in maximize]
    other_values = [float(getattr(other, name)) for name in maximize]
    candidate_costs = [float(getattr(candidate, name)) for name in minimize]
    other_costs = [float(getattr(other, name)) for name in minimize]
    weakly_better = all(c >= o - tolerance for c, o in zip(candidate_values, other_values)) and all(
        c <= o + tolerance for c, o in zip(candidate_costs, other_costs)
    )
    strictly_better = any(c > o + tolerance for c, o in zip(candidate_values, other_values)) or any(
        c < o - tolerance for c, o in zip(candidate_costs, other_costs)
    )
    return weakly_better and strictly_better


def pareto_frontier(results: Sequence[BudgetResult]) -> tuple[str, ...]:
    return tuple(
        row.policy
        for row in results
        if not any(dominates(candidate, row) for candidate in results if candidate is not row)
    )


def _load_evaluation_rows(
    pollipi_trace_path: str | Path,
    *,
    evaluation_split: str,
) -> tuple[dict[str, object], list[Mapping[str, object]], list[Mapping[str, object]]]:
    provenance, pollipi_rows = read_pollipi_factorial_trace(pollipi_trace_path)
    insepi_rows = [row.to_dict() for row in run_factorial_v4()]
    selected_pollipi, selected_insepi = _validate_and_select_rows(
        pollipi_rows,
        insepi_rows,
        evaluation_split=evaluation_split,
    )
    return provenance, selected_pollipi, selected_insepi


def run_factorial_cross_v4(
    pollipi_trace_path: str | Path,
    *,
    budget_fraction: float = 0.25,
    world_windows: int = 4800,
    replicates: int = 200,
    seed: int = 20260821,
    evaluation_split: str = "test",
) -> tuple[dict[str, object], list[BudgetResult]]:
    provenance, pollipi_rows, insepi_rows = _load_evaluation_rows(
        pollipi_trace_path,
        evaluation_split=evaluation_split,
    )
    results = run_budget_competition(
        pollipi_rows,
        insepi_rows,
        budget_fraction=budget_fraction,
        world_windows=world_windows,
        replicates=replicates,
        seed=seed,
    )
    return provenance, results


def run_factorial_cross_v4_grid(
    pollipi_trace_path: str | Path,
    *,
    insepi_source_commit: str,
    budgets: Sequence[float] = DEFAULT_BUDGETS,
    policies: Sequence[str] = CROSS_POLICIES,
    evaluation_split: str = "test",
    world_windows: int = 4800,
    replicates: int = 200,
    seed: int = 20260821,
) -> FactorialCrossV4Report:
    if not insepi_source_commit:
        raise ValueError("insepi_source_commit provenance is required")
    provenance, pollipi_rows, insepi_rows = _load_evaluation_rows(
        pollipi_trace_path,
        evaluation_split=evaluation_split,
    )
    points: list[BudgetGridPoint] = []
    for budget in budgets:
        results = tuple(run_budget_competition(
            pollipi_rows,
            insepi_rows,
            policies=policies,
            budget_fraction=budget,
            world_windows=world_windows,
            replicates=replicates,
            seed=seed,
        ))
        points.append(BudgetGridPoint(
            budget_fraction=budget,
            results=results,
            pareto_policies=pareto_frontier(results),
        ))
    return FactorialCrossV4Report(
        pollipi_provenance=provenance,
        insepi_source_commit=insepi_source_commit,
        evaluation_split=evaluation_split,
        evaluated_conditions=len(pollipi_rows),
        world_windows=world_windows,
        replicates=replicates,
        seed=seed,
        budgets=tuple(points),
    )


def write_factorial_cross_v4_report(path: str | Path, report: FactorialCrossV4Report) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output
