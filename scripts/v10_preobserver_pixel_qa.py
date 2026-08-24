#!/usr/bin/env python3
"""Post-freeze descriptive QA for the canonical V10 real-pixel artifact.

This script never imports or runs either observer. It inspects only the already
frozen pixel arrays and registries to document (1) disturbance-panel balance
across source-video/time strata and (2) whether the preregistered perturbations
are non-degenerate at the pixel level. These diagnostics are explicitly not a
V10 claim gate and cannot change the frozen protocol, operators or thresholds.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

PIXEL_SHA256 = "b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66"
CONDITION_SHA256 = "1689f5ce102abfef722e3e8667e8c6e290a42fe1d4563c1655b7f14520cde393"
PANEL_SHA256 = "b1e59cda67977e5ab8d09e1ea28236b442d72c616c92df0c22adca89122cac8a"
FAMILIES = ("shadow", "occlusion", "blur", "sensor_banding", "glare", "framing_drift")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def categorical_tv(base_rows: list[dict[str, object]], indices: list[int], keys: tuple[str, ...]) -> float:
    full = Counter(tuple(row[key] for key in keys) for row in base_rows)
    selected = Counter(tuple(base_rows[index][key] for key in keys) for index in indices)
    return 0.5 * sum(
        abs(selected.get(category, 0) / len(indices) - count / len(base_rows))
        for category, count in full.items()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.artifact_dir
    pixel_path = root / "v10_real_pixel_artifact.npz"
    condition_path = root / "v10_condition_registry.json"
    panel_path = root / "v10_panel_registry.json"
    base_path = root / "v10_base_windows.json"
    variant_path = root / "v10_variant_registry.json"
    for path in (pixel_path, condition_path, panel_path, base_path, variant_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256_file(pixel_path) != PIXEL_SHA256:
        raise RuntimeError("canonical V10 pixel SHA mismatch")
    if sha256_file(condition_path) != CONDITION_SHA256:
        raise RuntimeError("canonical V10 condition-registry SHA mismatch")
    if sha256_file(panel_path) != PANEL_SHA256:
        raise RuntimeError("canonical V10 panel-registry SHA mismatch")

    base = json.loads(base_path.read_text(encoding="utf-8"))
    panels = json.loads(panel_path.read_text(encoding="utf-8"))
    variants = json.loads(variant_path.read_text(encoding="utf-8"))
    if len(base) != 364 or len(panels) != 18 or len(variants) != 19:
        raise RuntimeError("V10 frozen registry cardinality changed")

    full_video = Counter(row["video_index"] for row in base)
    full_vq = Counter((row["video_index"], row["temporal_quartile"]) for row in base)
    panel_rows: list[dict[str, object]] = []
    for panel in panels:
        indices = list(map(int, panel["disturbed_base_indices"]))
        if len(indices) != 182 or len(set(indices)) != 182:
            raise RuntimeError("V10 panel is not the frozen 182/182 assignment")
        video_counts = Counter(base[index]["video_index"] for index in indices)
        vq_counts = Counter((base[index]["video_index"], base[index]["temporal_quartile"]) for index in indices)
        panel_rows.append({
            "panel_id": panel["panel_id"],
            "video_tv": categorical_tv(base, indices, ("video_index",)),
            "video_temporal_quartile_tv": categorical_tv(base, indices, ("video_index", "temporal_quartile")),
            "missing_video_categories": [
                {"video_index": int(key), "full_window_count": int(full_video[key])}
                for key in sorted(full_video)
                if video_counts.get(key, 0) == 0
            ],
            "missing_video_temporal_quartile_categories": [
                {"video_index": int(key[0]), "temporal_quartile": int(key[1]), "full_window_count": int(full_vq[key])}
                for key in sorted(full_vq)
                if vq_counts.get(key, 0) == 0
            ],
            "max_abs_video_count_deviation_from_half": max(
                abs(video_counts.get(key, 0) - full_video[key] / 2) for key in full_video
            ),
            "max_abs_video_quartile_count_deviation_from_half": max(
                abs(vq_counts.get(key, 0) - full_vq[key] / 2) for key in full_vq
            ),
        })

    with np.load(pixel_path, allow_pickle=False) as archive:
        if set(archive.files) != {"backgrounds", "frames"}:
            raise RuntimeError("unexpected V10 NPZ members")
        frames = np.asarray(archive["frames"])
    if frames.shape != (364, 19, 96, 128) or frames.dtype != np.uint8:
        raise RuntimeError("V10 frozen frame tensor changed")

    native = frames[:, 0].astype(np.int16)
    variant_map = {
        (str(row["family"]), int(row["tier_index"])): int(row["variant_index"])
        for row in variants
        if row["family"] is not None
    }
    perturbation_rows: list[dict[str, object]] = []
    monotone: dict[str, bool] = {}
    for family in FAMILIES:
        family_mae: list[float] = []
        for tier in range(3):
            variant_index = variant_map[(family, tier)]
            perturbed_u8 = frames[:, variant_index]
            delta = np.abs(perturbed_u8.astype(np.int16) - native)
            mae = delta.mean(axis=(1, 2))
            saturation = ((perturbed_u8 == 0) | (perturbed_u8 == 255)).mean(axis=(1, 2))
            row = {
                "family": family,
                "tier_index": tier,
                "variant_index": variant_index,
                "median_mae": float(np.median(mae)),
                "min_window_mae": float(np.min(mae)),
                "max_window_mae": float(np.max(mae)),
                "median_fraction_pixels_changed": float(np.median((delta > 0).mean(axis=(1, 2)))),
                "median_fraction_abs_delta_gt5": float(np.median((delta > 5).mean(axis=(1, 2)))),
                "median_fraction_abs_delta_gt20": float(np.median((delta > 20).mean(axis=(1, 2)))),
                "median_saturation_fraction": float(np.median(saturation)),
                "max_window_saturation_fraction": float(np.max(saturation)),
            }
            perturbation_rows.append(row)
            family_mae.append(float(row["median_mae"]))
        monotone[family] = family_mae[0] <= family_mae[1] <= family_mae[2]

    result = {
        "schema": "interaction-sensing-v10-preobserver-pixel-qa-v1",
        "status": "post-freeze-descriptive-only-not-a-v10-claim-gate",
        "observer_execution": False,
        "scientific_protocol_changed": False,
        "canonical_pixel_npz_sha256": PIXEL_SHA256,
        "condition_registry_sha256": CONDITION_SHA256,
        "panel_registry_sha256": PANEL_SHA256,
        "panel_assignment": {
            "panel_count": len(panel_rows),
            "disturbed_per_panel": 182,
            "video_tv_mean": float(np.mean([row["video_tv"] for row in panel_rows])),
            "video_tv_max": float(np.max([row["video_tv"] for row in panel_rows])),
            "video_temporal_quartile_tv_mean": float(np.mean([row["video_temporal_quartile_tv"] for row in panel_rows])),
            "video_temporal_quartile_tv_max": float(np.max([row["video_temporal_quartile_tv"] for row in panel_rows])),
            "panels_with_missing_video_category": sum(bool(row["missing_video_categories"]) for row in panel_rows),
            "panels_with_missing_video_temporal_quartile_category": sum(bool(row["missing_video_temporal_quartile_categories"]) for row in panel_rows),
            "panels": panel_rows,
        },
        "perturbation_pixel_diagnostics": {
            "base_window_count": 364,
            "family_count": 6,
            "tier_count": 3,
            "all_family_median_mae_nondecreasing_by_tier": all(monotone.values()),
            "family_median_mae_nondecreasing_by_tier": monotone,
            "minimum_over_all_variants_of_min_window_mae": float(min(row["min_window_mae"] for row in perturbation_rows)),
            "maximum_over_all_variants_of_max_window_saturation_fraction": float(max(row["max_window_saturation_fraction"] for row in perturbation_rows)),
            "rows": perturbation_rows,
        },
        "interpretation_boundary": [
            "These diagnostics were computed after the V10 protocol and pixel bytes were frozen.",
            "They are descriptive artifact-quality checks only and cannot change perturbations, thresholds, comparators, claim level, or acceptance criteria.",
            "No PolliPi or InsePi observer was run to compute these diagnostics.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V10_PIXEL_QA_VIDEO_TV_MEAN", result["panel_assignment"]["video_tv_mean"])
    print("V10_PIXEL_QA_VIDEO_TV_MAX", result["panel_assignment"]["video_tv_max"])
    print("V10_PIXEL_QA_VIDEO_QUARTILE_TV_MEAN", result["panel_assignment"]["video_temporal_quartile_tv_mean"])
    print("V10_PIXEL_QA_VIDEO_QUARTILE_TV_MAX", result["panel_assignment"]["video_temporal_quartile_tv_max"])
    print("V10_PIXEL_QA_MISSING_VIDEO_CATEGORIES", result["panel_assignment"]["panels_with_missing_video_category"])
    print("V10_PIXEL_QA_MISSING_VIDEO_QUARTILE_CATEGORIES", result["panel_assignment"]["panels_with_missing_video_temporal_quartile_category"])
    print("V10_PIXEL_QA_ALL_FAMILY_MAE_MONOTONE", result["perturbation_pixel_diagnostics"]["all_family_median_mae_nondecreasing_by_tier"])
    print("V10_PIXEL_QA_MIN_WINDOW_MAE", result["perturbation_pixel_diagnostics"]["minimum_over_all_variants_of_min_window_mae"])
    print("V10_PIXEL_QA_MAX_WINDOW_SATURATION", result["perturbation_pixel_diagnostics"]["maximum_over_all_variants_of_max_window_saturation_fraction"])
    print("V10_PIXEL_QA_OBSERVER_EXECUTION false")


if __name__ == "__main__":
    main()
