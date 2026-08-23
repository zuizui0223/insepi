"""Trace-only evaluator for the preregistered V10 real-pixel validation.

Observer traces contain no perturbation truth.  This evaluator joins condition
truth and panel membership from the byte-frozen V10 registries only after both
observer decisions have been emitted.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
from statistics import mean, median
from typing import Mapping, Sequence

from interaction_sensing.guarded_portfolio import GuardedPortfolio, select_guarded_indices
from interaction_sensing.simulation.real_video_artifact_v10 import (
    V10LoadedArtifact,
    load_v10_artifact,
    sha256_file,
)

REPORT_SCHEMA = "interaction-sensing-v10-locked-report-v1"
POLLIPI_TRACE_SCHEMA = "pollipi-insepi-v10-pollipi-trace-v1"
INSEPI_TRACE_SCHEMA = "pollipi-insepi-v10-insepi-trace-v1"
POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"
PIXEL_SHA256 = "b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66"
CONDITION_REGISTRY_SHA256 = "1689f5ce102abfef722e3e8667e8c6e290a42fe1d4563c1655b7f14520cde393"
PANEL_REGISTRY_SHA256 = "b1e59cda67977e5ab8d09e1ea28236b442d72c616c92df0c22adca89122cac8a"
SELECTION_SEED_DOMAIN = "interaction-sensing-v10-panel-selection-v1"
BUDGETS = ((0.10, "0.10"), (0.25, "0.25"), (0.50, "0.50"))
REPLICATES = 200

POLLIPI_PROVENANCE_KEYS = {
    "record_type", "schema", "source_commit", "pixel_artifact_sha256",
    "condition_registry_sha256", "condition_count",
}
INSEPI_PROVENANCE_KEYS = POLLIPI_PROVENANCE_KEYS | {"occlusion_threshold"}
POLLIPI_RESULT_KEYS = {
    "record_type", "schema", "condition_index", "condition_id",
    "pollipi_state", "pollipi_reason", "global_synchrony",
    "active_cell_proportion", "estimated_global_shift",
}
INSEPI_RESULT_KEYS = {
    "record_type", "schema", "condition_index", "condition_id",
    "inferred_noise_source", "observability_state", "false_event_risk",
    "missed_event_risk", "attribution_risk", "local_structure_loss",
    "occlusion_threshold",
}
EVIDENCE_SCORE = {
    "strong_visitation_candidate": 1.0,
    "uncertain_local_activity": 0.70,
    "environmental_noise": 0.0,
    "no_activity": 0.0,
}
POLICIES = (
    "uniform",
    "guarded_v6",
    "guarded_e_only",
    "guarded_o_only",
    "guarded_fused_20_80",
    "guarded_max",
)


@dataclass(frozen=True, slots=True)
class TraceData:
    provenance: Mapping[str, object]
    rows: tuple[Mapping[str, object], ...]
    sha256: str


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_trace(
    path: Path,
    *,
    schema: str,
    expected_commit: str,
    provenance_keys: set[str],
    result_keys: set[str],
    artifact: V10LoadedArtifact,
) -> TraceData:
    payloads: list[object] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise RuntimeError(f"blank trace line at {line_number}")
            payloads.append(json.loads(line))
    if len(payloads) != 6917:
        raise RuntimeError(f"V10 trace must contain provenance + 6916 results, got {len(payloads)}")
    provenance = payloads[0]
    if not isinstance(provenance, dict) or set(provenance) != provenance_keys:
        raise RuntimeError("V10 trace provenance key set differs from frozen contract")
    if provenance.get("record_type") != "provenance" or provenance.get("schema") != schema:
        raise RuntimeError("V10 trace provenance schema mismatch")
    if provenance.get("source_commit") != expected_commit:
        raise RuntimeError("V10 trace source commit is not the exact frozen V5 commit")
    if provenance.get("pixel_artifact_sha256") != PIXEL_SHA256:
        raise RuntimeError("V10 trace pixel artifact identity mismatch")
    if provenance.get("condition_registry_sha256") != CONDITION_REGISTRY_SHA256:
        raise RuntimeError("V10 trace condition-registry identity mismatch")
    if int(provenance.get("condition_count", -1)) != 6916:
        raise RuntimeError("V10 trace condition count mismatch")

    rows: list[Mapping[str, object]] = []
    for expected_index, raw in enumerate(payloads[1:]):
        if not isinstance(raw, dict) or set(raw) != result_keys:
            raise RuntimeError(f"V10 trace result key set differs at condition {expected_index}")
        if raw.get("record_type") != "result" or raw.get("schema") != schema:
            raise RuntimeError(f"V10 trace result schema mismatch at condition {expected_index}")
        if int(raw.get("condition_index", -1)) != expected_index:
            raise RuntimeError("V10 trace is not in canonical condition-index order")
        registry = artifact.condition_registry[expected_index]
        if str(raw.get("condition_id")) != str(registry["condition_id"]):
            raise RuntimeError("V10 trace condition id does not match frozen registry")
        rows.append(raw)
    return TraceData(provenance=provenance, rows=tuple(rows), sha256=sha256_file(path))


def load_traces(artifact: V10LoadedArtifact, pollipi_path: Path, insepi_path: Path) -> tuple[TraceData, TraceData]:
    pollipi = _load_trace(
        pollipi_path,
        schema=POLLIPI_TRACE_SCHEMA,
        expected_commit=POLLIPI_COMMIT,
        provenance_keys=POLLIPI_PROVENANCE_KEYS,
        result_keys=POLLIPI_RESULT_KEYS,
        artifact=artifact,
    )
    insepi = _load_trace(
        insepi_path,
        schema=INSEPI_TRACE_SCHEMA,
        expected_commit=INSEPI_COMMIT,
        provenance_keys=INSEPI_PROVENANCE_KEYS,
        result_keys=INSEPI_RESULT_KEYS,
        artifact=artifact,
    )
    return pollipi, insepi


def evidence_score(row: Mapping[str, object]) -> float:
    state = str(row["pollipi_state"])
    if state not in EVIDENCE_SCORE:
        raise RuntimeError(f"unknown frozen PolliPi state in V10 trace: {state}")
    return EVIDENCE_SCORE[state]


def observability_risk(row: Mapping[str, object]) -> float:
    values = [float(row[key]) for key in ("false_event_risk", "missed_event_risk", "attribution_risk")]
    if any((not isfinite(value) or value < 0.0 or value > 1.0) for value in values):
        raise RuntimeError(f"invalid frozen InsePi risk values: {values}")
    return max(values)


def _candidate(row: Mapping[str, object]) -> bool:
    return evidence_score(row) > 0.0


def _variant_map(artifact: V10LoadedArtifact) -> dict[tuple[str, int], int]:
    mapping: dict[tuple[str, int], int] = {}
    for row in artifact.variant_registry:
        if row["family"] is None:
            continue
        key = (str(row["family"]), int(row["tier_index"]))
        mapping[key] = int(row["variant_index"])
    if len(mapping) != 18:
        raise RuntimeError("V10 variant family/tier registry is not complete")
    return mapping


def _condition_index(base_index: int, variant_index: int) -> int:
    return int(base_index) * 19 + int(variant_index)


def _observer_transfer(
    artifact: V10LoadedArtifact,
    pollipi: TraceData,
    insepi: TraceData,
) -> dict[str, object]:
    variants = _variant_map(artifact)
    native_risk = [observability_risk(insepi.rows[_condition_index(base, 0)]) for base in range(364)]
    native_candidate = [_candidate(pollipi.rows[_condition_index(base, 0)]) for base in range(364)]
    native_state = [str(pollipi.rows[_condition_index(base, 0)]["pollipi_state"]) for base in range(364)]

    family_tier: list[dict[str, object]] = []
    family_absolute_risk: dict[str, list[float]] = {}
    family_high_delta: dict[str, float] = {}
    pooled_delta_by_tier: dict[int, list[float]] = {0: [], 1: [], 2: []}

    for family in ("shadow", "occlusion", "blur", "sensor_banding", "glare", "framing_drift"):
        tier_medians: list[float] = []
        for tier_index in range(3):
            variant_index = variants[(family, tier_index)]
            risks = [observability_risk(insepi.rows[_condition_index(base, variant_index)]) for base in range(364)]
            deltas = [risks[base] - native_risk[base] for base in range(364)]
            pooled_delta_by_tier[tier_index].extend(deltas)
            tier_medians.append(float(median(risks)))
            pert_candidate = [_candidate(pollipi.rows[_condition_index(base, variant_index)]) for base in range(364)]
            eligible = [base for base in range(364) if native_state[base] != "environmental_noise"]
            transitioned = sum(
                str(pollipi.rows[_condition_index(base, variant_index)]["pollipi_state"]) == "environmental_noise"
                for base in eligible
            )
            row = {
                "family": family,
                "tier_index": tier_index,
                "variant_index": variant_index,
                "median_insepi_risk": float(median(risks)),
                "median_paired_risk_delta": float(median(deltas)),
                "fraction_paired_risk_delta_positive": sum(value > 0.0 for value in deltas) / len(deltas),
                "native_pollipi_candidate_rate": sum(native_candidate) / len(native_candidate),
                "perturbed_pollipi_candidate_rate": sum(pert_candidate) / len(pert_candidate),
                "absolute_pollipi_candidate_rate_change": abs(sum(pert_candidate) / len(pert_candidate) - sum(native_candidate) / len(native_candidate)),
                "environmental_noise_transition_rate": transitioned / len(eligible) if eligible else 0.0,
                "environmental_noise_transition_denominator": len(eligible),
            }
            family_tier.append(row)
            if tier_index == 2:
                family_high_delta[family] = row["median_paired_risk_delta"]
        family_absolute_risk[family] = tier_medians

    family_summary = []
    for family, tier_medians in family_absolute_risk.items():
        family_summary.append({
            "family": family,
            "median_risk_by_tier": tier_medians,
            "dose_monotone": tier_medians[0] <= tier_medians[1] <= tier_medians[2],
            "high_tier_median_paired_risk_delta": float(family_high_delta[family]),
            "high_tier_positive": float(family_high_delta[family]) > 0.0,
        })
    global_by_tier = [
        {"tier_index": tier, "global_median_paired_risk_delta": float(median(pooled_delta_by_tier[tier]))}
        for tier in range(3)
    ]
    return {
        "family_tier": family_tier,
        "family_summary": family_summary,
        "global_by_tier": global_by_tier,
        "positive_high_tier_family_count": sum(bool(row["high_tier_positive"]) for row in family_summary),
        "dose_monotone_family_count": sum(bool(row["dose_monotone"]) for row in family_summary),
        "global_high_tier_median_risk_delta": global_by_tier[2]["global_median_paired_risk_delta"],
    }


def selection_seed(panel_id: str, budget_token: str, replicate_index: int) -> int:
    text = f"{SELECTION_SEED_DOMAIN}|{panel_id}|{budget_token}|{int(replicate_index)}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def _policy(policy: str) -> GuardedPortfolio:
    if policy == "uniform":
        return GuardedPortfolio(exploration=1.0, arms=())
    if policy == "guarded_v6":
        return GuardedPortfolio.frozen_v6_reference()
    if policy == "guarded_e_only":
        return GuardedPortfolio(exploration=0.50, arms=(("evidence", 0.50),))
    if policy == "guarded_o_only":
        return GuardedPortfolio(exploration=0.50, arms=(("observability", 0.50),))
    if policy == "guarded_fused_20_80":
        return GuardedPortfolio(exploration=0.50, arms=(("fused", 0.50),))
    if policy == "guarded_max":
        return GuardedPortfolio(exploration=0.50, arms=(("maximum", 0.50),))
    raise RuntimeError(f"unknown frozen V10 policy: {policy}")


def _score_rows(evidence: Sequence[float], observability: Sequence[float]) -> list[dict[str, float]]:
    return [
        {
            "evidence": float(evidence[index]),
            "observability": float(observability[index]),
            "fused": 0.20 * float(evidence[index]) + 0.80 * float(observability[index]),
            "maximum": max(float(evidence[index]), float(observability[index])),
        }
        for index in range(len(evidence))
    ]


def _categorical_tv(selected: set[int], full_rows: Sequence[Mapping[str, object]], keys: tuple[str, ...]) -> float:
    if not selected:
        raise RuntimeError("cannot compute representation TV for an empty selection")
    def category(row: Mapping[str, object]):
        return tuple(row[key] for key in keys)
    full_counts = Counter(category(row) for row in full_rows)
    selected_counts = Counter(category(full_rows[index]) for index in selected)
    full_n = len(full_rows)
    selected_n = len(selected)
    return 0.5 * sum(
        abs(selected_counts.get(cat, 0) / selected_n - count / full_n)
        for cat, count in full_counts.items()
    )


def _allocation_transfer(
    artifact: V10LoadedArtifact,
    pollipi: TraceData,
    insepi: TraceData,
) -> dict[str, object]:
    variants = _variant_map(artifact)
    cells: list[dict[str, object]] = []
    v6_cell_ratios: list[float] = []
    v6_pass_count = 0

    for panel in artifact.panel_registry:
        panel_id = str(panel["panel_id"])
        family = str(panel["family"])
        tier_index = int(panel["tier_index"])
        variant_index = variants[(family, tier_index)]
        disturbed = set(map(int, panel["disturbed_base_indices"]))
        if len(disturbed) != 182:
            raise RuntimeError("V10 panel disturbance truth changed")
        evidence: list[float] = []
        risk: list[float] = []
        for base_index in range(364):
            condition_index = _condition_index(base_index, variant_index if base_index in disturbed else 0)
            evidence.append(evidence_score(pollipi.rows[condition_index]))
            risk.append(observability_risk(insepi.rows[condition_index]))
        score_rows = _score_rows(evidence, risk)

        for budget_value, budget_token in BUDGETS:
            per_policy = {
                name: {"recall": [], "yield": [], "video_tv": [], "video_quartile_tv": [], "ratio": []}
                for name in POLICIES
            }
            for replicate_index in range(REPLICATES):
                seed = selection_seed(panel_id, budget_token, replicate_index)
                selected_by_policy: dict[str, set[int]] = {}
                for policy_name in POLICIES:
                    selected, _counts = select_guarded_indices(
                        score_rows,
                        budget_fraction=budget_value,
                        portfolio=_policy(policy_name),
                        seed=seed,
                    )
                    selected_by_policy[policy_name] = selected
                uniform_selected = selected_by_policy["uniform"]
                uniform_recall = len(uniform_selected & disturbed) / len(disturbed)
                if uniform_recall <= 0.0:
                    raise RuntimeError("paired uniform disturbance recall is zero; frozen rule forbids smoothing")
                for policy_name, selected in selected_by_policy.items():
                    recall = len(selected & disturbed) / len(disturbed)
                    hit_count = len(selected & disturbed)
                    stats = per_policy[policy_name]
                    stats["recall"].append(recall)
                    stats["yield"].append(float(hit_count))
                    stats["ratio"].append(recall / uniform_recall)
                    stats["video_tv"].append(_categorical_tv(selected, artifact.base_registry, ("video_index",)))
                    stats["video_quartile_tv"].append(_categorical_tv(selected, artifact.base_registry, ("video_index", "temporal_quartile")))

            for policy_name in POLICIES:
                stats = per_policy[policy_name]
                cell = {
                    "panel_id": panel_id,
                    "family": family,
                    "tier_index": tier_index,
                    "budget": budget_value,
                    "budget_token": budget_token,
                    "policy": policy_name,
                    "mean_known_disturbance_recall": mean(stats["recall"]),
                    "mean_paired_uniform_recall_ratio": mean(stats["ratio"]),
                    "mean_selected_known_disturbance_yield": mean(stats["yield"]),
                    "mean_source_video_tv": mean(stats["video_tv"]),
                    "mean_video_temporal_quartile_tv": mean(stats["video_quartile_tv"]),
                }
                cells.append(cell)
                if policy_name == "guarded_v6":
                    ratio = float(cell["mean_paired_uniform_recall_ratio"])
                    v6_cell_ratios.append(ratio)
                    v6_pass_count += int(ratio >= 1.0)

    if len(v6_cell_ratios) != 54:
        raise RuntimeError("V10 allocation did not produce 54 frozen V6 regime cells")
    overall = mean(v6_cell_ratios)
    allocation_pass = v6_pass_count >= 45 and overall > 1.0
    return {
        "cells": cells,
        "v6_cell_pass_count": v6_pass_count,
        "v6_cell_count": 54,
        "v6_overall_mean_paired_uniform_recall_ratio": overall,
        "v6_allocation_pass": allocation_pass,
    }


def _claim(observer: Mapping[str, object], allocation: Mapping[str, object]) -> tuple[str, str]:
    positive = int(observer["positive_high_tier_family_count"])
    monotone = int(observer["dose_monotone_family_count"])
    global_high = float(observer["global_high_tier_median_risk_delta"])
    allocation_pass = bool(allocation["v6_allocation_pass"])
    if positive <= 2 or global_high <= 0.0:
        return "D", "null_or_adverse_real_pixel_transfer"
    if positive >= 5 and monotone >= 4 and allocation_pass:
        return "A", "broad_real_pixel_transfer"
    if positive >= 5 and monotone >= 4 and not allocation_pass:
        return "B", "observer_transfer_allocation_mixed"
    return "C", "partial_or_family_specific_transfer"


def evaluate_v10(
    artifact_dir: str | Path,
    pollipi_trace: str | Path,
    insepi_trace: str | Path,
) -> dict[str, object]:
    artifact_root = Path(artifact_dir)
    artifact = load_v10_artifact(artifact_root)
    if sha256_file(artifact_root / "v10_real_pixel_artifact.npz") != PIXEL_SHA256:
        raise RuntimeError("V10 evaluator received the wrong pixel artifact")
    if sha256_file(artifact_root / "v10_condition_registry.json") != CONDITION_REGISTRY_SHA256:
        raise RuntimeError("V10 evaluator received the wrong condition registry")
    if sha256_file(artifact_root / "v10_panel_registry.json") != PANEL_REGISTRY_SHA256:
        raise RuntimeError("V10 evaluator received the wrong panel registry")
    pollipi, insepi = load_traces(artifact, Path(pollipi_trace), Path(insepi_trace))
    observer = _observer_transfer(artifact, pollipi, insepi)
    allocation = _allocation_transfer(artifact, pollipi, insepi)
    level, label = _claim(observer, allocation)
    return {
        "schema": REPORT_SCHEMA,
        "provenance": {
            "pixel_artifact_sha256": PIXEL_SHA256,
            "condition_registry_sha256": CONDITION_REGISTRY_SHA256,
            "panel_registry_sha256": PANEL_REGISTRY_SHA256,
            "pollipi_source_commit": POLLIPI_COMMIT,
            "insepi_source_commit": INSEPI_COMMIT,
            "pollipi_trace_sha256": pollipi.sha256,
            "insepi_trace_sha256": insepi.sha256,
            "condition_count": 6916,
            "truth_join_stage": "post-observer evaluator only",
        },
        "observer_transfer": observer,
        "allocation_transfer": allocation,
        "claim": {"level": level, "label": label},
        "forbidden_claims": [
            "field biological-event detection accuracy",
            "pollinator identification accuracy",
            "occupancy/detection-probability validity",
            "universal optimality of 50/10/40",
            "use of V10 to rescue or reinterpret V7",
        ],
    }
