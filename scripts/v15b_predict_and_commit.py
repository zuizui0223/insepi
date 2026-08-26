#!/usr/bin/env python3
"""Emit V15b blinded predictions and their pre-unseal commitment."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.heldout_measurement_v15b import (
    build_blinded_prediction_ledger,
    build_prediction_commitment,
)

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


def _write_new(path: Path, value: dict[str, object]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite retained V15b artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def run(
    *,
    protocol_path: Path,
    measurement_freeze_path: Path,
    component_ledger_path: Path,
    truth_seal_receipt_path: Path,
    prediction_output_path: Path,
    commitment_output_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    if prediction_output_path.exists() or commitment_output_path.exists():
        raise FileExistsError(
            "refusing to overwrite retained V15b prediction artifacts"
        )
    prediction = build_blinded_prediction_ledger(
        protocol=_read_json(protocol_path),
        measurement_freeze=_read_json(measurement_freeze_path),
        component_ledger=_read_json(component_ledger_path),
        component_ledger_file_sha256=sha256_file(component_ledger_path),
        truth_seal_receipt=_read_json(truth_seal_receipt_path),
    )
    commitment = build_prediction_commitment(prediction)
    _write_new(prediction_output_path, prediction)
    _write_new(commitment_output_path, commitment)
    return prediction, commitment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--measurement-freeze", type=Path, required=True)
    parser.add_argument("--component-ledger", type=Path, required=True)
    parser.add_argument("--truth-seal-receipt", type=Path, required=True)
    parser.add_argument("--prediction-output", type=Path, required=True)
    parser.add_argument("--commitment-output", type=Path, required=True)
    args = parser.parse_args()
    prediction, commitment = run(
        protocol_path=args.protocol,
        measurement_freeze_path=args.measurement_freeze,
        component_ledger_path=args.component_ledger,
        truth_seal_receipt_path=args.truth_seal_receipt,
        prediction_output_path=args.prediction_output,
        commitment_output_path=args.commitment_output,
    )
    print("V15B_BLINDED_PREDICTION_COMMITMENT PASS")
    print("V15B_HELDOUT_TRUTH_READ false")
    print(
        "V15B_PREDICTION_LEDGER_CANONICAL_SHA256",
        commitment["prediction_ledger_canonical_sha256"],
    )
    print("V15B_WINDOW_COUNT", prediction["window_count"])


if __name__ == "__main__":
    main()
