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


def read_truth(path: Path) -> tuple[HeldoutTruth, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != ["block_id", "treatment_class", "day_id", "scene_id"]:
            raise RuntimeError("V13 heldout truth columns changed")
        rows = list(reader)
    if len(rows) != 72:
        raise RuntimeError(f"V13 heldout truth must contain 72 blocks, got {len(rows)}")
    return tuple(
        HeldoutTruth(row["block_id"], row["treatment_class"], row["day_id"], row["scene_id"])
        for row in rows
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
        # Require all three compliance questions to be explicit. They are retained
        # as annotation evidence even though the frozen scientific gate uses only
        # gross_protocol_violation as the hard invalidation criterion.
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
    truth = read_truth(args.heldout_truth)

    randomisation_commitment = json.loads(args.randomisation_commitment.read_text(encoding="utf-8"))
    qc = read_qc_annotations(args.qc_plan, args.qc_annotations, randomisation_commitment)

    report = evaluate_predictions(predictions, truth, qc)
    report["provenance"] = {
        "prediction_file_sha256": prediction_file_sha,
        "prediction_ledger_sha256": prediction_payload["prediction_ledger_sha256"],
        "prediction_commitment_sha256": sha256_file(args.prediction_commitment),
        "heldout_truth_sha256": heldout_truth_sha,
        "truth_split_receipt_sha256": sha256_file(args.truth_split_receipt),
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
