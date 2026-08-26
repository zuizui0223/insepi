#!/usr/bin/env python3
"""Post-result V14a2 plateau failure-source audit.

This diagnostic never modifies the locked V14a2 sweep. It asks whether the
observed weak-evidence T+N ambiguity plateau still contains exploitable target or
nuisance information under the already-frozen dimensionless signatures.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

import numpy as np

from interaction_sensing.evaluation.plateau_diagnosis import auc, fit_lda
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    observation_support,
    route_scores,
    signature_for,
    temporally_resolved,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14a2_plateau_diagnosis_protocol.json"
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


class SignatureCache:
    def __init__(self) -> None:
        self._cache: dict[tuple[SpatiotemporalPoint, LatentRegime, int], tuple[np.ndarray, float, float]] = {}

    def get(self, point: SpatiotemporalPoint, regime: LatentRegime, seed: int) -> tuple[np.ndarray, float, float]:
        key = (point, regime, seed)
        if key not in self._cache:
            signature = signature_for(point, regime, seed=seed)
            direct, indirect, nuisance = route_scores(signature)
            self._cache[key] = (signature.vector(), max(direct, indirect), nuisance)
        return self._cache[key]


def _class_matrices(
    cache: SignatureCache,
    point: SpatiotemporalPoint,
    regime: LatentRegime,
    seeds: list[int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = [cache.get(point, regime, seed) for seed in seeds]
    return (
        np.stack([row[0] for row in rows], axis=0),
        np.array([row[1] for row in rows], dtype=float),
        np.array([row[2] for row in rows], dtype=float),
    )


def run(protocol_path: Path, output_dir: Path) -> dict[str, Any]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("schema") != "insepi-v14a2-plateau-diagnosis-protocol-v1":
        raise ValueError("unexpected plateau-diagnosis protocol schema")
    world_protocol = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    train_seeds = [int(v) for v in protocol["seeds"]["train"]]
    heldout_seeds = [int(v) for v in protocol["seeds"]["heldout"]]
    ridge_fraction = float(protocol["lda"]["ridge_fraction_of_mean_variance"])
    support_minimum = float(protocol["coordinate_rules"]["target_observation_support_minimum"])
    frozen = world_protocol["operational_thresholds_prefrozen"]
    minimum_samples = float(frozen["minimum_samples_per_process_timescale_for_resolved_slice"])
    minimum_timescales = float(frozen["minimum_process_timescales_per_window_for_resolved_slice"])
    nuisance_threshold = float(protocol["nuisance_calibration_comparison"]["frozen_positive_threshold"])

    cache = SignatureCache()
    rows: list[dict[str, Any]] = []
    nuisance_pos_all: list[float] = []
    nuisance_neg_all: list[float] = []

    for point in _coordinates(world_protocol):
        if not temporally_resolved(
            point,
            minimum_samples=minimum_samples,
            minimum_timescales_per_window=minimum_timescales,
        ):
            continue

        # Nuisance calibration uses exactly the same Pi coordinate and held-out seeds.
        _, _, nuisance_pos = _class_matrices(cache, point, LatentRegime.NUISANCE_ONLY, heldout_seeds)
        _, _, nuisance_neg = _class_matrices(cache, point, LatentRegime.TARGET_ONLY, heldout_seeds)
        nuisance_pos_all.extend(nuisance_pos.tolist())
        nuisance_neg_all.extend(nuisance_neg.tolist())
        rows.append({
            "comparison": "nuisance_calibration",
            "pi1": point.pi1, "pi2": point.pi2, "pi3": point.pi3,
            "pi4": point.pi4, "pi5": point.pi5, "pi6": point.pi6,
            "target_support_eligible": 1,
            "target_support_auc": float("nan"),
            "full_signature_lda_auc": float("nan"),
            "nuisance_support_auc": auc(nuisance_pos, nuisance_neg),
            "nuisance_threshold_recall": float(np.mean(nuisance_pos >= nuisance_threshold)),
            "nuisance_threshold_false_positive_rate": float(np.mean(nuisance_neg >= nuisance_threshold)),
        })

        for comparison in protocol["paired_comparisons"]:
            neg_regime = REGIME_BY_NAME[comparison["negative_regime"]]
            pos_regime = REGIME_BY_NAME[comparison["positive_regime"]]
            coupling_available = pos_regime is LatentRegime.TARGET_NUISANCE_COUPLED
            if observation_support(point, coupling_available=coupling_available) < support_minimum:
                continue

            x0_train, _, _ = _class_matrices(cache, point, neg_regime, train_seeds)
            x1_train, _, _ = _class_matrices(cache, point, pos_regime, train_seeds)
            x0_test, target0, _ = _class_matrices(cache, point, neg_regime, heldout_seeds)
            x1_test, target1, _ = _class_matrices(cache, point, pos_regime, heldout_seeds)
            w = fit_lda(x0_train, x1_train, ridge_fraction)
            lda0 = x0_test @ w
            lda1 = x1_test @ w
            rows.append({
                "comparison": comparison["name"],
                "pi1": point.pi1, "pi2": point.pi2, "pi3": point.pi3,
                "pi4": point.pi4, "pi5": point.pi5, "pi6": point.pi6,
                "target_support_eligible": 1,
                "target_support_auc": auc(target1, target0),
                "full_signature_lda_auc": auc(lda1, lda0),
                "nuisance_support_auc": float("nan"),
                "nuisance_threshold_recall": float("nan"),
                "nuisance_threshold_false_positive_rate": float("nan"),
            })

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "v14a2_plateau_diagnosis_coordinates.csv"
    fields = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: (f"{value:.12g}" if isinstance(value, float) else value) for key, value in row.items()})

    summaries: dict[str, Any] = {}
    for comparison in [item["name"] for item in protocol["paired_comparisons"]]:
        subset = [row for row in rows if row["comparison"] == comparison]
        target_aucs = np.array([float(row["target_support_auc"]) for row in subset])
        lda_aucs = np.array([float(row["full_signature_lda_auc"]) for row in subset])
        median_lda = float(np.median(lda_aucs))
        if median_lda >= 0.80:
            classification = "representation_defect_candidate"
        elif median_lda <= 0.60:
            classification = "essential_ambiguity_candidate"
        else:
            classification = "mixed_boundary"
        summaries[comparison] = {
            "coordinate_count": len(subset),
            "median_target_support_auc": float(np.median(target_aucs)),
            "target_support_auc_q10": float(np.quantile(target_aucs, 0.10)),
            "target_support_auc_q90": float(np.quantile(target_aucs, 0.90)),
            "median_full_signature_lda_auc": median_lda,
            "full_signature_lda_auc_q10": float(np.quantile(lda_aucs, 0.10)),
            "full_signature_lda_auc_q90": float(np.quantile(lda_aucs, 0.90)),
            "fraction_full_signature_auc_ge_0_80": float(np.mean(lda_aucs >= 0.80)),
            "prefrozen_failure_source_classification": classification,
        }

    nuisance_pos_array = np.asarray(nuisance_pos_all, dtype=float)
    nuisance_neg_array = np.asarray(nuisance_neg_all, dtype=float)
    pooled_nuisance_auc = auc(nuisance_pos_array, nuisance_neg_array)
    pooled_nuisance_recall = float(np.mean(nuisance_pos_array >= nuisance_threshold))
    pooled_nuisance_fpr = float(np.mean(nuisance_neg_array >= nuisance_threshold))
    nuisance_scale_mismatch = pooled_nuisance_auc >= 0.90 and pooled_nuisance_recall < 0.20
    summaries["nuisance_calibration"] = {
        "heldout_positive_worlds": int(len(nuisance_pos_array)),
        "heldout_negative_worlds": int(len(nuisance_neg_array)),
        "pooled_nuisance_support_auc": pooled_nuisance_auc,
        "recall_at_frozen_0_55_threshold": pooled_nuisance_recall,
        "false_positive_rate_at_frozen_0_55_threshold": pooled_nuisance_fpr,
        "prefrozen_nuisance_scale_mismatch": nuisance_scale_mismatch,
    }

    summary = {
        "schema": "insepi-v14a2-plateau-diagnosis-result-v1",
        "protocol_sha256": sha256(protocol_path),
        "locked_v14a2_result_artifact_digest": protocol["source_locked_result"]["artifact_digest"],
        "coordinate_row_count": len(rows),
        "diagnostics": summaries,
        "claim_boundary": protocol["claim_boundary"],
    }
    summary_path = output_dir / "v14a2_plateau_diagnosis_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    parser.add_argument("--output-dir", default=".v14a2/plateau_diagnosis")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.protocol), Path(args.output_dir)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
