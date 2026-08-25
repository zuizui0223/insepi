from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "v10_verify_v7_prerequisite",
    ROOT / "scripts/v10_verify_v7_prerequisite.py",
)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> Path:
    evidence = root / "evidence"
    evidence.mkdir()
    pip_path = evidence / "v7_pip_freeze.txt"
    pip_path.write_text("numpy==2.4.6\n", encoding="utf-8")
    runtime_path = evidence / "v7_runtime_environment.json"
    write_json(runtime_path, {
        "schema": verifier.RUNTIME_SCHEMA,
        "python_version": verifier.PYTHON_VERSION,
        "numpy_version": verifier.NUMPY_VERSION,
        "master_seed_derived": False,
        "v7_pixels_materialised": False,
        "observer_output_inspected": False,
        "pip_freeze_sha256": sha(pip_path),
    })
    runtime_freeze_path = evidence / "v7_runtime_freeze.json"
    write_json(runtime_freeze_path, {
        "schema": verifier.RUNTIME_FREEZE_SCHEMA,
        "python_version": verifier.PYTHON_VERSION,
        "numpy_version": verifier.NUMPY_VERSION,
    })
    report_path = evidence / "v7_report.json"
    write_json(report_path, {"schema": "dummy-report"})
    pollipi_path = evidence / "pollipi_v7_trace.jsonl"
    pollipi_path.write_text("pollipi\n", encoding="utf-8")
    insepi_path = evidence / "insepi_v7_trace.jsonl"
    insepi_path.write_text("insepi\n", encoding="utf-8")
    pixel_sha = "a" * 64
    world_fp = "b" * 64
    materialisation_path = evidence / "v7_materialisation_receipt.json"
    write_json(materialisation_path, {
        "frozen_inputs": {
            "pollipi_method_sha": verifier.POLLIPI,
            "insepi_method_sha": verifier.INSEPI,
            "allocator_sha": verifier.ALLOCATOR,
            "generator_sha": verifier.GENERATOR,
            "baseline_registry_sha256": verifier.BASELINE,
            "world_spec_sha256": verifier.WORLD_SPEC,
        },
        "pixel_artifact_sha256": pixel_sha,
        "world_fingerprint": world_fp,
    })
    ledger_path = evidence / "v7_execution_ledger.json"
    ledger = {
        "schema": verifier.LEDGER_SCHEMA,
        "claim_level": "A",
        "gate_passed": True,
        "pollipi_source_commit": verifier.POLLIPI,
        "insepi_source_commit": verifier.INSEPI,
        "allocator_sha": verifier.ALLOCATOR,
        "generator_sha": verifier.GENERATOR,
        "evaluator_freeze_sha": verifier.EVALUATOR,
        "materializer_freeze_sha": verifier.MATERIALIZER,
        "baseline_registry_sha256": verifier.BASELINE,
        "world_spec_sha256": verifier.WORLD_SPEC,
        "runtime_python_version": verifier.PYTHON_VERSION,
        "runtime_numpy_version": verifier.NUMPY_VERSION,
        "orchestrator_sha": "c" * 40,
        "pixel_artifact_sha256": pixel_sha,
        "world_fingerprint": world_fp,
        "report_sha256": sha(report_path),
        "runtime_environment_sha256": sha(runtime_path),
        "runtime_pip_freeze_sha256": sha(pip_path),
        "runtime_freeze_sha256": sha(runtime_freeze_path),
        "materialisation_receipt_sha256": sha(materialisation_path),
        "pollipi_trace_sha256": sha(pollipi_path),
        "insepi_trace_sha256": sha(insepi_path),
    }
    write_json(ledger_path, ledger)
    return evidence


def test_v10_v7_prerequisite_accepts_complete_locked_provenance(tmp_path: Path) -> None:
    evidence = build_fixture(tmp_path)
    result = verifier.verify(evidence)
    assert result["claim_level"] == "A"
    assert result["gate_passed"] is True


def test_v10_v7_prerequisite_rejects_wrong_frozen_generation(tmp_path: Path) -> None:
    evidence = build_fixture(tmp_path)
    ledger_path = evidence / "v7_execution_ledger.json"
    ledger = json.loads(ledger_path.read_text())
    ledger["allocator_sha"] = "0" * 40
    write_json(ledger_path, ledger)
    with pytest.raises(RuntimeError, match="allocator provenance mismatch"):
        verifier.verify(evidence)


def test_v10_v7_prerequisite_rejects_hash_tampering(tmp_path: Path) -> None:
    evidence = build_fixture(tmp_path)
    (evidence / "v7_report.json").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch for report_sha256"):
        verifier.verify(evidence)


def test_v10_v7_prerequisite_is_outcome_neutral(tmp_path: Path) -> None:
    evidence = build_fixture(tmp_path)
    ledger_path = evidence / "v7_execution_ledger.json"
    ledger = json.loads(ledger_path.read_text())
    ledger["claim_level"] = "D"
    ledger["gate_passed"] = False
    write_json(ledger_path, ledger)
    result = verifier.verify(evidence)
    assert result["claim_level"] == "D"
    assert result["gate_passed"] is False
