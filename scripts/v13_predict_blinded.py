#!/usr/bin/env python3
"""Fit V13 development models and emit held-out predictions without heldout truth."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from interaction_sensing.physical_evaluation_v13 import (
    BlockResponse,
    DevelopmentLabel,
    STRATEGIES,
    fit_strategy_models,
    predict_heldout,
    prediction_ledger_sha256,
)

RESPONSE_FIELDS = [
    "block_id", "split",
    "event_restore_delta_evidence", "event_restore_delta_observability",
    "observability_restore_delta_evidence", "observability_restore_delta_observability",
    "shared_restore_delta_evidence", "shared_restore_delta_observability",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_responses(path: Path) -> tuple[BlockResponse, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != RESPONSE_FIELDS:
            raise RuntimeError(f"V13 response table columns changed: {reader.fieldnames}")
        rows = list(reader)
    if len(rows) != 180:
        raise RuntimeError(f"V13 response table must have 180 blocks, got {len(rows)}")
    output = []
    for row in rows:
        response = {
            "event_restore": (
                float(row["event_restore_delta_evidence"]),
                float(row["event_restore_delta_observability"]),
            ),
            "observability_restore": (
                float(row["observability_restore_delta_evidence"]),
                float(row["observability_restore_delta_observability"]),
            ),
            "shared_restore": (
                float(row["shared_restore_delta_evidence"]),
                float(row["shared_restore_delta_observability"]),
            ),
        }
        output.append(BlockResponse(row["block_id"], row["split"], response))
    return tuple(output)


def read_development_labels(path: Path) -> tuple[DevelopmentLabel, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if list(reader.fieldnames or []) != ["block_id", "treatment_class"]:
            raise RuntimeError("V13 development label columns changed")
        rows = list(reader)
    if len(rows) != 108:
        raise RuntimeError(f"V13 development labels must contain 108 blocks, got {len(rows)}")
    return tuple(DevelopmentLabel(row["block_id"], row["treatment_class"]) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--response-receipt", type=Path, required=True)
    parser.add_argument("--development-labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    response_receipt = json.loads(args.response_receipt.read_text(encoding="utf-8"))
    if response_receipt.get("schema") != "interaction-sensing-v13-safe-response-table-v1":
        raise SystemExit("wrong V13 response receipt schema")
    response_sha = sha256_file(args.responses)
    if response_sha != response_receipt.get("safe_block_responses_sha256"):
        raise SystemExit("V13 safe response table differs from trace-summary receipt")

    responses = read_responses(args.responses)
    development = tuple(row for row in responses if row.split == "development")
    heldout = tuple(row for row in responses if row.split == "heldout")
    if len(development) != 108 or len(heldout) != 72:
        raise SystemExit(f"V13 response split mismatch: dev={len(development)} heldout={len(heldout)}")
    labels = read_development_labels(args.development_labels)
    models = fit_strategy_models(development, labels)
    predictions = predict_heldout(models, heldout)
    ledger_sha = prediction_ledger_sha256(predictions)
    payload = {
        "schema": "interaction-sensing-v13-blinded-prediction-ledger-v1",
        "heldout_truth_read": False,
        "safe_response_table_sha256": response_sha,
        "development_labels_sha256": sha256_file(args.development_labels),
        "heldout_block_count": 72,
        "strategies": list(STRATEGIES),
        "prediction_ledger_sha256": ledger_sha,
        "predictions": [
            {
                "block_id": row.block_id,
                "strategy": row.strategy,
                "predicted_class_budget2": row.predicted_class_budget2,
                "predicted_class_after_one": row.predicted_class_after_one,
                "full_battery_prediction": row.full_battery_prediction,
                "intervention_order": list(row.intervention_order),
            }
            for row in predictions
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V13_BLINDED_PREDICTION PASS")
    print("V13_PREDICTION_LEDGER_SHA256", ledger_sha)
    print("V13_PREDICTION_FILE_SHA256", sha256_file(args.output))
    print("V13_HELDOUT_TRUTH_READ false")


if __name__ == "__main__":
    main()
