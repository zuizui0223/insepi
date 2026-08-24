#!/usr/bin/env python3
"""Split the private V13 truth ledger into training labels and sealed heldout truth.

Run this in the field-operator/private environment.  Only the development-label
file is transferred to the blinded prediction environment before heldout
predictions are frozen.  The heldout truth file remains sealed until then.
"""
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


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def split(private_truth: Path, commitment_path: Path, output_dir: Path) -> dict[str, object]:
    commitment = json.loads(commitment_path.read_text(encoding="utf-8"))
    if commitment.get("schema") != "interaction-sensing-v13-randomisation-commitment-v1":
        raise RuntimeError("wrong V13 commitment schema")
    actual = sha256_file(private_truth)
    if actual != commitment.get("private_truth_ledger_sha256"):
        raise RuntimeError("private truth ledger differs from pre-field commitment")

    with private_truth.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if len(rows) != 180:
        raise RuntimeError("V13 private truth ledger must contain 180 blocks")

    development = [
        {"block_id": row["block_id"], "treatment_class": row["treatment_class"]}
        for row in rows
        if row["split"] == "development"
    ]
    heldout = [
        {
            "block_id": row["block_id"],
            "treatment_class": row["treatment_class"],
            "day_id": row["day_id"],
            "scene_id": row["scene_id"],
        }
        for row in rows
        if row["split"] == "heldout"
    ]
    if len(development) != 108 or len(heldout) != 72:
        raise RuntimeError("V13 truth split cardinality mismatch")
    development.sort(key=lambda row: row["block_id"])
    heldout.sort(key=lambda row: row["block_id"])

    output_dir.mkdir(parents=True, exist_ok=True)
    development_path = output_dir / "v13_development_labels.csv"
    heldout_path = output_dir / "v13_heldout_truth_SEALED.csv"
    write_csv(development_path, ["block_id", "treatment_class"], development)
    write_csv(heldout_path, ["block_id", "treatment_class", "day_id", "scene_id"], heldout)
    receipt = {
        "schema": "interaction-sensing-v13-private-truth-split-v1",
        "status": "heldout-truth-must-remain-sealed-until-prediction-ledger-frozen",
        "source_private_truth_sha256": actual,
        "development_labels_sha256": sha256_file(development_path),
        "heldout_truth_sha256": sha256_file(heldout_path),
        "development_label_count": len(development),
        "heldout_truth_count": len(heldout),
        "transfer_to_blinded_prediction_environment_before_prediction": [
            "v13_development_labels.csv"
        ],
        "forbidden_before_prediction_ledger_freeze": [
            "v13_heldout_truth_SEALED.csv"
        ],
    }
    receipt_path = output_dir / "v13_truth_split_receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-truth", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = split(args.private_truth, args.commitment, args.output_dir)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
