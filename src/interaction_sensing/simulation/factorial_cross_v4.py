"""Cross-repository V4 competition from an emitted PolliPi trace artifact.

This module never imports PolliPi. It verifies the PolliPi artifact provenance,
recomputes InsePi decisions locally from the shared V4 pixels, and then runs the
pre-registered equal-budget policies on matching condition IDs.
"""
from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing.simulation.budget_competition import BudgetResult, run_budget_competition
from interaction_sensing.simulation.factorial_benchmark_v4 import run_factorial_v4
from interaction_sensing.simulation.factorial_world_v4 import suite_fingerprint


def read_pollipi_factorial_trace(path: str | Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    provenance = [row for row in records if row.get("record_type") == "provenance"]
    results = [row for row in records if row.get("record_type") == "result"]
    if len(provenance) != 1:
        raise ValueError("PolliPi V4 trace needs exactly one provenance record")
    prov = provenance[0]
    if prov.get("schema") != "pollipi-insepi-factorial-v4":
        raise ValueError("unexpected PolliPi V4 schema")
    if prov.get("world_fingerprint") != suite_fingerprint():
        raise ValueError("PolliPi/InsePi V4 world fingerprint mismatch")
    if not prov.get("source_commit"):
        raise ValueError("PolliPi V4 trace is missing source_commit provenance")
    if not results:
        raise ValueError("PolliPi V4 trace has no result records")
    return prov, results


def run_factorial_cross_v4(
    pollipi_trace_path: str | Path,
    *,
    budget_fraction: float = 0.25,
    world_windows: int = 4800,
    replicates: int = 200,
    seed: int = 20260821,
) -> tuple[dict[str, object], list[BudgetResult]]:
    provenance, pollipi_rows = read_pollipi_factorial_trace(pollipi_trace_path)
    insepi_rows = [row.to_dict() for row in run_factorial_v4()]
    results = run_budget_competition(
        pollipi_rows,
        insepi_rows,
        budget_fraction=budget_fraction,
        world_windows=world_windows,
        replicates=replicates,
        seed=seed,
    )
    return provenance, results
