"""One-shot cross-repository evaluator for locked V5 validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from interaction_sensing.simulation.budget_competition import (
    BudgetResult,
    _latent_error_types,
    allocation_score,
    run_budget_competition,
)
from interaction_sensing.simulation.factorial_cross_v4 import (
    CROSS_POLICIES,
    DEFAULT_BUDGETS,
    pareto_frontier,
)
from interaction_sensing.simulation.locked_benchmark_v5 import run_locked_v5
from interaction_sensing.simulation.locked_world_v5 import (
    PREVALENCE_REGIMES,
    build_registry,
    derive_competition_seed,
    seed_material,
    suite_fingerprint,
)

SCHEMA = "pollipi-insepi-locked-v5"
REPORT_SCHEMA = "pollipi-insepi-locked-v5-report"
SCARCE_BUDGETS = (0.10, 0.25)
DISTURBANCE_TV_CEILING = 0.80
MIN_COMPLEMENTARY_SUPPORT_FAMILIES = 2


@dataclass(frozen=True, slots=True)
class LockedGridPoint:
    prevalence_regime: str
    budget_fraction: float
    results: tuple[BudgetResult, ...]
    pareto_policies: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "prevalence_regime": self.prevalence_regime,
            "budget_fraction": self.budget_fraction,
            "pareto_policies": list(self.pareto_policies),
            "results": [row.to_dict() for row in self.results],
        }


@dataclass(frozen=True, slots=True)
class LockedV5Report:
    provenance: Mapping[str, object]
    evaluated_conditions: int
    world_windows: int
    replicates: int
    competition_seed: int
    complementary_support_families: Mapping[str, tuple[str, ...]]
    points: tuple[LockedGridPoint, ...]
    claim_status: str
    gate_failures: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": REPORT_SCHEMA,
            "provenance": dict(self.provenance),
            "evaluated_conditions": self.evaluated_conditions,
            "world_windows": self.world_windows,
            "replicates": self.replicates,
            "competition_seed": self.competition_seed,
            "complementary_support_families": {
                regime: list(families)
                for regime, families in self.complementary_support_families.items()
            },
            "claim_status": self.claim_status,
            "gate_failures": list(self.gate_failures),
            "points": [point.to_dict() for point in self.points],
        }


def read_pollipi_locked_trace(path: str | Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not records or not all(isinstance(row, dict) for row in records):
        raise ValueError("PolliPi locked V5 trace must contain JSON objects")
    if any(row.get("record_type") not in {"provenance", "result"} for row in records):
        raise ValueError("PolliPi locked V5 trace contains an unknown record type")
    provenance_rows = [row for row in records if row.get("record_type") == "provenance"]
    results = [row for row in records if row.get("record_type") == "result"]
    if len(provenance_rows) != 1:
        raise ValueError("PolliPi locked V5 trace needs exactly one provenance record")
    provenance = provenance_rows[0]
    if provenance.get("schema") != SCHEMA:
        raise ValueError("unexpected PolliPi locked V5 schema")
    pollipi_commit = str(provenance.get("pollipi_source_commit", ""))
    insepi_commit = str(provenance.get("insepi_source_commit", ""))
    expected_material_hash = hashlib.sha256(seed_material(pollipi_commit, insepi_commit)).hexdigest()
    if provenance.get("seed_material_sha256") != expected_material_hash:
        raise ValueError("locked V5 seed-material provenance mismatch")
    expected_fingerprint = suite_fingerprint(pollipi_commit, insepi_commit)
    if provenance.get("world_fingerprint") != expected_fingerprint:
        raise ValueError("PolliPi/InsePi locked V5 world fingerprint mismatch")
    if len(results) != len(build_registry(pollipi_commit, insepi_commit)):
        raise ValueError("PolliPi locked V5 trace has incomplete result coverage")
    return provenance, results


def _index_unique(rows: Sequence[Mapping[str, object]], observer: str) -> dict[str, Mapping[str, object]]:
    indexed: dict[str, Mapping[str, object]] = {}
    for row in rows:
        condition_id = str(row.get("condition_id", ""))
        if not condition_id:
            raise ValueError(f"{observer} locked V5 row is missing condition_id")
        if condition_id in indexed:
            raise ValueError(f"duplicate {observer} locked V5 condition_id: {condition_id}")
        indexed[condition_id] = row
    return indexed


def _validate_alignment(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    pollipi = _index_unique(pollipi_rows, "PolliPi")
    insepi = _index_unique(insepi_rows, "InsePi")
    if set(pollipi) != set(insepi):
        raise ValueError("PolliPi/InsePi locked V5 condition IDs differ")
    for condition_id in sorted(pollipi):
        p_row, i_row = pollipi[condition_id], insepi[condition_id]
        if p_row.get("schema") != SCHEMA or i_row.get("schema") != SCHEMA:
            raise ValueError(f"unexpected locked V5 result schema: {condition_id}")
        for key in ("prevalence_regime", "true_visit", "disturbance_family"):
            if p_row.get(key) != i_row.get(key):
                raise ValueError(f"PolliPi/InsePi locked V5 {key} mismatch: {condition_id}")
    ordered = sorted(pollipi)
    return [pollipi[key] for key in ordered], [insepi[key] for key in ordered]


def _checkout_state() -> tuple[str, bool]:
    """Return the source HEAD and tracked-file cleanliness for provenance."""

    start = Path(__file__).resolve()
    root = next((parent for parent in start.parents if (parent / ".git").exists()), None)
    if root is None:
        raise RuntimeError("locked V5 evaluation requires an InsePi Git checkout")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip().lower()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return head, not status


def _require_frozen_checkout(insepi_commit_sha: str) -> None:
    head, tracked_clean = _checkout_state()
    if head != insepi_commit_sha.strip().lower():
        raise RuntimeError("InsePi locked V5 source commit does not match checkout HEAD")
    if not tracked_clean:
        raise RuntimeError("InsePi locked V5 checkout has uncommitted tracked changes")


def evaluate_scarce_budget_gate(points: Sequence[LockedGridPoint]) -> tuple[str, tuple[str, ...]]:
    failures: list[str] = []
    expected_regimes = {name for name, _ in PREVALENCE_REGIMES}
    for regime in sorted(expected_regimes):
        for budget in SCARCE_BUDGETS:
            matches = [
                point for point in points
                if point.prevalence_regime == regime and abs(point.budget_fraction - budget) < 1e-12
            ]
            if len(matches) != 1:
                failures.append(f"{regime}@{budget:.2f}: missing locked grid point")
                continue
            point = matches[0]
            by_policy = {row.policy: row for row in point.results}
            required = {
                "union",
                "intersection",
                "disagreement",
                "disagreement_pollipi_only",
                "disagreement_insepi_only",
            }
            if not required <= set(by_policy):
                failures.append(f"{regime}@{budget:.2f}: missing gate policy")
                continue
            full = by_policy["disagreement"]
            removals = (
                by_policy["disagreement_pollipi_only"],
                by_policy["disagreement_insepi_only"],
            )
            if "disagreement" not in point.pareto_policies:
                failures.append(f"{regime}@{budget:.2f}: disagreement is off the central Pareto frontier")
            if full.hidden_error_recall <= max(row.hidden_error_recall for row in removals):
                failures.append(f"{regime}@{budget:.2f}: no hidden-error gain over both single-view removals")
            if full.missed_event_audit_yield <= max(
                by_policy["union"].missed_event_audit_yield,
                by_policy["intersection"].missed_event_audit_yield,
            ):
                failures.append(f"{regime}@{budget:.2f}: missed-event yield is reproduced by OR/AND")
            if full.disturbance_tv_distance > DISTURBANCE_TV_CEILING:
                failures.append(f"{regime}@{budget:.2f}: disturbance TV exceeds preregistered ceiling")
    return ("pass" if not failures else "fail", tuple(failures))


def complementary_support_families(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
) -> dict[str, tuple[str, ...]]:
    """Identify families where joint disagreement adds priority to a hidden error."""

    support: dict[str, set[str]] = {regime: set() for regime, _ in PREVALENCE_REGIMES}
    for pollipi, insepi in zip(pollipi_rows, insepi_rows):
        if not _latent_error_types(pollipi, insepi):
            continue
        joint = allocation_score("disagreement", pollipi, insepi)
        pollipi_only = allocation_score("disagreement_pollipi_only", pollipi, insepi)
        insepi_only = allocation_score("disagreement_insepi_only", pollipi, insepi)
        if joint > max(pollipi_only, insepi_only):
            regime = str(pollipi["prevalence_regime"])
            support[regime].add(str(pollipi["disturbance_family"]))
    return {regime: tuple(sorted(families)) for regime, families in support.items()}


def evaluate_family_support_gate(
    support: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    failures = []
    for regime, _ in PREVALENCE_REGIMES:
        families = set(support.get(regime, ()))
        if len(families) < MIN_COMPLEMENTARY_SUPPORT_FAMILIES:
            failures.append(
                f"{regime}: joint priority has hidden-error support in fewer than "
                f"{MIN_COMPLEMENTARY_SUPPORT_FAMILIES} disturbance families"
            )
    return tuple(failures)


def run_locked_cross_v5(
    pollipi_trace_path: str | Path,
    *,
    budgets: Sequence[float] = DEFAULT_BUDGETS,
    policies: Sequence[str] = CROSS_POLICIES,
    world_windows: int = 4800,
    replicates: int = 200,
) -> LockedV5Report:
    provenance, pollipi_rows = read_pollipi_locked_trace(pollipi_trace_path)
    pollipi_commit = str(provenance["pollipi_source_commit"])
    insepi_commit = str(provenance["insepi_source_commit"])
    _require_frozen_checkout(insepi_commit)
    insepi_rows = [row.to_dict() for row in run_locked_v5(pollipi_commit, insepi_commit)]
    pollipi_rows, insepi_rows = _validate_alignment(pollipi_rows, insepi_rows)
    family_support = complementary_support_families(pollipi_rows, insepi_rows)
    competition_seed = derive_competition_seed(pollipi_commit, insepi_commit)
    points: list[LockedGridPoint] = []
    for regime, _ in PREVALENCE_REGIMES:
        p_regime = [row for row in pollipi_rows if row["prevalence_regime"] == regime]
        i_regime = [row for row in insepi_rows if row["prevalence_regime"] == regime]
        for budget in budgets:
            results = tuple(run_budget_competition(
                p_regime,
                i_regime,
                policies=policies,
                budget_fraction=budget,
                world_windows=world_windows,
                replicates=replicates,
                seed=competition_seed,
            ))
            points.append(LockedGridPoint(
                prevalence_regime=regime,
                budget_fraction=budget,
                results=results,
                pareto_policies=pareto_frontier(results),
            ))
    status, failures = evaluate_scarce_budget_gate(points)
    failures = failures + evaluate_family_support_gate(family_support)
    status = "pass" if not failures else "fail"
    return LockedV5Report(
        provenance=provenance,
        evaluated_conditions=len(pollipi_rows),
        world_windows=world_windows,
        replicates=replicates,
        competition_seed=competition_seed,
        complementary_support_families=family_support,
        points=tuple(points),
        claim_status=status,
        gate_failures=failures,
    )


def write_locked_v5_report(path: str | Path, report: LockedV5Report) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(report.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the one-shot locked V5 competition")
    parser.add_argument("pollipi_trace", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = run_locked_cross_v5(args.pollipi_trace)
    write_locked_v5_report(args.output, report)


if __name__ == "__main__":
    main()
