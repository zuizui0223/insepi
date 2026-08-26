#!/usr/bin/env python3
"""Evaluate frozen V7 traces and emit a provenance-locked report/ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from interaction_sensing.simulation.v7_evaluator import (
    INSEPI_TRACE_SCHEMA,
    POLLIPI_TRACE_SCHEMA,
    apply_locked_gate,
    build_report,
    evaluate_v7_traces,
    load_baseline_registry,
    read_trace_jsonl,
)

LEDGER_SCHEMA = "pollipi-insepi-v7-execution-ledger-v1"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _claim_level(gate) -> str:
    if gate.passed:
        return "A"
    failures = tuple(gate.failures)
    if any(item.startswith("arm_removal_strictly_dominates") for item in failures):
        return "D"
    if any(item.startswith("max_tv_above") for item in failures):
        return "D"
    if gate.v6.max_tv <= 0.25 and gate.v6.mean_joint_ratio <= 1.0:
        return "C"
    if gate.v6.max_tv <= 0.25 and gate.v6.mean_joint_ratio > 1.0:
        if any(item.startswith("joint_ratio_below_floor") for item in failures):
            return "B"
        if any(item.startswith("legacy_worst_joint_superior") for item in failures):
            return "B"
    return "D"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--pollipi-trace", required=True, type=Path)
    parser.add_argument("--insepi-trace", required=True, type=Path)
    parser.add_argument("--baseline-registry", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--orchestrator-sha", required=True)
    parser.add_argument("--evaluator-freeze-sha", required=True)
    parser.add_argument("--materializer-freeze-sha", required=True)
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    world_fingerprint = str(receipt["world_fingerprint"])
    pixel_sha = str(receipt["pixel_artifact_sha256"])
    master_seed = str(receipt["master_seed_hex"])

    pollipi_prov, pollipi_rows = read_trace_jsonl(
        args.pollipi_trace,
        expected_schema=POLLIPI_TRACE_SCHEMA,
        expected_world_fingerprint=world_fingerprint,
        expected_pixel_sha256=pixel_sha,
    )
    insepi_prov, insepi_rows = read_trace_jsonl(
        args.insepi_trace,
        expected_schema=INSEPI_TRACE_SCHEMA,
        expected_world_fingerprint=world_fingerprint,
        expected_pixel_sha256=pixel_sha,
    )
    if pollipi_prov["source_commit"] != receipt["frozen_inputs"]["pollipi_method_sha"]:
        raise ValueError("PolliPi trace source commit differs from materialisation receipt")
    if insepi_prov["source_commit"] != receipt["frozen_inputs"]["insepi_method_sha"]:
        raise ValueError("InsePi trace source commit differs from materialisation receipt")

    registry = load_baseline_registry(args.baseline_registry)
    if registry["registry_sha256"] != receipt["frozen_inputs"]["baseline_registry_sha256"]:
        raise ValueError("baseline registry differs from materialisation receipt")

    metrics = evaluate_v7_traces(
        pollipi_rows,
        insepi_rows,
        registry,
        master_seed_hex=master_seed,
        prevalences=(0.1, 0.5, 0.9),
        budgets=(0.1, 0.25, 0.5),
        world_windows=4800,
        replicates=200,
    )
    gate = apply_locked_gate(
        metrics,
        joint_ratio_floor=0.98,
        mean_joint_ratio_strictly_above=1.0,
        max_tv=0.25,
        legacy_tolerance=0.01,
    )
    claim_level = _claim_level(gate)

    provenance = {
        "materialisation_receipt_sha256": _sha256_file(args.receipt),
        "pollipi_trace_sha256": _sha256_file(args.pollipi_trace),
        "insepi_trace_sha256": _sha256_file(args.insepi_trace),
        "pollipi_source_commit": pollipi_prov["source_commit"],
        "insepi_source_commit": insepi_prov["source_commit"],
        "allocator_sha": receipt["frozen_inputs"]["allocator_sha"],
        "generator_sha": receipt["frozen_inputs"]["generator_sha"],
        "baseline_registry_sha256": registry["registry_sha256"],
        "world_spec_sha256": receipt["frozen_inputs"]["world_spec_sha256"],
        "world_fingerprint": world_fingerprint,
        "pixel_artifact_sha256": pixel_sha,
        "orchestrator_sha": args.orchestrator_sha,
        "evaluator_freeze_sha": args.evaluator_freeze_sha,
        "materializer_freeze_sha": args.materializer_freeze_sha,
    }
    report = build_report(metrics=metrics, gate=gate, provenance=provenance)
    report["claim_level"] = claim_level
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    ledger = {
        "schema": LEDGER_SCHEMA,
        "claim_level": claim_level,
        "gate_passed": bool(gate.passed),
        "gate_failures": list(gate.failures),
        "v6_robustness": gate.v6.to_dict(),
        "report_sha256": _sha256_file(args.report),
        **provenance,
    }
    args.ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V7_GATE", "PASS" if gate.passed else "FAIL")
    print("V7_CLAIM_LEVEL", claim_level)
    print("V7_WORST_JOINT", gate.v6.worst_joint_ratio)
    print("V7_MEAN_JOINT", gate.v6.mean_joint_ratio)
    print("V7_MAX_TV", gate.v6.max_tv)
    for failure in gate.failures:
        print("V7_FAILURE", failure)
    print("V7_REPORT_SHA256", ledger["report_sha256"])


if __name__ == "__main__":
    main()
