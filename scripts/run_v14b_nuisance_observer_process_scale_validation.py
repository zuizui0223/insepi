#!/usr/bin/env python3
"""Validate V14b nuisance process evidence with target observer frozen."""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from interaction_sensing.evaluation.plateau_diagnosis import auc
from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    signature_for,
    temporally_resolved,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14b_nuisance_observer_process_scale_protocol.json"
WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"


def _coordinates(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep = world["focused_collision_sweep"]
    values = [
        sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"],
        sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"],
    ]
    return [SpatiotemporalPoint(*(float(v) for v in coord)) for coord in itertools.product(*values)]


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "insepi-v14b-nuisance-observer-process-scale-protocol-v1":
        raise ValueError("unexpected nuisance observer protocol schema")
    world = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    frozen = world["operational_thresholds_prefrozen"]
    min_samples = float(frozen["minimum_samples_per_process_timescale_for_resolved_slice"])
    min_timescales = float(frozen["minimum_process_timescales_per_window_for_resolved_slice"])
    seeds = [int(v) for v in protocol["validation_rules"]["validation_seeds"]]
    threshold = float(protocol["validation_rules"]["frozen_operational_positive_threshold"])

    nuisance_scores: list[float] = []
    target_only_scores: list[float] = []
    target_coupled_scores: list[float] = []
    coherent_nuisance_scores: list[float] = []
    low_pi5_nuisance_scores: list[float] = []
    strata_seen: set[str] = set()

    for point in _coordinates(world):
        if not temporally_resolved(
            point,
            minimum_samples=min_samples,
            minimum_timescales_per_window=min_timescales,
        ):
            continue
        strata_seen.add(
            f"pi2_{'low' if point.pi2 < 1 else 'near' if point.pi2 == 1 else 'high'}__"
            f"pi5_{'low' if point.pi5 < 1 else 'near' if point.pi5 == 1 else 'high'}"
        )
        for seed in seeds:
            nuisance = observe_nuisance_v14b(
                signature_for(point, LatentRegime.NUISANCE_ONLY, seed=seed)
            ).nuisance_process_support
            target_only = observe_nuisance_v14b(
                signature_for(point, LatentRegime.TARGET_ONLY, seed=seed)
            ).nuisance_process_support
            target_coupled = observe_nuisance_v14b(
                signature_for(point, LatentRegime.TARGET_COUPLED, seed=seed)
            ).nuisance_process_support
            nuisance_scores.append(nuisance)
            target_only_scores.append(target_only)
            target_coupled_scores.append(target_coupled)
            if point.pi5 >= 1.0:
                coherent_nuisance_scores.append(nuisance)
            else:
                low_pi5_nuisance_scores.append(nuisance)

    nuisance_arr = np.asarray(nuisance_scores, dtype=float)
    target_only_arr = np.asarray(target_only_scores, dtype=float)
    target_coupled_arr = np.asarray(target_coupled_scores, dtype=float)
    coherent_arr = np.asarray(coherent_nuisance_scores, dtype=float)
    low_pi5_arr = np.asarray(low_pi5_nuisance_scores, dtype=float)

    metrics = {
        "nuisance_vs_target_only_auc": auc(nuisance_arr, target_only_arr),
        "nuisance_vs_target_coupled_auc": auc(nuisance_arr, target_coupled_arr),
        "coherent_nuisance_recall_at_0_55": float(np.mean(coherent_arr >= threshold)),
        "target_only_false_positive_at_0_55": float(np.mean(target_only_arr >= threshold)),
        "target_coupled_false_positive_at_0_55": float(np.mean(target_coupled_arr >= threshold)),
        "low_pi5_nuisance_positive_rate_descriptive": float(np.mean(low_pi5_arr >= threshold)),
    }

    expected = protocol["prefrozen_expected_invariants"]
    checks = {
        "nuisance_vs_target_only_auc_min": metrics["nuisance_vs_target_only_auc"] >= float(expected["nuisance_vs_target_only_auc_min"]),
        "nuisance_vs_target_coupled_auc_min": metrics["nuisance_vs_target_coupled_auc"] >= float(expected["nuisance_vs_target_coupled_auc_min"]),
        "coherent_nuisance_recall_at_0_55_min": metrics["coherent_nuisance_recall_at_0_55"] >= float(expected["coherent_nuisance_recall_at_0_55_min"]),
        "target_only_false_positive_at_0_55_max": metrics["target_only_false_positive_at_0_55"] <= float(expected["target_only_false_positive_at_0_55_max"]),
        "target_coupled_false_positive_at_0_55_max": metrics["target_coupled_false_positive_at_0_55"] <= float(expected["target_coupled_false_positive_at_0_55_max"]),
    }

    contradictions = Counter()
    if not checks["target_only_false_positive_at_0_55_max"]:
        contradictions["nuisance_false_positive_on_target_only"] += 1
    if not checks["target_coupled_false_positive_at_0_55_max"]:
        contradictions["nuisance_false_positive_on_target_coupled"] += 1
    if not checks["coherent_nuisance_recall_at_0_55_min"]:
        contradictions["coherent_nuisance_missed_after_rescaling"] += 1

    result = {
        "schema": "insepi-v14b-nuisance-observer-process-scale-validation-v1",
        "metrics": metrics,
        "invariant_checks": checks,
        "all_invariants_hold": all(checks.values()),
        "contradiction_types_observed": dict(contradictions),
        "new_contradiction_type_count": len(contradictions),
        "strata_seen": sorted(strata_seen),
        "nuisance_side_type_saturated": all(checks.values()) and len(contradictions) == 0,
        "target_observer_modified": False,
        "claim_boundary": protocol["claim_boundary"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--output", default="v14b_nuisance_output/process_scale_validation.json")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.protocol), Path(args.output)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
