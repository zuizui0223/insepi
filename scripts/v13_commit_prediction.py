#!/usr/bin/env python3
"""Create a portable hash commitment for a blinded V13 prediction ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.predictions.read_text(encoding="utf-8"))
    if payload.get("schema") != "interaction-sensing-v13-blinded-prediction-ledger-v1":
        raise SystemExit("wrong V13 prediction schema")
    if payload.get("heldout_truth_read") is not False:
        raise SystemExit("cannot commit a prediction ledger that reports heldout truth access")
    commitment = {
        "schema": "interaction-sensing-v13-prediction-commitment-v1",
        "status": "must-be-preserved-before-heldout-truth-unseal",
        "prediction_file_sha256": sha256_file(args.predictions),
        "prediction_ledger_sha256": payload["prediction_ledger_sha256"],
        "safe_response_table_sha256": payload["safe_response_table_sha256"],
        "development_labels_sha256": payload["development_labels_sha256"],
        "heldout_block_count": payload["heldout_block_count"],
        "heldout_truth_read": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(commitment, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V13_PREDICTION_COMMITMENT PASS")
    print("V13_PREDICTION_FILE_SHA256", commitment["prediction_file_sha256"])
    print("V13_PREDICTION_LEDGER_SHA256", commitment["prediction_ledger_sha256"])
    print("V13_COMMITMENT_FILE_SHA256", sha256_file(args.output))


if __name__ == "__main__":
    main()
