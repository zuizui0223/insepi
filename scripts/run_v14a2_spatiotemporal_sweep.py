#!/usr/bin/env python3
"""Locked V14a2 phase-sweep runner.

A full sweep fails closed until a separate prefreeze receipt records the exact
scientific-file hashes. A tiny --smoke-limit run is allowed before receipt for
engineering checks and is always marked non-canonical.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from interaction_sensing.simulation.dimensionless_observability_v14 import (
    IndeterminacyReason,
    LatentRegime,
)
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    IndeterminacyReasonA2,
    SpatiotemporalPoint,
    VisitInferenceA2,
    temporally_resolved,
)
from interaction_sensing.simulation.v14a2_sweep import (
    FrozenThresholds,
    interpret_with_prototypes,
    prototype_vectors,
    replicate_seed,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"
DEFAULT_RECEIPT = ROOT / "benchmarks/v14a2_spatiotemporal_prefreeze_receipt.json"
GENERATOR_PATH = ROOT / "src/interaction_sensing/simulation/dimensionless_observability_v14a2.py"
HELPER_PATH = ROOT / "src/interaction_sensing/simulation/v14a2_sweep.py"
RUNNER_PATH = Path(__file__).resolve()

REGIME_BY_NAME = {item.value: item for item in LatentRegime}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(values: Iterable[float]) -> float:
    data = [float(value) for value in values]
    return float("nan") if not data else sum(data) / len(data)


def _thresholds(protocol: dict[str, Any]) -> FrozenThresholds:
    raw = protocol["operational_thresholds_prefrozen"]
    return FrozenThresholds(
        support_minimum=float(raw["minimum_observation_support"]),
        ambiguity_margin=float(raw["essential_ambiguity_margin"]),
        target_high=float(raw["target_high"]),
        target_low=float(raw["target_low"]),
        nuisance_high=float(raw["nuisance_high"]),
    )


def _verify_receipt(protocol_path: Path, receipt_path: Path) -> dict[str, Any]:
    if not receipt_path.exists():
        raise RuntimeError("full V14a2 sweep is locked: prefreeze receipt is absent")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != "insepi-v14a2-spatiotemporal-prefreeze-receipt-v1":
        raise RuntimeError("unexpected V14a2 prefreeze receipt schema")
    if receipt.get("unlocked_for_first_scientific_sweep") is not True:
        raise RuntimeError("V14a2 receipt does not unlock the first scientific sweep")
    expected = receipt["scientific_file_sha256"]
    actual = {
        "protocol": sha256(protocol_path),
        "generator": sha256(GENERATOR_PATH),
        "sweep_helpers": sha256(HELPER_PATH),
        "runner": sha256(RUNNER_PATH),
    }
    if expected != actual:
        raise RuntimeError(f"V14a2 scientific file hash mismatch: expected={expected}, actual={actual}")
    return receipt


def _coordinates(sweep: dict[str, Any]) -> list[tuple[float, float, float, float, float, float]]:
    values = [
        sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"],
        sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"],
    ]
    return [tuple(float(value) for value in coord) for coord in itertools.product(*values)]


def _rate(bucket: dict[str, float], key: str) -> float:
    return bucket[key] / bucket["n"]


def _rows_for_sweep(
    protocol: dict[str, Any],
    sweep_name: str,
    *,
    smoke_limit: int | None,
) -> tuple[list[dict[str, Any]], int]:
    sweep = protocol[sweep_name]
    coordinates = _coordinates(sweep)
    if smoke_limit is not None:
        if not 1 <= smoke_limit <= 3:
            raise ValueError("--smoke-limit must be in [1,3]")
        coordinates = coordinates[:smoke_limit]

    regimes = [REGIME_BY_NAME[name] for name in sweep["latent_deviation_regimes"]]
    thresholds = _thresholds(protocol)
    aggregate: dict[tuple[float, float, float, float, float, float, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    total_worlds = 0

    for coordinate_index, coords in enumerate(coordinates):
        point = SpatiotemporalPoint(*coords)
        prototypes = prototype_vectors(point)
        for regime_index, regime in enumerate(regimes):
            key = (*coords, regime.value)
            bucket = aggregate[key]
            for replicate in range(int(sweep["replicates_per_coordinate_regime"])):
                seed = replicate_seed(coordinate_index, regime_index, replicate)
                result = interpret_with_prototypes(
                    point,
                    regime,
                    seed=seed,
                    prototypes=prototypes,
                    thresholds=thresholds,
                )
                total_worlds += 1
                bucket["n"] += 1
                bucket["present"] += result.inference is VisitInferenceA2.PRESENT
                bucket["absent"] += result.inference is VisitInferenceA2.ABSENT
                bucket["undetermined"] += result.inference is VisitInferenceA2.UNDETERMINED
                bucket["information_absent"] += result.indeterminacy_reason is IndeterminacyReasonA2.INFORMATION_ABSENT
                bucket["essential_ambiguity"] += result.indeterminacy_reason is IndeterminacyReasonA2.ESSENTIAL_AMBIGUITY
                bucket["model_uncertainty"] += result.indeterminacy_reason is IndeterminacyReasonA2.MODEL_UNCERTAINTY
                bucket["both_supported"] += result.both_supported
                bucket["indirect_rescue"] += result.indirect_rescue
                bucket["target_support"] += result.target_support
                bucket["nuisance_support"] += result.nuisance_support
                bucket["observation_support"] += result.observation_support
                bucket["identifiability_margin"] += result.identifiability_margin

    rows: list[dict[str, Any]] = []
    for key in sorted(aggregate):
        pi1, pi2, pi3, pi4, pi5, pi6, regime = key
        bucket = aggregate[key]
        n = bucket["n"]
        point = SpatiotemporalPoint(pi1, pi2, pi3, pi4, pi5, pi6)
        rows.append(
            {
                "pi1": pi1,
                "pi2": pi2,
                "pi3": pi3,
                "pi4": pi4,
                "pi5": pi5,
                "pi6": pi6,
                "regime": regime,
                "n": int(n),
                "temporally_resolved": int(temporally_resolved(
                    point,
                    minimum_samples=float(protocol["operational_thresholds_prefrozen"]["minimum_samples_per_process_timescale_for_resolved_slice"]),
                    minimum_timescales_per_window=float(protocol["operational_thresholds_prefrozen"]["minimum_process_timescales_per_window_for_resolved_slice"]),
                )),
                "present_rate": _rate(bucket, "present"),
                "absent_rate": _rate(bucket, "absent"),
                "undetermined_rate": _rate(bucket, "undetermined"),
                "information_absence_rate": _rate(bucket, "information_absent"),
                "essential_ambiguity_rate": _rate(bucket, "essential_ambiguity"),
                "model_uncertainty_rate": _rate(bucket, "model_uncertainty"),
                "both_supported_rate": _rate(bucket, "both_supported"),
                "indirect_rescue_rate": _rate(bucket, "indirect_rescue"),
                "mean_target_support": bucket["target_support"] / n,
                "mean_nuisance_support": bucket["nuisance_support"] / n,
                "mean_observation_support": bucket["observation_support"] / n,
                "mean_identifiability_margin": bucket["identifiability_margin"] / n,
            }
        )
    return rows, total_worlds


def _prediction_summary(rows: list[dict[str, Any]], protocol: dict[str, Any], sweep_name: str) -> dict[str, Any]:
    if not rows:
        return {}
    weak_max = max(v for v in protocol[sweep_name]["pi3_values"] if 0 < float(v) < 1)

    if sweep_name == "coarse_sweep":
        min_pi6 = min(float(v) for v in protocol[sweep_name]["pi6_values"])
        max_pi6 = max(float(v) for v in protocol[sweep_name]["pi6_values"])
        low = [r["information_absence_rate"] for r in rows if r["pi6"] == min_pi6]
        high = [r["information_absence_rate"] for r in rows if r["pi6"] == max_pi6]
        return {
            "Q1_low_pi6_information_absence": _mean(low),
            "Q1_high_pi6_information_absence": _mean(high),
            "Q1_sampling_prediction_supported": _mean(low) > _mean(high),
            "note": "descriptive result; never a CI gate",
        }

    mixed = {"target_nuisance_superposed", "target_nuisance_coupled"}
    selected = [
        r for r in rows
        if r["temporally_resolved"] == 1
        and r["regime"] in mixed
        and r["pi3"] <= weak_max + 1e-12
        and r["pi4"] <= weak_max + 1e-12
    ]
    pi2_values = [float(v) for v in protocol[sweep_name]["pi2_values"]]
    pi5_values = [float(v) for v in protocol[sweep_name]["pi5_values"]]
    near_pi2 = 1.0
    shoulder_pi2 = {min(pi2_values), max(pi2_values)}
    matched_pi5 = 1.0
    broad_pi5 = max(pi5_values)

    def amb(*, pi2_mode: str, pi5: float) -> float:
        subset = []
        for row in selected:
            pi2_ok = row["pi2"] == near_pi2 if pi2_mode == "near" else row["pi2"] in shoulder_pi2
            if pi2_ok and row["pi5"] == pi5:
                subset.append(row["essential_ambiguity_rate"])
        return _mean(subset)

    matched_near = amb(pi2_mode="near", pi5=matched_pi5)
    matched_far = amb(pi2_mode="shoulder", pi5=matched_pi5)
    broad_near = amb(pi2_mode="near", pi5=broad_pi5)
    broad_far = amb(pi2_mode="shoulder", pi5=broad_pi5)
    collision_matched = matched_near - matched_far
    collision_broad = broad_near - broad_far
    interaction = collision_matched - collision_broad
    return {
        "Q3_resolved_row_count": len(selected),
        "Q3_matched_spatial_near_pi2_ambiguity": matched_near,
        "Q3_matched_spatial_shoulder_pi2_ambiguity": matched_far,
        "Q3_broad_spatial_near_pi2_ambiguity": broad_near,
        "Q3_broad_spatial_shoulder_pi2_ambiguity": broad_far,
        "Q3_temporal_collision_effect_at_pi5_1": collision_matched,
        "Q3_temporal_collision_effect_at_broad_pi5": collision_broad,
        "Q3_pi2_by_pi5_interaction": interaction,
        "Q3_collision_interaction_supported": collision_matched > 0 and interaction > 0,
        "Q4_reject_timescale_collision_more_strongly_if_false": not (collision_matched > 0 and interaction > 0),
        "note": "descriptive registered contrast; never a CI gate",
    }


def run(
    protocol_path: Path,
    receipt_path: Path,
    output_dir: Path,
    *,
    sweep_name: str,
    smoke_limit: int | None = None,
) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "insepi-v14a2-spatiotemporal-world-protocol-v1":
        raise ValueError("unexpected V14a2 protocol schema")
    if sweep_name not in {"coarse_sweep", "focused_collision_sweep"}:
        raise ValueError("unsupported V14a2 sweep")

    receipt = None
    if smoke_limit is None:
        receipt = _verify_receipt(protocol_path, receipt_path)

    rows, world_count = _rows_for_sweep(protocol, sweep_name, smoke_limit=smoke_limit)
    predictions = _prediction_summary(rows, protocol, sweep_name)
    output_dir.mkdir(parents=True, exist_ok=True)
    surface = output_dir / f"v14a2_{sweep_name}_surface.csv"
    with surface.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.12g}" if isinstance(v, float) else v) for k, v in row.items()})

    summary = {
        "schema": "insepi-v14a2-spatiotemporal-sweep-result-v1",
        "sweep": sweep_name,
        "canonical": smoke_limit is None,
        "world_count": world_count,
        "surface_row_count": len(rows),
        "protocol_sha256": sha256(protocol_path),
        "surface_sha256": sha256(surface),
        "prediction_checks_descriptive_not_gates": predictions,
        "prefreeze_design_commit": None if receipt is None else receipt["design_commit"],
        "claim_boundary": "closed-world phase geometry only; no field accuracy or physical transition claim",
    }
    summary_path = output_dir / f"v14a2_{sweep_name}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--receipt", default=str(DEFAULT_RECEIPT))
    parser.add_argument("--output-dir", default=".v14a2")
    parser.add_argument("--sweep", choices=("coarse_sweep", "focused_collision_sweep"), required=True)
    parser.add_argument("--smoke-limit", type=int)
    args = parser.parse_args()
    summary = run(
        Path(args.protocol),
        Path(args.receipt),
        Path(args.output_dir),
        sweep_name=args.sweep,
        smoke_limit=args.smoke_limit,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
