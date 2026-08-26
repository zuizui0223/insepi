"""Join independent PolliPi and InsePi contradiction traces.

This module is intentionally a *trace* comparator, not a shared classifier.
Each project first makes its own decision.  Only afterwards do we ask where the
biological-evidence view and the observability view agree or compete.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable, Mapping


CONTRADICTION_SCHEMA = "pollipi-insepi-contradiction-v1"
_POLLIPI_CANDIDATE = {"strong_visitation_candidate", "uncertain_local_activity"}
_OBSERVATION_RISKY = {"audit_priority", "unobservable"}


@dataclass(frozen=True, slots=True)
class DisagreementResult:
    scenario_id: str
    true_visit: bool
    noise_source: str
    pollipi_state: str
    observability_state: str
    category: str
    disagreement_score: float
    requires_audit: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def classify_disagreement(
    *,
    true_visit: bool,
    pollipi_state: str,
    observability_state: str,
) -> tuple[str, float]:
    """Classify simulation-only tension between independent decisions.

    ``true_visit`` is latent simulator truth.  A future field comparator must
    not assume this value exists; it should use human/audit labels instead.
    """

    if pollipi_state in _POLLIPI_CANDIDATE and not true_visit:
        return "false_candidate", 1.0

    if (
        pollipi_state == "environmental_noise"
        and observability_state in _OBSERVATION_RISKY
        and true_visit
    ):
        return "visit_suppressed_where_observation_is_risky", 1.0

    if (
        pollipi_state == "no_activity"
        and observability_state in _OBSERVATION_RISKY
        and true_visit
    ):
        return "missed_visit_in_unreliable_window", 1.0

    if (
        pollipi_state in {"no_activity", "environmental_noise"}
        and observability_state == "clean"
        and true_visit
    ):
        return "pollipi_miss_under_clean_observation", 1.0

    if pollipi_state in _POLLIPI_CANDIDATE and observability_state in _OBSERVATION_RISKY:
        return "candidate_requires_audit", 0.8

    if pollipi_state == "environmental_noise" and observability_state in _OBSERVATION_RISKY:
        return "shared_noise_detection", 0.1

    if pollipi_state == "strong_visitation_candidate" and observability_state == "clean":
        return "supported_candidate", 0.0

    if pollipi_state == "no_activity" and not true_visit and observability_state == "clean":
        return "supported_absence", 0.0

    if pollipi_state in _POLLIPI_CANDIDATE and observability_state == "confounded":
        return "candidate_under_confounding", 0.5

    return "mixed_interpretation", 0.5


def compare_traces(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
) -> list[DisagreementResult]:
    """Join two independent traces by stable ``scenario_id``."""

    pollipi = {str(row["scenario_id"]): row for row in pollipi_rows}
    insepi = {str(row["scenario_id"]): row for row in insepi_rows}
    if set(pollipi) != set(insepi):
        missing_from_insepi = sorted(set(pollipi) - set(insepi))
        missing_from_pollipi = sorted(set(insepi) - set(pollipi))
        raise ValueError(
            "trace scenario mismatch: "
            f"missing_from_insepi={missing_from_insepi}, "
            f"missing_from_pollipi={missing_from_pollipi}"
        )

    results: list[DisagreementResult] = []
    for scenario_id in sorted(pollipi):
        p_row = pollipi[scenario_id]
        i_row = insepi[scenario_id]
        if p_row.get("schema") != CONTRADICTION_SCHEMA or i_row.get("schema") != CONTRADICTION_SCHEMA:
            raise ValueError(f"incompatible trace schema for {scenario_id}")
        if bool(p_row["true_visit"]) != bool(i_row["true_visit"]):
            raise ValueError(f"latent truth mismatch for {scenario_id}")
        if str(p_row["noise_source"]) != str(i_row["noise_source"]):
            raise ValueError(f"noise source mismatch for {scenario_id}")

        true_visit = bool(p_row["true_visit"])
        pollipi_state = str(p_row["pollipi_state"])
        observability_state = str(i_row["observability_state"])
        category, score = classify_disagreement(
            true_visit=true_visit,
            pollipi_state=pollipi_state,
            observability_state=observability_state,
        )
        results.append(
            DisagreementResult(
                scenario_id=scenario_id,
                true_visit=true_visit,
                noise_source=str(p_row["noise_source"]),
                pollipi_state=pollipi_state,
                observability_state=observability_state,
                category=category,
                disagreement_score=score,
                requires_audit=bool(i_row.get("capture_audit", False)) or score >= 0.8,
            )
        )
    return results


def summarize_disagreements(results: Iterable[DisagreementResult]) -> dict[str, object]:
    rows = list(results)
    by_category: dict[str, int] = {}
    for row in rows:
        by_category[row.category] = by_category.get(row.category, 0) + 1
    return {
        "n_scenarios": len(rows),
        "n_high_disagreement": sum(row.disagreement_score >= 0.8 for row in rows),
        "mean_disagreement_score": (
            sum(row.disagreement_score for row in rows) / len(rows) if rows else 0.0
        ),
        "by_category": dict(sorted(by_category.items())),
    }


def read_jsonl(path: str | Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def compare_jsonl(pollipi_path: str | Path, insepi_path: str | Path) -> list[DisagreementResult]:
    return compare_traces(read_jsonl(pollipi_path), read_jsonl(insepi_path))
