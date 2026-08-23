#!/usr/bin/env python3
"""Evaluate frozen V10 observer traces without rerunning observers or pixels."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.simulation.v10_evaluator import evaluate_v10


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--pollipi-trace", required=True, type=Path)
    parser.add_argument("--insepi-trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    report = evaluate_v10(args.artifact_dir, args.pollipi_trace, args.insepi_trace)
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
    }
    args.receipt.write_bytes(json_bytes(receipt))
    print("V10_REPORT_SHA256", report_sha256)
    print("V10_CLAIM_LEVEL", report["claim"]["level"])
    print("V10_CLAIM_LABEL", report["claim"]["label"])
    print("V10_POSITIVE_HIGH_TIER_FAMILIES", report["observer_transfer"]["positive_high_tier_family_count"])
    print("V10_DOSE_MONOTONE_FAMILIES", report["observer_transfer"]["dose_monotone_family_count"])
    print("V10_V6_CELL_PASS_COUNT", report["allocation_transfer"]["v6_cell_pass_count"])
    print("V10_V6_MEAN_PAIRED_UNIFORM_RATIO", report["allocation_transfer"]["v6_overall_mean_paired_uniform_recall_ratio"])


if __name__ == "__main__":
    main()
