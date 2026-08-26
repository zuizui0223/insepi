#!/usr/bin/env python3
"""Run V15c on a committed V15b descriptive result without reopening truth."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.cluster_inference_v15c import (
    evaluate_cluster_family,
    validate_analysis_plan,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v15c_cluster_inference_protocol.json"
DEFAULT_V15B_PROTOCOL = ROOT / "benchmarks/v15b_heldout_measurement_gate_protocol.json"


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    *,
    protocol_path: Path,
    analysis_plan_path: Path,
    v15b_protocol_path: Path,
    measurement_freeze_path: Path,
    v15b_result_path: Path,
    output_path: Path,
) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(
            f"refusing to overwrite retained V15c result: {output_path}"
        )

    # Validate the pre-heldout contracts before opening the post-truth result.
    protocol = _read_json(protocol_path)
    analysis_plan = _read_json(analysis_plan_path)
    v15b_protocol = _read_json(v15b_protocol_path)
    measurement_freeze = _read_json(measurement_freeze_path)
    validate_analysis_plan(
        analysis_plan,
        protocol=protocol,
        v15b_protocol=v15b_protocol,
        measurement_freeze=measurement_freeze,
    )

    descriptive_result = _read_json(v15b_result_path)
    result = evaluate_cluster_family(
        protocol=protocol,
        analysis_plan=analysis_plan,
        v15b_protocol=v15b_protocol,
        measurement_freeze=measurement_freeze,
        descriptive_result=descriptive_result,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--analysis-plan", type=Path, required=True)
    parser.add_argument("--v15b-protocol", type=Path, default=DEFAULT_V15B_PROTOCOL)
    parser.add_argument("--measurement-freeze", type=Path, required=True)
    parser.add_argument("--v15b-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        protocol_path=args.protocol,
        analysis_plan_path=args.analysis_plan,
        v15b_protocol_path=args.v15b_protocol,
        measurement_freeze_path=args.measurement_freeze,
        v15b_result_path=args.v15b_result,
        output_path=args.output,
    )
    print("V15C_FAMILYWISE_STATUS", result["status"])
    print(
        "V15C_HYPOTHESIS_TESTS_EXECUTED",
        result["familywise"]["hypothesis_tests_executed"],
    )
    print("V15C_RAW_TRUTH_REOPENED false")
    print("V15C_RESULT_FILE_SHA256", sha256_file(args.output))


if __name__ == "__main__":
    main()
