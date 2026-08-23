#!/usr/bin/env python3
"""Validate that a locked V7 evidence pair is eligible for publication transform.

This is stricter than the historical downstream formatter. A valid scientific V7
execution has claim level A-D. Runtime/provenance/truth-boundary failures are
invalid executions and must never be converted into a manuscript claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

LEDGER_SCHEMA = "pollipi-insepi-v7-execution-ledger-v1"
REPORT_SCHEMA = "pollipi-insepi-v7-report-v1"
VALID_CLAIMS = {"A", "B", "C", "D"}

POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"
ALLOCATOR_SHA = "a8ac75991ab28fd74a3f3a5482304a2b127a97bc"
GENERATOR_SHA = "1c4c5ffc214ebdfb71ddabe170a071352acd4879"
EVALUATOR_SHA = "6860fa973ce8f25b25028f49723710e8a920709c"
MATERIALIZER_SHA = "11f5a7ad97dc71720a5ba0249bf36c6997a4e289"
WORLD_SPEC_SHA256 = "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3"
BASELINE_SHA256 = "94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975"
PYTHON_VERSION = "3.11.16"
NUMPY_VERSION = "2.4.6"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_hex(value: object, length: int, label: str) -> str:
    text = str(value or "").lower()
    if len(text) != length or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"invalid {label}: {value!r}")
    return text


def validate(ledger_path: Path, report_path: Path) -> tuple[dict[str, object], dict[str, object]]:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise ValueError("unexpected V7 execution-ledger schema")
    if report.get("schema") != REPORT_SCHEMA:
        raise ValueError("unexpected V7 report schema")
    if ledger.get("report_sha256") != sha256_file(report_path):
        raise ValueError("V7 report hash differs from locked ledger")

    claim = str(ledger.get("claim_level", ""))
    if claim not in VALID_CLAIMS:
        raise ValueError(
            f"V7 publication transform requires a valid A-D scientific claim; got {claim!r}"
        )
    if report.get("claim_level") != claim:
        raise ValueError("V7 report and ledger claim levels differ")

    gate = report.get("gate")
    if not isinstance(gate, Mapping):
        raise ValueError("V7 report is missing gate")
    passed = bool(gate.get("passed"))
    if bool(ledger.get("gate_passed")) != passed:
        raise ValueError("V7 gate status differs between ledger and report")
    if (claim == "A") != passed:
        raise ValueError("valid V7 claim A must correspond exactly to a passing hard gate")

    exact = {
        "pollipi_source_commit": POLLIPI_COMMIT,
        "insepi_source_commit": INSEPI_COMMIT,
        "allocator_sha": ALLOCATOR_SHA,
        "generator_sha": GENERATOR_SHA,
        "evaluator_freeze_sha": EVALUATOR_SHA,
        "materializer_freeze_sha": MATERIALIZER_SHA,
        "world_spec_sha256": WORLD_SPEC_SHA256,
        "baseline_registry_sha256": BASELINE_SHA256,
        "runtime_python_version": PYTHON_VERSION,
        "runtime_numpy_version": NUMPY_VERSION,
    }
    provenance = report.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("V7 report is missing provenance")
    for key, expected in exact.items():
        if str(ledger.get(key, "")) != expected:
            raise ValueError(f"V7 ledger provenance mismatch for {key}")
        if str(provenance.get(key, "")) != expected:
            raise ValueError(f"V7 report provenance mismatch for {key}")

    for key in (
        "materialisation_receipt_sha256",
        "pollipi_trace_sha256",
        "insepi_trace_sha256",
        "pixel_artifact_sha256",
        "runtime_environment_sha256",
        "runtime_pip_freeze_sha256",
        "runtime_freeze_sha256",
    ):
        ledger_value = _require_hex(ledger.get(key), 64, key)
        report_value = _require_hex(provenance.get(key), 64, f"report.{key}")
        if ledger_value != report_value:
            raise ValueError(f"V7 report/ledger provenance mismatch for {key}")

    _require_hex(ledger.get("orchestrator_sha"), 40, "orchestrator_sha")
    if str(provenance.get("orchestrator_sha", "")) != str(ledger["orchestrator_sha"]):
        raise ValueError("V7 report/ledger orchestrator SHA differs")

    failures = [str(item) for item in ledger.get("gate_failures", [])]
    report_failures = [str(item) for item in gate.get("failures", [])]
    if failures != report_failures:
        raise ValueError("V7 report/ledger failure lists differ")

    return dict(ledger), dict(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    ledger, _report = validate(args.ledger, args.report)
    print("MEE_V7_PUBLICATION_EVIDENCE PASS")
    print("MEE_V7_PUBLICATION_CLAIM_LEVEL", ledger["claim_level"])
    print("MEE_V7_PUBLICATION_GATE", "PASS" if ledger["gate_passed"] else "FAIL")
    print("MEE_V7_PUBLICATION_RUNTIME", ledger["runtime_python_version"], ledger["runtime_numpy_version"])


if __name__ == "__main__":
    main()
