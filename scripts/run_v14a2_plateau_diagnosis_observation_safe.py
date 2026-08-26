#!/usr/bin/env python3
"""Corrected observation-safe post-result audit for the V14a2 ambiguity plateau."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from interaction_sensing.evaluation.plateau_diagnosis import (
    OBSERVATION_SAFE_FEATURE_NAMES,
    auc,
    fit_lda,
    observation_safe_vector,
)
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    observation_support,
    route_scores,
    signature_for,
    temporally_resolved,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14a2_plateau_diagnosis_observation_safe_protocol.json"
WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"
REGIME_BY_NAME = {item.value: item for item in LatentRegime}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coordinates(world_protocol: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep = world_protocol["focused_collision_sweep"]
    values = [
        sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"],
        sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"],
    ]
    return [SpatiotemporalPoint(*(float(v) for v in coord)) for coord in itertools.product(*values)]


class Cache:
    def __init__(self) -> None:
        self._cache: dict[tuple[SpatiotemporalPoint, LatentRegime, int], tuple[np.ndarray, float, float]] = {}

    def get(self, point: SpatiotemporalPoint, regime: LatentRegime, seed: int) -> tuple[np.ndarray, float, float]:
        key = (point, regime, seed)
        if key not in self._cache:
            sig = signature_for(point, regime, seed=seed)
            _, _, nuisance = route_scores(sig)
            self._cache[key] = (
                observation_safe_vector(sig),
                float(sig.direct_target_signal_fraction),
                float(nuisance),
            )
        return self._cache[key]


def _matrices(cache: Cache, point: SpatiotemporalPoint, regime: LatentRegime, seeds: list[int]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = [cache.get(point, regime, seed) for seed in seeds]
    return (
        np.stack([row[0] for row in rows], axis=0),
        np.array([row[1] for row in rows], dtype=float),
        np.array([row[2] for row in rows], dtype=float),
    )


def run(protocol_path: Path, output_dir: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "insepi-v14a2-plateau-diagnosis-observation-safe-protocol-v1":
        raise ValueError("unexpected observation-safe plateau protocol schema")
    if tuple(protocol["observation_safe_signature"]["included"]) != OBSERVATION_SAFE_FEATURE_NAMES:
        raise ValueError("protocol and code observation-safe feature sets differ")

    world = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    train = [int(v) for v in protocol["seeds"]["train"]]
    heldout = [int(v) for v in protocol["seeds"]["heldout"]]
    ridge = float(protocol["lda"]["ridge_fraction_of_mean_variance"])
    support_min = float(protocol["coordinate_rules"]["target_observation_support_minimum"])
    frozen = world["operational_thresholds_prefrozen"]
    min_samples = float(frozen["minimum_samples_per_process_timescale_for_resolved_slice"])
    min_timescales = float(frozen["minimum_process_timescales_per_window_for_resolved_slice"])
    nuisance_threshold = float(protocol["nuisance_calibration_comparison"]["frozen_positive_threshold"])

    cache = Cache()
    rows: list[dict[str, Any]] = []
    nuisance_pos_all: list[float] = []
    nuisance_neg_all: list[float] = []

    for point in _coordinates(world):
        if not temporally_resolved(point, minimum_samples=min_samples, minimum_timescales_per_window=min_timescales):
            continue

        _, _, nuisance_pos = _matrices(cache, point, LatentRegime.NUISANCE_ONLY, heldout)
        _, _, nuisance_neg = _matrices(cache, point, LatentRegime.TARGET_ONLY, heldout)
        nuisance_pos_all.extend(nuisance_pos.tolist())
        nuisance_neg_all.extend(nuisance_neg.tolist())

        for comparison in protocol["paired_comparisons"]:
            neg_regime = REGIME_BY_NAME[comparison["negative_regime"]]
            pos_regime = REGIME_BY_NAME[comparison["positive_regime"]]
            coupling_available = pos_regime is LatentRegime.TARGET_NUISANCE_COUPLED
            if observation_support(point, coupling_available=coupling_available) < support_min:
                continue

            x0_train, _, _ = _matrices(cache, point, neg_regime, train)
            x1_train, _, _ = _matrices(cache, point, pos_regime, train)
            x0_test, direct0, _ = _matrices(cache, point, neg_regime, heldout)
            x1_test, direct1, _ = _matrices(cache, point, pos_regime, heldout)
            w = fit_lda(x0_train, x1_train, ridge)
            rows.append({
                "comparison": comparison["name"],
                "pi1": point.pi1, "pi2": point.pi2, "pi3": point.pi3,
                "pi4": point.pi4, "pi5": point.pi5, "pi6": point.pi6,
                "direct_signal_auc": auc(direct1, direct0),
                "observation_safe_lda_auc": auc(x1_test @ w, x0_test @ w),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "v14a2_plateau_observation_safe_coordinates.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (f"{v:.12g}" if isinstance(v, float) else v) for k, v in row.items()})

    diagnostics: dict[str, Any] = {}
    for comparison in [item["name"] for item in protocol["paired_comparisons"]]:
        subset = [row for row in rows if row["comparison"] == comparison]
        direct = np.array([float(row["direct_signal_auc"]) for row in subset], dtype=float)
        safe = np.array([float(row["observation_safe_lda_auc"]) for row in subset], dtype=float)
        median = float(np.median(safe))
        classification = (
            "representation_defect_candidate" if median >= 0.80 else
            "essential_ambiguity_candidate" if median <= 0.60 else
            "mixed_boundary"
        )
        diagnostics[comparison] = {
            "coordinate_count": len(subset),
            "median_direct_signal_auc": float(np.median(direct)),
            "direct_signal_auc_q10": float(np.quantile(direct, 0.10)),
            "direct_signal_auc_q90": float(np.quantile(direct, 0.90)),
            "median_observation_safe_lda_auc": median,
            "observation_safe_lda_auc_q10": float(np.quantile(safe, 0.10)),
            "observation_safe_lda_auc_q90": float(np.quantile(safe, 0.90)),
            "fraction_observation_safe_auc_ge_0_80": float(np.mean(safe >= 0.80)),
            "prefrozen_failure_source_classification": classification,
        }

    nuisance_pos = np.asarray(nuisance_pos_all, dtype=float)
    nuisance_neg = np.asarray(nuisance_neg_all, dtype=float)
    nuisance_auc = auc(nuisance_pos, nuisance_neg)
    nuisance_recall = float(np.mean(nuisance_pos >= nuisance_threshold))
    diagnostics["nuisance_calibration"] = {
        "pooled_nuisance_support_auc": nuisance_auc,
        "recall_at_frozen_0_55_threshold": nuisance_recall,
        "false_positive_rate_at_frozen_0_55_threshold": float(np.mean(nuisance_neg >= nuisance_threshold)),
        "prefrozen_nuisance_scale_mismatch": nuisance_auc >= 0.90 and nuisance_recall < 0.20,
    }

    summary = {
        "schema": "insepi-v14a2-plateau-diagnosis-observation-safe-result-v1",
        "protocol_sha256": sha256(protocol_path),
        "safe_feature_names": list(OBSERVATION_SAFE_FEATURE_NAMES),
        "coordinate_row_count": len(rows),
        "diagnostics": diagnostics,
        "claim_boundary": protocol["claim_boundary"],
    }
    summary_path = output_dir / "v14a2_plateau_observation_safe_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--output-dir", default=".v14a2/plateau_observation_safe")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.protocol), Path(args.output_dir)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
