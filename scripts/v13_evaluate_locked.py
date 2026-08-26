#!/usr/bin/env python3
"""Evaluate a frozen V13 held-out prediction ledger after private truth unsealing."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from interaction_sensing.physical_evaluation_v13 import (
    HeldoutPrediction,
    HeldoutTruth,
    QcAnnotation,
    evaluate_predictions,
    prediction_ledger_sha256,
)

BLOCK_LOG_REQUIRED_COLUMNS = {
    "block_id", "split", "recording_date_local", "physical_scene_code",
    "operator_code", "device_id", "firmware_version", "lens_id", "mount_id",
    "width", "height", "fps", "exposure_mode", "exposure_us", "analogue_gain",
    "focus_mode", "lens_position", "ambient_light_note", "weather_note",
    "block_complete", "comments",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_predictions(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "interaction-sensing-v13-blinded-prediction-ledger-v1":
        raise RuntimeError("wrong V13 prediction-ledger schema")
    if payload.get("heldout_truth_read") is not False:
        raise RuntimeError("V13 prediction ledger violates blinded truth boundary")
    rows = tuple(
        HeldoutPrediction(
            block_id=row["block_id"],
            strategy=row["strategy"],
            predicted_class_budget2=row["predicted_class_budget2"],
            predicted_class_after_one=row["predicted_class_after_one"],
            full_battery_prediction=row["full_battery_prediction"],
            intervention_order=tuple(row["intervention_order"]),
        )
        for row in payload["predictions"]
    )
    actual = prediction_ledger_sha256(rows)
    if actual != payload.get("prediction_ledger_sha256"):
        raise RuntimeError("V13 prediction ledger content/hash mismatch")
    return payload, rows


def read_class_truth(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != ["block_id", "treatment_class"]:
            raise RuntimeError("V13 heldout class-truth columns changed")
        rows = list(reader)
    if len(rows) != 72:
        raise RuntimeError(f"V13 heldout class truth must contain 72 blocks, got {len(rows)}")
    output = {row["block_id"]: row["treatment_class"] for row in rows}
    if len(output) != 72:
        raise RuntimeError("duplicate heldout class-truth block id")
    return output


def read_validated_physical_clusters(
    block_log: Path,
    capture_validation_receipt: Path,
) -> dict[str, tuple[str, str]]:
    receipt = json.loads(capture_validation_receipt.read_text(encoding="utf-8"))
    if receipt.get("schema") != "interaction-sensing-v13-capture-log-validation-v1":
        raise RuntimeError("wrong V13 capture-validation receipt schema")
    if receipt.get("status") != "PASS" or receipt.get("observer_execution_allowed") is not True:
        raise RuntimeError("V13 capture-validation receipt is not a pre-observer PASS")
    block_log_sha = sha256_file(block_log)
    if block_log_sha != receipt.get("block_log_sha256"):
        raise RuntimeError("V13 block capture log changed after capture validation")
    if receipt.get("development_heldout_dates_disjoint") is not True:
        raise RuntimeError("V13 capture validation did not establish disjoint dates")
    if receipt.get("development_heldout_scenes_disjoint") is not True:
        raise RuntimeError("V13 capture validation did not establish disjoint physical scenes")
    if int(receipt.get("day_x_scene_cluster_count", -1)) != 15:
        raise RuntimeError("V13 capture validation did not establish 15 physical day_x_scene clusters")
    if receipt.get("blocks_per_cluster") != [12]:
        raise RuntimeError("V13 capture validation did not establish 12 blocks per physical cluster")

    with block_log.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or []) != BLOCK_LOG_REQUIRED_COLUMNS:
            raise RuntimeError("V13 block capture-log columns changed")
        rows = list(reader)
    if len(rows) != 180:
        raise RuntimeError("V13 block capture log must contain 180 blocks")
    heldout = {
        row["block_id"]: (row["recording_date_local"], row["physical_scene_code"])
        for row in rows
        if row["split"] == "heldout"
    }
    if len(heldout) != 72:
        raise RuntimeError(f"V13 capture log must contain 72 heldout blocks, got {len(heldout)}")
    if len(set(heldout.values())) != 6:
        raise RuntimeError("V13 heldout capture log must contain exactly six actual physical clusters")
    return heldout


def combine_truth_and_clusters(
    class_truth: dict[str, str],
    physical_clusters: dict[str, tuple[str, str]],
) -> tuple[HeldoutTruth, ...]:
    if set(class_truth) != set(physical_clusters):
        raise RuntimeError("V13 sealed heldout class truth and physical cluster block ids differ")
    return tuple(
        HeldoutTruth(block_id, class_truth[block_id], *physical_clusters[block_id])
        for block_id in sorted(class_truth)
    )


def _parse_yes_no(value: str, field: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"yes", "y", "1", "true"}:
        return True
    if normalized in {"no", "n", "0", "false"}:
        return False
    raise RuntimeError(f"V13 QC field {field} must be explicit yes/no, got {value!r}")


def read_qc_annotations(qc_plan: Path, annotations: Path, commitment: dict[str, object]) -> tuple[QcAnnotation, ...]:
    if sha256_file(qc_plan) != commitment.get("protected_qc_plan_sha256"):
        raise RuntimeError("V13 QC plan differs from pre-field commitment")
    with qc_plan.open(newline="", encoding="utf-8") as handle:
        planned = list(csv.DictReader(handle))
    selected = {row["block_id"] for row in planned if row["protected_qc"] == "1"}
    with annotations.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = [
            "block_id", "split",
            "local_event_reference_present_as_planned",
            "nuisance_treatment_present_as_planned",
            "shared_optical_treatment_present_as_planned",
            "gross_protocol_violation",
            "annotator_code", "notes",
        ]
        if list(reader.fieldnames or []) != required:
            raise RuntimeError("V13 QC annotation columns changed")
        rows = list(reader)
    if {row["block_id"] for row in rows} != selected or len(rows) != len(selected):
        raise RuntimeError("V13 QC annotations do not cover exactly the protected-QC block set")
    output = []
    for row in rows:
        _parse_yes_no(row["local_event_reference_present_as_planned"], "local_event_reference_present_as_planned")
        _parse_yes_no(row["nuisance_treatment_present_as_planned"], "nuisance_treatment_present_as_planned")
        _parse_yes_no(row["shared_optical_treatment_present_as_planned"], "shared_optical_treatment_present_as_planned")
        gross = _parse_yes_no(row["gross_protocol_violation"], "gross_protocol_violation")
        output.append(QcAnnotation(row["block_id"], protected_qc=True, gross_protocol_violation=gross))
    return tuple(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--prediction-commitment", type=Path, required=True)
    parser.add_argument("--heldout-truth", type=Path, required=True)
    parser.add_argument("--truth-split-receipt", type=Path, required=True)
    parser.add_argument("--block-capture-log", type=Path, required=True)
    parser.add_argument("--capture-validation-receipt", type=Path, required=True)
    parser.add_argument("--randomisation-commitment", type=Path, required=True)
    parser.add_argument("--qc-plan", type=Path, required=True)
    parser.add_argument("--qc-annotations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prediction_commitment = json.loads(args.prediction_commitment.read_text(encoding="utf-8"))
    if prediction_commitment.get("schema") != "interaction-sensing-v13-prediction-commitment-v1":
        raise SystemExit("wrong V13 prediction commitment schema")
    prediction_file_sha = sha256_file(args.predictions)
    if prediction_file_sha != prediction_commitment.get("prediction_file_sha256"):
        raise SystemExit("V13 prediction file changed after prediction commitment")

    prediction_payload, predictions = read_predictions(args.predictions)
    if prediction_payload["prediction_ledger_sha256"] != prediction_commitment.get("prediction_ledger_sha256"):
        raise SystemExit("V13 prediction-ledger SHA differs from pre-unseal commitment")

    truth_receipt = json.loads(args.truth_split_receipt.read_text(encoding="utf-8"))
    if truth_receipt.get("schema") != "interaction-sensing-v13-private-truth-split-v1":
        raise SystemExit("wrong V13 truth-split receipt schema")
    heldout_truth_sha = sha256_file(args.heldout_truth)
    if heldout_truth_sha != truth_receipt.get("heldout_truth_sha256"):
        raise SystemExit("V13 heldout truth differs from sealed truth-split receipt")
    if truth_receipt.get("synthetic_randomisation_day_scene_slots_used_for_final_cluster_inference") is not False:
        raise SystemExit("V13 truth-split receipt does not require actual physical capture clusters")
    class_truth = read_class_truth(args.heldout_truth)
    physical_clusters = read_validated_physical_clusters(
        args.block_capture_log,
        args.capture_validation_receipt,
    )
    truth = combine_truth_and_clusters(class_truth, physical_clusters)

    randomisation_commitment = json.loads(args.randomisation_commitment.read_text(encoding="utf-8"))
    qc = read_qc_annotations(args.qc_plan, args.qc_annotations, randomisation_commitment)

    report = evaluate_predictions(predictions, truth, qc)
    report["provenance"] = {
        "prediction_file_sha256": prediction_file_sha,
        "prediction_ledger_sha256": prediction_payload["prediction_ledger_sha256"],
        "prediction_commitment_sha256": sha256_file(args.prediction_commitment),
        "heldout_truth_sha256": heldout_truth_sha,
        "truth_split_receipt_sha256": sha256_file(args.truth_split_receipt),
        "block_capture_log_sha256": sha256_file(args.block_capture_log),
        "capture_validation_receipt_sha256": sha256_file(args.capture_validation_receipt),
        "cluster_identity_source": "validated completed capture log",
        "randomisation_commitment_sha256": sha256_file(args.randomisation_commitment),
        "qc_plan_sha256": sha256_file(args.qc_plan),
        "qc_annotations_sha256": sha256_file(args.qc_annotations),
        "truth_join_stage": "after blinded prediction ledger commitment",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V13_LOCKED_EVALUATION", report["claim"]["level"], report["claim"]["label"])
    print("V13_PREDICTION_LEDGER_SHA256", report["prediction_ledger_sha256"])
    print("V13_REPORT_SHA256", sha256_file(args.output))


if __name__ == "__main__":
    main()
