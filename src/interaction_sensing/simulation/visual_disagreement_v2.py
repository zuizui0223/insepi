"""Post-decision comparator for V2 identical-pixel traces.

The comparator never alters either front end. It consumes portable traces after
PolliPi and InsePi have independently processed the same rendered images.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping

VISUAL_SCHEMA = "pollipi-insepi-visual-contradiction-v2"
POLLIPI_CANDIDATE = {"strong_visitation_candidate", "uncertain_local_activity"}


@dataclass(frozen=True, slots=True)
class VisualDisagreement:
    scenario_id: str
    true_visit: bool
    pollipi_state: str
    observability_state: str
    inferred_noise_source: str
    disagreement_type: str
    observable_priority: float
    latent_error: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def observable_disagreement_priority(
    pollipi_state: str,
    observability_state: str,
    *,
    false_event_risk: float,
    missed_event_risk: float,
    attribution_risk: float,
) -> tuple[str, float]:
    """Compute audit priority without hidden truth or scenario labels."""

    candidate = pollipi_state in POLLIPI_CANDIDATE
    max_risk = max(false_event_risk, missed_event_risk, attribution_risk)
    risky = observability_state in {"audit_priority", "unobservable"} or max_risk >= 0.60
    if candidate and risky:
        return "candidate_vs_unreliable_observation", 1.00
    if not candidate and missed_event_risk >= 0.60:
        return "absence_vs_high_missed_risk", 0.98
    if pollipi_state == "environmental_noise" and max(false_event_risk, attribution_risk) >= 0.60:
        return "noise_suppression_vs_audit_risk", 0.92
    if candidate and observability_state == "clean":
        return "supported_candidate", 0.25
    if pollipi_state == "no_activity" and observability_state == "clean":
        return "supported_quiet", 0.05
    if pollipi_state == "environmental_noise" and risky:
        return "shared_noise_but_audit_worthy", 0.55
    return "mixed", 0.40


def _latent_error(true_visit: bool, pollipi_state: str, inferred_noise_source: str) -> str | None:
    """Simulation evaluation label. This value is never used in priority scoring."""

    candidate = pollipi_state in POLLIPI_CANDIDATE
    if true_visit and not candidate:
        return "missed_visit"
    if not true_visit and candidate:
        return "false_candidate"
    if candidate and inferred_noise_source == "multi_object_clutter":
        return "attribution_ambiguity"
    return None


def compare_visual_traces(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
) -> list[VisualDisagreement]:
    pollipi = {str(row["scenario_id"]): row for row in pollipi_rows}
    insepi = {str(row["scenario_id"]): row for row in insepi_rows}
    if set(pollipi) != set(insepi):
        raise ValueError("V2 trace scenario mismatch")

    rows: list[VisualDisagreement] = []
    for scenario_id in sorted(pollipi):
        p = pollipi[scenario_id]
        i = insepi[scenario_id]
        if p.get("schema") != VISUAL_SCHEMA or i.get("schema") != VISUAL_SCHEMA:
            raise ValueError(f"V2 schema mismatch for {scenario_id}")
        if bool(p["true_visit"]) != bool(i["true_visit"]):
            raise ValueError(f"V2 truth mismatch for {scenario_id}")
        p_state = str(p["pollipi_state"])
        o_state = str(i["observability_state"])
        noise_source = str(i["inferred_noise_source"])
        kind, priority = observable_disagreement_priority(
            p_state,
            o_state,
            false_event_risk=float(i.get("false_event_risk", 0.0)),
            missed_event_risk=float(i.get("missed_event_risk", 0.0)),
            attribution_risk=float(i.get("attribution_risk", 0.0)),
        )
        truth = bool(p["true_visit"])
        rows.append(VisualDisagreement(
            scenario_id=scenario_id,
            true_visit=truth,
            pollipi_state=p_state,
            observability_state=o_state,
            inferred_noise_source=noise_source,
            disagreement_type=kind,
            observable_priority=priority,
            latent_error=_latent_error(truth, p_state, noise_source),
        ))
    return rows
