#!/usr/bin/env python3
"""Verify that supplied V7 evidence is the exact locked V7 prerequisite for V10.

This check is outcome-neutral: V7 PASS and FAIL are both acceptable. The only
question is whether the supplied artifact is a complete, provenance-consistent
execution of the frozen V7 generation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

POLLIPI = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI = "980813bab996909020140fad5bd83b055eb3db9c"
ALLOCATOR = "a8ac75991ab28fd74a3f3a5482304a2b127a97bc"
GENERATOR = "1c4c5ffc214ebdfb71ddabe170a071352acd4879"
EVALUATOR = "6860fa973ce8f25b25028f49723710e8a920709c"
MATERIALIZER = "11f5a7ad97dc71720a5ba0249bf36c6997a4e289"
BASELINE = "94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975"
WORLD_SPEC = "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3"
PYTHON_VERSION = "3.11.16"
NUMPY_VERSION = "2.4.6"
LEDGER_SCHEMA = "pollipi-insepi-v7-execution-ledger-v1"
RUNTIME_SCHEMA = "pollipi-insepi-v7-runtime-environment-v1"
RUNTIME_FREEZE_SCHEMA = "pollipi-insepi-v7-runtime-freeze-v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name}, found {matches}")
    return matches[0]


def require_hex64(value: object, label: str) -> str:
    text = str(value)
    if not HEX64.fullmatch(text):
        raise RuntimeError(f"{label} is not a lowercase 64-hex SHA-256")
    return text


def verify(root: Path) -> dict[str, object]:
    ledger_path = unique(root, "v7_execution_ledger.json")
    report_path = unique(root, "v7_report.json")
    runtime_path = unique(root, "v7_runtime_environment.json")
    pip_path = unique(root, "v7_pip_freeze.txt")
    runtime_freeze_path = unique(root, "v7_runtime_freeze.json")
    materialisation_path = unique(root, "v7_materialisation_receipt.json")
    pollipi_trace_path = unique(root, "pollipi_v7_trace.jsonl")
    insepi_trace_path = unique(root, "insepi_v7_trace.jsonl")

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise RuntimeError("unexpected V7 ledger schema")
    if ledger.get("pollipi_source_commit") != POLLIPI or ledger.get("insepi_source_commit") != INSEPI:
        raise RuntimeError("V7 ledger observer commits differ from frozen V5 commits")
    if ledger.get("allocator_sha") != ALLOCATOR:
        raise RuntimeError("V7 allocator provenance mismatch")
    if ledger.get("generator_sha") != GENERATOR:
        raise RuntimeError("V7 generator provenance mismatch")
    if ledger.get("evaluator_freeze_sha") != EVALUATOR:
        raise RuntimeError("V7 evaluator provenance mismatch")
    if ledger.get("materializer_freeze_sha") != MATERIALIZER:
        raise RuntimeError("V7 materializer provenance mismatch")
    if ledger.get("baseline_registry_sha256") != BASELINE:
        raise RuntimeError("V7 baseline registry mismatch")
    if ledger.get("world_spec_sha256") != WORLD_SPEC:
        raise RuntimeError("V7 world-spec fingerprint mismatch")
    if ledger.get("runtime_python_version") != PYTHON_VERSION:
        raise RuntimeError("V7 runtime Python mismatch")
    if ledger.get("runtime_numpy_version") != NUMPY_VERSION:
        raise RuntimeError("V7 runtime NumPy mismatch")
    if ledger.get("claim_level") not in {"A", "B", "C", "D", "E"}:
        raise RuntimeError("V7 claim level is outside the preregistered ceiling")
    if not isinstance(ledger.get("gate_passed"), bool):
        raise RuntimeError("V7 gate_passed must be boolean")
    if not HEX40.fullmatch(str(ledger.get("orchestrator_sha", ""))):
        raise RuntimeError("V7 orchestrator SHA is invalid")

    hash_bindings = {
        "report_sha256": report_path,
        "runtime_environment_sha256": runtime_path,
        "runtime_pip_freeze_sha256": pip_path,
        "runtime_freeze_sha256": runtime_freeze_path,
        "materialisation_receipt_sha256": materialisation_path,
        "pollipi_trace_sha256": pollipi_trace_path,
        "insepi_trace_sha256": insepi_trace_path,
    }
    for field, path in hash_bindings.items():
        expected = require_hex64(ledger.get(field), field)
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"V7 prerequisite hash mismatch for {field}: {actual} != {expected}")

    require_hex64(ledger.get("pixel_artifact_sha256"), "pixel_artifact_sha256")
    require_hex64(ledger.get("world_fingerprint"), "world_fingerprint")

    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    if runtime.get("schema") != RUNTIME_SCHEMA:
        raise RuntimeError("unexpected V7 runtime-environment schema")
    if runtime.get("python_version") != PYTHON_VERSION or runtime.get("numpy_version") != NUMPY_VERSION:
        raise RuntimeError("V7 runtime file version mismatch")
    if runtime.get("master_seed_derived") is not False:
        raise RuntimeError("V7 runtime manifest was not captured pre-seed")
    if runtime.get("v7_pixels_materialised") is not False:
        raise RuntimeError("V7 runtime manifest was not captured pre-pixels")
    if runtime.get("observer_output_inspected") is not False:
        raise RuntimeError("V7 runtime manifest was not captured pre-output")
    if runtime.get("pip_freeze_sha256") != sha256_file(pip_path):
        raise RuntimeError("V7 runtime pip-freeze binding mismatch")

    runtime_freeze = json.loads(runtime_freeze_path.read_text(encoding="utf-8"))
    if runtime_freeze.get("schema") != RUNTIME_FREEZE_SCHEMA:
        raise RuntimeError("unexpected V7 runtime-freeze schema")
    if runtime_freeze.get("python_version") != PYTHON_VERSION or runtime_freeze.get("numpy_version") != NUMPY_VERSION:
        raise RuntimeError("V7 runtime-freeze version mismatch")

    materialisation = json.loads(materialisation_path.read_text(encoding="utf-8"))
    frozen_inputs = materialisation.get("frozen_inputs")
    if not isinstance(frozen_inputs, dict):
        raise RuntimeError("V7 materialisation receipt lacks frozen_inputs")
    expected_inputs = {
        "pollipi_method_sha": POLLIPI,
        "insepi_method_sha": INSEPI,
        "allocator_sha": ALLOCATOR,
        "generator_sha": GENERATOR,
        "baseline_registry_sha256": BASELINE,
        "world_spec_sha256": WORLD_SPEC,
    }
    for key, expected in expected_inputs.items():
        if frozen_inputs.get(key) != expected:
            raise RuntimeError(f"V7 materialisation frozen input mismatch: {key}")
    if materialisation.get("pixel_artifact_sha256") != ledger.get("pixel_artifact_sha256"):
        raise RuntimeError("V7 materialisation/ledger pixel identity mismatch")
    if materialisation.get("world_fingerprint") != ledger.get("world_fingerprint"):
        raise RuntimeError("V7 materialisation/ledger world identity mismatch")

    return {
        "ledger_path": str(ledger_path),
        "ledger_sha256": sha256_file(ledger_path),
        "claim_level": ledger["claim_level"],
        "gate_passed": ledger["gate_passed"],
        "world_fingerprint": ledger["world_fingerprint"],
        "pixel_artifact_sha256": ledger["pixel_artifact_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("V10_V7_PREREQUISITE PASS")
    print("V7_PRIOR_CLAIM_LEVEL", result["claim_level"])
    print("V7_PRIOR_GATE", "PASS" if result["gate_passed"] else "FAIL")
    print("V7_PRIOR_LEDGER_SHA256", result["ledger_sha256"])


if __name__ == "__main__":
    main()
