#!/usr/bin/env python3
"""Fail closed on V13 capture-log deviations before observer execution."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

BLOCK_FIELDS = [
    "block_id", "split", "recording_date_local", "physical_scene_code", "operator_code",
    "device_id", "firmware_version", "lens_id", "mount_id",
    "width", "height", "fps", "exposure_mode", "exposure_us",
    "analogue_gain", "focus_mode", "lens_position",
    "ambient_light_note", "weather_note", "block_complete", "comments",
]
PHASE_FIELDS = [
    "block_id", "split", "phase_order", "phase_name", "clip_key",
    "start_time_local", "end_time_local",
    "washout_completed_before_phase", "latent_baseline_restored_before_phase",
    "camera_settings_changed_within_block", "operator_protocol_deviation", "notes",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != fields:
            raise RuntimeError(f"V13 capture log columns changed for {path.name}")
        return list(reader)


def yes(value: str, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"yes", "y", "1", "true"}:
        return True
    if normalized in {"no", "n", "0", "false"}:
        return False
    raise RuntimeError(f"V13 {field} must be explicit yes/no, got {value!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observer-plan", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--block-log", type=Path, required=True)
    parser.add_argument("--phase-log", type=Path, required=True)
    parser.add_argument("--output-receipt", type=Path, required=True)
    args = parser.parse_args()

    commitment = json.loads(args.commitment.read_text(encoding="utf-8"))
    if sha256_file(args.observer_plan) != commitment.get("observer_plan_sha256"):
        raise SystemExit("V13 observer plan differs from pre-field commitment")
    with args.observer_plan.open(newline="", encoding="utf-8") as handle:
        plan = list(csv.DictReader(handle))
    block_rows = read_csv(args.block_log, BLOCK_FIELDS)
    phase_rows = read_csv(args.phase_log, PHASE_FIELDS)
    if len(block_rows) != 180 or len(phase_rows) != 720:
        raise SystemExit("V13 completed capture logs must contain exactly 180 blocks and 720 phases")

    plan_keys = {
        (row["opaque_block_id"], row["split"], int(row["phase_order"]), row["phase_name"], row["clip_key"])
        for row in plan
    }
    phase_keys = {
        (row["block_id"], row["split"], int(row["phase_order"]), row["phase_name"], row["clip_key"])
        for row in phase_rows
    }
    if phase_keys != plan_keys or len(phase_keys) != 720:
        raise SystemExit("V13 completed phase log does not match observer-safe randomisation plan")

    blocks_by_id = {row["block_id"]: row for row in block_rows}
    if len(blocks_by_id) != 180 or set(blocks_by_id) != {row["opaque_block_id"] for row in plan}:
        raise SystemExit("V13 completed block log ids differ from observer plan")
    for block_id, row in blocks_by_id.items():
        if row["split"] not in {"development", "heldout"}:
            raise SystemExit(f"V13 invalid split in block log: {block_id}")
        if (int(row["width"]), int(row["height"]), int(row["fps"])) != (1920, 1080, 30):
            raise SystemExit(f"V13 camera geometry/FPS contract violated: {block_id}")
        required_nonempty = (
            "recording_date_local", "physical_scene_code", "operator_code", "device_id",
            "firmware_version", "lens_id", "mount_id", "exposure_mode", "exposure_us",
            "analogue_gain", "focus_mode", "lens_position",
        )
        empty = [field for field in required_nonempty if not row[field].strip()]
        if empty:
            raise SystemExit(f"V13 missing required block metadata {empty}: {block_id}")
        if not yes(row["block_complete"], "block_complete"):
            raise SystemExit(f"V13 block not marked complete: {block_id}")

    # Physical cluster identity must be demonstrated by completed acquisition
    # metadata, not inferred from synthetic split labels.
    split_dates = {
        split: {row["recording_date_local"] for row in block_rows if row["split"] == split}
        for split in ("development", "heldout")
    }
    split_scenes = {
        split: {row["physical_scene_code"] for row in block_rows if row["split"] == split}
        for split in ("development", "heldout")
    }
    if len(split_dates["development"]) != 3 or len(split_dates["heldout"]) != 2:
        raise SystemExit(f"V13 physical day-count contract violated: {split_dates}")
    if split_dates["development"] & split_dates["heldout"]:
        raise SystemExit("V13 heldout recording dates overlap development dates")
    if len(split_scenes["development"]) != 3 or len(split_scenes["heldout"]) != 3:
        raise SystemExit(f"V13 physical scene-count contract violated: {split_scenes}")
    if split_scenes["development"] & split_scenes["heldout"]:
        raise SystemExit("V13 heldout physical scenes overlap development scenes")

    cluster_counts = Counter(
        (row["split"], row["recording_date_local"], row["physical_scene_code"])
        for row in block_rows
    )
    expected_cluster_count = 3 * 3 + 2 * 3
    if len(cluster_counts) != expected_cluster_count:
        raise SystemExit(f"V13 day_x_scene cluster cardinality changed: {len(cluster_counts)}")
    bad_clusters = {key: count for key, count in cluster_counts.items() if count != 12}
    if bad_clusters:
        raise SystemExit(f"V13 each day_x_scene cluster must contain 12 blocks: {bad_clusters}")

    deviations: list[str] = []
    for row in phase_rows:
        block_id = row["block_id"]
        order = int(row["phase_order"])
        if not row["start_time_local"].strip() or not row["end_time_local"].strip():
            deviations.append(f"missing phase timestamps:{block_id}:p{order}")
        if yes(row["camera_settings_changed_within_block"], "camera_settings_changed_within_block"):
            deviations.append(f"camera settings changed:{block_id}:p{order}")
        if yes(row["operator_protocol_deviation"], "operator_protocol_deviation"):
            deviations.append(f"operator protocol deviation:{block_id}:p{order}")
        if order == 0:
            if row["washout_completed_before_phase"].strip().lower() != "na":
                deviations.append(f"placebo washout must be na:{block_id}")
            if row["latent_baseline_restored_before_phase"].strip().lower() != "na":
                deviations.append(f"placebo baseline-restore must be na:{block_id}")
        else:
            if not yes(row["washout_completed_before_phase"], "washout_completed_before_phase"):
                deviations.append(f"washout incomplete:{block_id}:p{order}")
            if not yes(row["latent_baseline_restored_before_phase"], "latent_baseline_restored_before_phase"):
                deviations.append(f"latent baseline not restored:{block_id}:p{order}")

    receipt = {
        "schema": "interaction-sensing-v13-capture-log-validation-v1",
        "status": "PASS" if not deviations else "FAIL",
        "observer_plan_sha256": sha256_file(args.observer_plan),
        "block_log_sha256": sha256_file(args.block_log),
        "phase_log_sha256": sha256_file(args.phase_log),
        "block_count": 180,
        "phase_count": 720,
        "development_date_count": len(split_dates["development"]),
        "heldout_date_count": len(split_dates["heldout"]),
        "development_physical_scene_count": len(split_scenes["development"]),
        "heldout_physical_scene_count": len(split_scenes["heldout"]),
        "day_x_scene_cluster_count": len(cluster_counts),
        "blocks_per_cluster": sorted(set(cluster_counts.values())),
        "development_heldout_dates_disjoint": True,
        "development_heldout_scenes_disjoint": True,
        "deviations": deviations,
        "observer_execution_allowed": not deviations,
    }
    args.output_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.output_receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if deviations:
        raise SystemExit("V13 capture-log validation FAIL: " + "; ".join(deviations[:10]))
    print("V13_CAPTURE_LOG_VALIDATION PASS", sha256_file(args.output_receipt))


if __name__ == "__main__":
    main()
