#!/usr/bin/env python3
"""Post-result diagnosis of nuisance process-score compression."""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalPoint, signature_for, temporally_resolved

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14b_nuisance_score_distribution_diagnosis_protocol.json"
WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"


def _coordinates(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep = world["focused_collision_sweep"]
    values = [sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"], sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"]]
    return [SpatiotemporalPoint(*(float(v) for v in coord)) for coord in itertools.product(*values)]


def _summary(values: list[float], threshold: float) -> dict[str, float]:
    a = np.asarray(values, dtype=float)
    return {
        "n": int(a.size),
        "q10": float(np.quantile(a, 0.10)),
        "median": float(np.median(a)),
        "q90": float(np.quantile(a, 0.90)),
        "pass_rate": float(np.mean(a >= threshold)),
    }


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    p = json.loads(protocol_path.read_text(encoding="utf-8"))
    if p.get("schema") != "insepi-v14b-nuisance-score-distribution-diagnosis-protocol-v1":
        raise ValueError("unexpected nuisance score diagnosis protocol schema")
    world = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    frozen = world["operational_thresholds_prefrozen"]
    min_samples = float(frozen["minimum_samples_per_process_timescale_for_resolved_slice"])
    min_timescales = float(frozen["minimum_process_timescales_per_window_for_resolved_slice"])
    seeds = [int(x) for x in p["frozen_inputs"]["validation_seeds"]]
    threshold = float(p["frozen_inputs"]["threshold"])

    by_pi5: dict[float, dict[str, list[float]]] = {}
    combined_by_pi2_pi5: dict[tuple[float, float], list[float]] = {}
    target_only: list[float] = []
    target_coupled: list[float] = []

    for point in _coordinates(world):
        if not temporally_resolved(point, minimum_samples=min_samples, minimum_timescales_per_window=min_timescales):
            continue
        bucket = by_pi5.setdefault(point.pi5, {"spatial": [], "temporal": [], "combined": []})
        for seed in seeds:
            n = observe_nuisance_v14b(signature_for(point, LatentRegime.NUISANCE_ONLY, seed=seed))
            bucket["spatial"].append(n.spatial_process_support)
            bucket["temporal"].append(n.temporal_process_support)
            bucket["combined"].append(n.nuisance_process_support)
            combined_by_pi2_pi5.setdefault((point.pi2, point.pi5), []).append(n.nuisance_process_support)
            target_only.append(observe_nuisance_v14b(signature_for(point, LatentRegime.TARGET_ONLY, seed=seed)).nuisance_process_support)
            target_coupled.append(observe_nuisance_v14b(signature_for(point, LatentRegime.TARGET_COUPLED, seed=seed)).nuisance_process_support)

    pi5_summary = {
        f"{pi5:.12g}": {
            "spatial": _summary(parts["spatial"], threshold),
            "temporal": _summary(parts["temporal"], threshold),
            "combined": _summary(parts["combined"], threshold),
        }
        for pi5, parts in sorted(by_pi5.items())
    }
    grid = {
        f"pi2={pi2:.12g}|pi5={pi5:.12g}": _summary(values, threshold)
        for (pi2, pi5), values in sorted(combined_by_pi2_pi5.items())
    }

    pi5_levels = sorted(by_pi5)
    near = pi5_summary.get("1")
    larger = [pi5_summary[f"{v:.12g}"]["combined"]["pass_rate"] for v in pi5_levels if v > 1.0]
    largest = pi5_summary[f"{max(pi5_levels):.12g}"]
    near_recall = float("nan") if near is None else float(near["combined"]["pass_rate"])
    any_large_good = bool(larger and max(larger) >= 0.80)

    if np.isfinite(near_recall) and near_recall < 0.50 and any_large_good:
        classification = "coherent_stratum_definition_defect"
    elif largest["temporal"]["pass_rate"] >= 0.80 and largest["spatial"]["pass_rate"] < 0.80:
        classification = "spatial_representation_bottleneck"
    elif largest["spatial"]["pass_rate"] >= 0.80 and largest["temporal"]["pass_rate"] < 0.80:
        classification = "temporal_representation_bottleneck"
    elif largest["spatial"]["pass_rate"] >= 0.80 and largest["temporal"]["pass_rate"] >= 0.80 and largest["combined"]["pass_rate"] < 0.80:
        classification = "aggregation_bottleneck"
    else:
        classification = "mixed_or_unresolved"

    result = {
        "schema": "insepi-v14b-nuisance-score-distribution-diagnosis-result-v1",
        "threshold": threshold,
        "pi5_component_summaries": pi5_summary,
        "pi2_pi5_combined_summaries": grid,
        "target_only_process_support_max": float(np.max(target_only)),
        "target_coupled_process_support_max": float(np.max(target_coupled)),
        "prefrozen_failure_classification": classification,
        "claim_boundary": p["claim_boundary"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--output", default="v14b_nuisance_diag/nuisance_score_distribution.json")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.protocol), Path(args.output)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
