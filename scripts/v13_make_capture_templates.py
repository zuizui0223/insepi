#!/usr/bin/env python3
"""Generate observer-safe V13 block and phase capture-log templates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_plan(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 720:
        raise RuntimeError("V13 observer plan must contain 720 phase rows")
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observer-plan", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    commitment = json.loads(args.commitment.read_text(encoding="utf-8"))
    if sha256_file(args.observer_plan) != commitment.get("observer_plan_sha256"):
        raise SystemExit("V13 observer plan differs from commitment")
    rows = read_plan(args.observer_plan)
    by_block: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_block.setdefault(row["opaque_block_id"], []).append(row)
    if len(by_block) != 180:
        raise SystemExit("V13 observer plan must contain 180 opaque blocks")

    block_fields = [
        "block_id", "split", "recording_date_local", "physical_scene_code", "operator_code",
        "device_id", "firmware_version", "lens_id", "mount_id",
        "width", "height", "fps", "exposure_mode", "exposure_us",
        "analogue_gain", "focus_mode", "lens_position",
        "ambient_light_note", "weather_note", "block_complete", "comments",
    ]
    block_rows = []
    for block_id, phases in sorted(by_block.items()):
        splits = {row["split"] for row in phases}
        if len(splits) != 1:
            raise RuntimeError(f"V13 split differs within block {block_id}")
        block_rows.append({
            "block_id": block_id,
            "split": next(iter(splits)),
            "recording_date_local": "",
            "physical_scene_code": "",
            "operator_code": "",
            "device_id": "",
            "firmware_version": "",
            "lens_id": "",
            "mount_id": "",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "exposure_mode": "",
            "exposure_us": "",
            "analogue_gain": "",
            "focus_mode": "",
            "lens_position": "",
            "ambient_light_note": "",
            "weather_note": "",
            "block_complete": "",
            "comments": "",
        })

    phase_fields = [
        "block_id", "split", "phase_order", "phase_name", "clip_key",
        "start_time_local", "end_time_local",
        "washout_completed_before_phase", "latent_baseline_restored_before_phase",
        "camera_settings_changed_within_block", "operator_protocol_deviation", "notes",
    ]
    phase_rows = []
    for row in rows:
        order = int(row["phase_order"])
        phase_rows.append({
            "block_id": row["opaque_block_id"],
            "split": row["split"],
            "phase_order": order,
            "phase_name": row["phase_name"],
            "clip_key": row["clip_key"],
            "start_time_local": "",
            "end_time_local": "",
            "washout_completed_before_phase": "na" if order == 0 else "",
            "latent_baseline_restored_before_phase": "na" if order == 0 else "",
            "camera_settings_changed_within_block": "",
            "operator_protocol_deviation": "",
            "notes": "",
        })

    args.output_dir.mkdir(parents=True, exist_ok=True)
    block_path = args.output_dir / "v13_block_capture_log.csv"
    phase_path = args.output_dir / "v13_phase_capture_log.csv"
    receipt_path = args.output_dir / "v13_capture_template_receipt.json"
    write_csv(block_path, block_fields, block_rows)
    write_csv(phase_path, phase_fields, phase_rows)
    receipt = {
        "schema": "interaction-sensing-v13-capture-template-v1",
        "observer_plan_sha256": sha256_file(args.observer_plan),
        "block_capture_template_sha256": sha256_file(block_path),
        "phase_capture_template_sha256": sha256_file(phase_path),
        "block_count": 180,
        "phase_count": 720,
        "truth_metadata_present": False,
    }
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
