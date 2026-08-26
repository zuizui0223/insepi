#!/usr/bin/env python3
"""Open V15b layered truth only after validating prediction commitment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.heldout_measurement_v15b import (
    evaluate_committed_predictions,
    validate_measurement_freeze,
    validate_prediction_commitment,
    validate_truth_seal_receipt,
)
from interaction_sensing.prefield_programming_closeout import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v15b_heldout_measurement_gate_protocol.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return value


def run(
    *,
    protocol_path: Path,
    measurement_freeze_path: Path,
    prediction_path: Path,
    prediction_commitment_path: Path,
    truth_seal_receipt_path: Path,
    truth_bundle_path: Path,
    output_path: Path,
) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(
            f"refusing to overwrite retained V15b result: {output_path}"
        )

    # This entire preflight runs before the truth-bundle contents are opened.
    protocol = _read_json(protocol_path)
    measurement_freeze = _read_json(measurement_freeze_path)
    prediction = _read_json(prediction_path)
    commitment = _read_json(prediction_commitment_path)
    truth_seal = _read_json(truth_seal_receipt_path)
    validate_measurement_freeze(measurement_freeze, protocol)
    validate_prediction_commitment(prediction, commitment)
    validate_truth_seal_receipt(
        truth_seal,
        measurement_freeze_sha256=canonical_json_sha256(measurement_freeze),
    )
    truth_file_sha = sha256_file(truth_bundle_path)
    if truth_file_sha != truth_seal.get("truth_bundle_file_sha256"):
        raise ValueError(
            "truth file differs from seal before truth contents were opened"
        )

    truth_bundle = _read_json(truth_bundle_path)
    result = evaluate_committed_predictions(
        protocol=protocol,
        measurement_freeze=measurement_freeze,
        prediction_ledger=prediction,
        prediction_commitment=commitment,
        truth_seal_receipt=truth_seal,
        truth_bundle=truth_bundle,
        truth_bundle_file_sha256=truth_file_sha,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--measurement-freeze", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--prediction-commitment", type=Path, required=True)
    parser.add_argument("--truth-seal-receipt", type=Path, required=True)
    parser.add_argument("--truth-bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        protocol_path=args.protocol,
        measurement_freeze_path=args.measurement_freeze,
        prediction_path=args.predictions,
        prediction_commitment_path=args.prediction_commitment,
        truth_seal_receipt_path=args.truth_seal_receipt,
        truth_bundle_path=args.truth_bundle,
        output_path=args.output,
    )
    print("V15B_LOCKED_EVALUATION", result["status"])
    print("V15B_FAMILYWISE_HYPOTHESIS_TESTS_EXECUTED 0")
    print("V15B_FIELD_PERFORMANCE_CLAIM false")
    print("V15B_RESULT_FILE_SHA256", sha256_file(args.output))


if __name__ == "__main__":
    main()
