#!/usr/bin/env python3
"""Evaluate frozen V10 observer traces and emit complete execution provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.simulation.v10_evaluator import evaluate_v10


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha(value: str, label: str) -> str:
    lowered = value.strip().lower()
    if len(lowered) != 40 or any(char not in "0123456789abcdef" for char in lowered):
        raise ValueError(f"{label} must be an exact 40-hex git commit")
    return lowered


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--pollipi-trace", required=True, type=Path)
    parser.add_argument("--insepi-trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--orchestrator-sha", required=True)
    parser.add_argument("--implementation-freeze", required=True, type=Path)
    parser.add_argument("--evaluator-freeze", required=True, type=Path)
    parser.add_argument("--pixel-freeze", required=True, type=Path)
    parser.add_argument("--protocol-freeze", required=True, type=Path)
    parser.add_argument("--v7-ledger", required=True, type=Path)
    args = parser.parse_args()

    orchestrator_sha = require_sha(args.orchestrator_sha, "orchestrator_sha")
    for path in (
        args.implementation_freeze,
        args.evaluator_freeze,
        args.pixel_freeze,
        args.protocol_freeze,
        args.v7_ledger,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    implementation_freeze = json.loads(args.implementation_freeze.read_text(encoding="utf-8"))
    evaluator_freeze = json.loads(args.evaluator_freeze.read_text(encoding="utf-8"))
    pixel_freeze = json.loads(args.pixel_freeze.read_text(encoding="utf-8"))
    protocol_freeze = json.loads(args.protocol_freeze.read_text(encoding="utf-8"))
    v7_ledger = json.loads(args.v7_ledger.read_text(encoding="utf-8"))

    if implementation_freeze.get("schema") != "interaction-sensing-v10-execution-implementation-freeze-v1":
        raise RuntimeError("unexpected V10 implementation-freeze schema")
    if evaluator_freeze.get("schema") != "interaction-sensing-v10-evaluator-freeze-v1":
        raise RuntimeError("unexpected V10 evaluator-freeze schema")
    if pixel_freeze.get("schema") != "interaction-sensing-v10-real-pixel-artifact-freeze-v1":
        raise RuntimeError("unexpected V10 pixel-freeze schema")
    if protocol_freeze.get("schema") != "interaction-sensing-v10-real-video-protocol-freeze-v1":
        raise RuntimeError("unexpected V10 protocol-freeze schema")
    if v7_ledger.get("schema") != "pollipi-insepi-v7-execution-ledger-v1":
        raise RuntimeError("unexpected V7 prerequisite ledger schema")

    report = evaluate_v10(args.artifact_dir, args.pollipi_trace, args.insepi_trace)
    execution_provenance = {
        "orchestrator_sha": orchestrator_sha,
        "implementation_freeze_sha256": sha256_file(args.implementation_freeze),
        "evaluator_freeze_sha256": sha256_file(args.evaluator_freeze),
        "pixel_freeze_sha256": sha256_file(args.pixel_freeze),
        "protocol_freeze_sha256": sha256_file(args.protocol_freeze),
        "v7_prerequisite_ledger_sha256": sha256_file(args.v7_ledger),
        "v7_prerequisite_claim_level": str(v7_ledger["claim_level"]),
        "v7_prerequisite_gate_passed": bool(v7_ledger["gate_passed"]),
    }
    # Execution provenance changes neither the trace-only scientific evaluator nor
    # claim assignment; it is attached before hashing so the final report is a
    # self-identifying evidence object.
    report["execution_provenance"] = execution_provenance

    payload = json_bytes(report)
    report_sha256 = hashlib.sha256(payload).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    receipt = {
        "schema": "interaction-sensing-v10-evaluation-receipt-v1",
        "report_sha256": report_sha256,
        "claim_level": report["claim"]["level"],
        "claim_label": report["claim"]["label"],
        "pollipi_trace_sha256": report["provenance"]["pollipi_trace_sha256"],
        "insepi_trace_sha256": report["provenance"]["insepi_trace_sha256"],
        "pixel_artifact_sha256": report["provenance"]["pixel_artifact_sha256"],
        **execution_provenance,
    }
    args.receipt.write_bytes(json_bytes(receipt))
    print("V10_REPORT_SHA256", report_sha256)
    print("V10_CLAIM_LEVEL", report["claim"]["level"])
    print("V10_CLAIM_LABEL", report["claim"]["label"])
    print("V10_POSITIVE_HIGH_TIER_FAMILIES", report["observer_transfer"]["positive_high_tier_family_count"])
    print("V10_DOSE_MONOTONE_FAMILIES", report["observer_transfer"]["dose_monotone_family_count"])
    print("V10_V6_CELL_PASS_COUNT", report["allocation_transfer"]["v6_cell_pass_count"])
    print("V10_V6_MEAN_PAIRED_UNIFORM_RATIO", report["allocation_transfer"]["v6_overall_mean_paired_uniform_recall_ratio"])
    print("V10_ORCHESTRATOR_SHA", orchestrator_sha)
    print("V10_IMPLEMENTATION_FREEZE_SHA256", execution_provenance["implementation_freeze_sha256"])
    print("V10_V7_PREREQUISITE_LEDGER_SHA256", execution_provenance["v7_prerequisite_ledger_sha256"])


if __name__ == "__main__":
    main()
