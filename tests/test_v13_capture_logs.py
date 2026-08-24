from __future__ import annotations

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _load_builder():
    spec = importlib.util.spec_from_file_location("v13_builder_capture_test", ROOT / "scripts/v13_build_randomisation.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(*args: str, check: bool = True):
    return subprocess.run([sys.executable, *args], cwd=ROOT, check=check, capture_output=True, text=True)


def _prepare(tmp_path: Path):
    builder = _load_builder()
    plan_dir = tmp_path / "plan"
    builder.build("de" * 32, plan_dir)
    logs = tmp_path / "logs"
    _run(
        "scripts/v13_make_capture_templates.py",
        "--observer-plan", str(plan_dir / "v13_observer_plan.csv"),
        "--commitment", str(plan_dir / "v13_randomisation_commitment.json"),
        "--output-dir", str(logs),
    )
    return plan_dir, logs


def _complete_logs(plan_dir: Path, logs: Path) -> None:
    with (plan_dir / "v13_private_truth_ledger.csv").open(newline="", encoding="utf-8") as handle:
        truth = {row["block_id"]: row for row in csv.DictReader(handle)}

    block_path = logs / "v13_block_capture_log.csv"
    with block_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or []); rows = list(reader)
    for index, row in enumerate(rows):
        private = truth[row["block_id"]]
        day_num = int(private["day_id"].rsplit("_", 1)[1])
        scene_num = int(private["scene_id"].rsplit("_", 1)[1])
        if row["split"] == "development":
            recording_date = f"2026-09-{day_num:02d}"
            scene_code = f"dev_physical_scene_{scene_num:02d}"
        else:
            recording_date = f"2026-10-{day_num:02d}"
            scene_code = f"held_physical_scene_{scene_num:02d}"
        row.update({
            "recording_date_local": recording_date,
            "physical_scene_code": scene_code,
            "operator_code": "blind-op",
            "device_id": f"pi-{index % 5}",
            "firmware_version": "frozen-test",
            "lens_id": "cam3",
            "mount_id": "fixed-tripod",
            "exposure_mode": "manual",
            "exposure_us": "5000",
            "analogue_gain": "1.0",
            "focus_mode": "manual",
            "lens_position": "2.0",
            "block_complete": "yes",
        })
    with block_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)

    phase_path = logs / "v13_phase_capture_log.csv"
    with phase_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or []); rows = list(reader)
    for row in rows:
        order = int(row["phase_order"])
        row["start_time_local"] = f"12:00:{order * 15:02d}"
        row["end_time_local"] = f"12:00:{order * 15 + 10:02d}"
        row["camera_settings_changed_within_block"] = "no"
        row["operator_protocol_deviation"] = "no"
        if order == 0:
            row["washout_completed_before_phase"] = "na"
            row["latent_baseline_restored_before_phase"] = "na"
        else:
            row["washout_completed_before_phase"] = "yes"
            row["latent_baseline_restored_before_phase"] = "yes"
    with phase_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)


def _validate(plan_dir: Path, logs: Path, check: bool = True):
    return _run(
        "scripts/v13_validate_capture_logs.py",
        "--observer-plan", str(plan_dir / "v13_observer_plan.csv"),
        "--commitment", str(plan_dir / "v13_randomisation_commitment.json"),
        "--block-log", str(logs / "v13_block_capture_log.csv"),
        "--phase-log", str(logs / "v13_phase_capture_log.csv"),
        "--output-receipt", str(logs / "capture_validation.json"),
        check=check,
    )


def test_v13_completed_capture_logs_pass_before_observer_execution(tmp_path: Path) -> None:
    plan, logs = _prepare(tmp_path)
    _complete_logs(plan, logs)
    completed = _validate(plan, logs)
    assert "V13_CAPTURE_LOG_VALIDATION PASS" in completed.stdout


def test_v13_missing_baseline_restoration_fails_before_observer_execution(tmp_path: Path) -> None:
    plan, logs = _prepare(tmp_path)
    _complete_logs(plan, logs)
    path = logs / "v13_phase_capture_log.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or []); rows = list(reader)
    active = next(row for row in rows if row["phase_order"] == "1")
    active["latent_baseline_restored_before_phase"] = "no"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    completed = _validate(plan, logs, check=False)
    assert completed.returncode != 0
    assert "baseline not restored" in (completed.stdout + completed.stderr)


def test_v13_camera_geometry_drift_fails_before_observer_execution(tmp_path: Path) -> None:
    plan, logs = _prepare(tmp_path)
    _complete_logs(plan, logs)
    path = logs / "v13_block_capture_log.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or []); rows = list(reader)
    rows[0]["fps"] = "29"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    completed = _validate(plan, logs, check=False)
    assert completed.returncode != 0
    assert "geometry/FPS" in (completed.stdout + completed.stderr)


def test_v13_heldout_physical_scene_overlap_fails_before_observer_execution(tmp_path: Path) -> None:
    plan, logs = _prepare(tmp_path)
    _complete_logs(plan, logs)
    path = logs / "v13_block_capture_log.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle); fields = list(reader.fieldnames or []); rows = list(reader)
    for row in rows:
        if row["physical_scene_code"] == "held_physical_scene_01":
            row["physical_scene_code"] = "dev_physical_scene_01"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n"); writer.writeheader(); writer.writerows(rows)
    completed = _validate(plan, logs, check=False)
    assert completed.returncode != 0
    assert "overlap" in (completed.stdout + completed.stderr)
