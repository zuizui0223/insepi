#!/usr/bin/env python3
"""Evaluate frozen V7 traces and emit a provenance-locked report/ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

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
RUNTIME_SCHEMA = "pollipi-insepi-v7-runtime-environment-v1"
RUNTIME_FREEZE_SCHEMA = "pollipi-insepi-v7-runtime-freeze-v1"
EXPECTED_PYTHON = "3.11.16"
EXPECTED_NUMPY = "2.4.6"


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


def _load_runtime(runtime_path: Path, pip_freeze_path: Path, freeze_path: Path):
    for path in (runtime_path, pip_freeze_path, freeze_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if runtime.get("schema") != RUNTIME_SCHEMA:
        raise ValueError("unexpected V7 runtime environment schema")
    if freeze.get("schema") != RUNTIME_FREEZE_SCHEMA:
        raise ValueError("unexpected V7 runtime freeze schema")
    if runtime.get("python_version") != EXPECTED_PYTHON:
        raise ValueError("V7 runtime Python version differs from frozen runtime")
    if runtime.get("numpy_version") != EXPECTED_NUMPY:
        raise ValueError("V7 runtime NumPy version differs from frozen runtime")
    if freeze.get("python_version") != EXPECTED_PYTHON or freeze.get("numpy_version") != EXPECTED_NUMPY:
        raise ValueError("V7 runtime freeze version contract changed")
    if runtime.get("master_seed_derived") is not False:
        raise ValueError("V7 runtime manifest was not captured before seed derivation")
    if runtime.get("v7_pixels_materialised") is not False:
        raise ValueError("V7 runtime manifest was not captured before pixel materialisation")
    if runtime.get("observer_output_inspected") is not False:
        raise ValueError("V7 runtime manifest was not captured before observer output")
    if runtime.get("pip_freeze_sha256") != _sha256_file(pip_freeze_path):
        raise ValueError("V7 pip-freeze bytes differ from runtime manifest")
    return runtime, freeze


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
    parser.add_argument(
        "--runtime-manifest",
        type=Path,
        default=Path(".v7/run/v7_runtime_environment.json"),
    )
    parser.add_argument(
        "--runtime-pip-freeze",
        type=Path,
        default=Path(".v7/run/v7_pip_freeze.txt"),
    )
    parser.add_argument(
        "--runtime-freeze",
        type=Path,
        default=Path("benchmarks/v7_runtime_freeze.json"),
    )
    args = parser.parse_args()

    runtime, _runtime_freeze = _load_runtime(
        args.runtime_manifest,
        args.runtime_pip_freeze,
        args.runtime_freeze,
    )

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
        "runtime_environment_sha256": _sha256_file(args.runtime_manifest),
        "runtime_pip_freeze_sha256": _sha256_file(args.runtime_pip_freeze),
        "runtime_freeze_sha256": _sha256_file(args.runtime_freeze),
        "runtime_python_version": str(runtime["python_version"]),
        "runtime_numpy_version": str(runtime["numpy_version"]),
    }
    report = build_report(metrics=metrics, gate=gate, provenance=provenance)
    report["claim_level"] = claim_level
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
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

    # Keep the exact pre-materialisation runtime contract beside the final V7
    # evidence so the execution remains auditable after workflow environments
    # change. Runtime environment and pip-freeze already live in .v7/run.
    runtime_freeze_copy = args.ledger.parent / "v7_runtime_freeze.json"
    if runtime_freeze_copy.resolve() != args.runtime_freeze.resolve():
        shutil.copyfile(args.runtime_freeze, runtime_freeze_copy)
    if _sha256_file(runtime_freeze_copy) != provenance["runtime_freeze_sha256"]:
        raise ValueError("copied V7 runtime-freeze hash changed")

    print("V7_GATE", "PASS" if gate.passed else "FAIL")
    print("V7_CLAIM_LEVEL", claim_level)
    print("V7_WORST_JOINT", gate.v6.worst_joint_ratio)
    print("V7_MEAN_JOINT", gate.v6.mean_joint_ratio)
    print("V7_MAX_TV", gate.v6.max_tv)
    print("V7_RUNTIME_PYTHON", provenance["runtime_python_version"])
    print("V7_RUNTIME_NUMPY", provenance["runtime_numpy_version"])
    for failure in gate.failures:
        print("V7_FAILURE", failure)
    print("V7_REPORT_SHA256", ledger["report_sha256"])


if __name__ == "__main__":
    main()
