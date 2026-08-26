#!/usr/bin/env python3
"""Validate the V14b target-only representation with nuisance observer frozen."""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    observation_support,
    signature_for,
    temporally_resolved,
)
from interaction_sensing.target_observer_v14b import observe_target_v14b

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14b_target_observer_direct_first_protocol.json"
WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"


def _coordinates(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep = world["focused_collision_sweep"]
    values = [
        sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"],
        sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"],
    ]
    return [SpatiotemporalPoint(*(float(v) for v in coord)) for coord in itertools.product(*values)]


def _stratum(point: SpatiotemporalPoint) -> str:
    temporal = "low" if point.pi2 < 1.0 else "near" if point.pi2 == 1.0 else "high"
    spatial = "low" if point.pi5 < 1.0 else "near" if point.pi5 == 1.0 else "high"
    return f"pi2_{temporal}__pi5_{spatial}"


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "insepi-v14b-target-observer-direct-first-protocol-v2":
        raise ValueError("unexpected target observer protocol schema")
    world = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    frozen = world["operational_thresholds_prefrozen"]
    min_samples = float(frozen["minimum_samples_per_process_timescale_for_resolved_slice"])
    min_timescales = float(frozen["minimum_process_timescales_per_window_for_resolved_slice"])
    support_min = float(protocol["validation_rules"]["target_observation_support_minimum"])
    seeds = [int(v) for v in protocol["validation_rules"]["validation_seeds"]]

    counts = Counter()
    contradictions: dict[str, set[str]] = {
        "direct_false_positive_without_direct_signal": set(),
        "direct_missed_despite_direct_signal": set(),
        "indirect_only_forced_positive": set(),
    }
    strata_seen: set[str] = set()

    for point in _coordinates(world):
        if not temporally_resolved(point, minimum_samples=min_samples, minimum_timescales_per_window=min_timescales):
            continue
        stratum = _stratum(point)
        strata_seen.add(stratum)

        for seed in seeds:
            nuisance_obs = observe_target_v14b(signature_for(point, LatentRegime.NUISANCE_ONLY, seed=seed))
            counts["nuisance_only_n"] += 1
            counts["nuisance_only_supported"] += int(nuisance_obs.target_supported)
            if nuisance_obs.target_supported:
                contradictions["direct_false_positive_without_direct_signal"].add(stratum)

        if observation_support(point, coupling_available=False) >= support_min:
            for seed in seeds:
                obs = observe_target_v14b(
                    signature_for(point, LatentRegime.TARGET_NUISANCE_SUPERPOSED, seed=seed)
                )
                counts["superposed_n"] += 1
                counts["superposed_supported"] += int(obs.target_supported)
                if point.pi3 > 0 and not obs.target_supported:
                    contradictions["direct_missed_despite_direct_signal"].add(stratum)

        if observation_support(point, coupling_available=True) >= support_min:
            for seed in seeds:
                obs = observe_target_v14b(
                    signature_for(point, LatentRegime.TARGET_NUISANCE_COUPLED, seed=seed)
                )
                if point.pi3 > 0:
                    counts["coupled_direct_n"] += 1
                    counts["coupled_direct_supported"] += int(obs.target_supported)
                    if not obs.target_supported:
                        contradictions["direct_missed_despite_direct_signal"].add(stratum)
                else:
                    counts["coupled_indirect_only_n"] += 1
                    counts["coupled_indirect_only_supported"] += int(obs.target_supported)
                    counts["coupled_indirect_only_inference_undetermined"] += int(not obs.target_supported)
                    if obs.target_supported:
                        contradictions["indirect_only_forced_positive"].add(stratum)

    def rate(num: str, den: str) -> float:
        return 0.0 if counts[den] == 0 else counts[num] / counts[den]

    metrics = {
        "nuisance_only_target_support_rate": rate("nuisance_only_supported", "nuisance_only_n"),
        "direct_visible_superposed_target_support_rate": rate("superposed_supported", "superposed_n"),
        "direct_visible_coupled_target_support_rate": rate("coupled_direct_supported", "coupled_direct_n"),
        "indirect_only_coupled_target_support_rate": rate("coupled_indirect_only_supported", "coupled_indirect_only_n"),
        "indirect_only_coupled_inference_undetermined_rate": rate(
            "coupled_indirect_only_inference_undetermined", "coupled_indirect_only_n"
        ),
    }
    expected = {k: float(v) for k, v in protocol["prefrozen_expected_invariants"].items()}
    invariant_checks = {key: metrics[key] == value for key, value in expected.items()}
    contradiction_summary = {key: sorted(value) for key, value in contradictions.items() if value}

    result = {
        "schema": "insepi-v14b-target-observer-direct-first-validation-v2",
        "metrics": metrics,
        "expected_invariants": expected,
        "invariant_checks": invariant_checks,
        "all_invariants_hold": all(invariant_checks.values()),
        "contradiction_types_observed": contradiction_summary,
        "new_contradiction_type_count": len(contradiction_summary),
        "strata_seen": sorted(strata_seen),
        "target_side_type_saturated": all(invariant_checks.values()) and len(contradiction_summary) == 0,
        "nuisance_observer_modified": False,
        "claim_boundary": protocol["claim_boundary"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--output", default="v14b_output/target_direct_first_validation_v2.json")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.protocol), Path(args.output)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
