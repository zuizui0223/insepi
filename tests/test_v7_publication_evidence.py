from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts/validate_v7_publication_evidence.py"
    spec = importlib.util.spec_from_file_location("v7_publication_evidence_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_pair(tmp_path: Path, *, claim: str = "B", passed: bool = False):
    module = _load_module()
    h = lambda ch: ch * 64
    provenance = {
        "pollipi_source_commit": module.POLLIPI_COMMIT,
        "insepi_source_commit": module.INSEPI_COMMIT,
        "allocator_sha": module.ALLOCATOR_SHA,
        "generator_sha": module.GENERATOR_SHA,
        "evaluator_freeze_sha": module.EVALUATOR_SHA,
        "materializer_freeze_sha": module.MATERIALIZER_SHA,
        "world_spec_sha256": module.WORLD_SPEC_SHA256,
        "baseline_registry_sha256": module.BASELINE_SHA256,
        "runtime_python_version": module.PYTHON_VERSION,
        "runtime_numpy_version": module.NUMPY_VERSION,
        "materialisation_receipt_sha256": h("1"),
        "pollipi_trace_sha256": h("2"),
        "insepi_trace_sha256": h("3"),
        "pixel_artifact_sha256": h("4"),
        "runtime_environment_sha256": h("5"),
        "runtime_pip_freeze_sha256": h("6"),
        "runtime_freeze_sha256": h("7"),
        "orchestrator_sha": "8" * 40,
    }
    failures = [] if passed else ["joint_ratio_below_floor:p=0.9:b=0.25:0.970000"]
    report = {
        "schema": module.REPORT_SCHEMA,
        "claim_level": claim,
        "gate": {"passed": passed, "failures": failures},
        "provenance": provenance,
    }
    report_path = tmp_path / "v7_report.json"
    report_path.write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
    ledger = {
        "schema": module.LEDGER_SCHEMA,
        "claim_level": claim,
        "gate_passed": passed,
        "gate_failures": failures,
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        **provenance,
    }
    ledger_path = tmp_path / "v7_execution_ledger.json"
    ledger_path.write_text(json.dumps(ledger, sort_keys=True) + "\n", encoding="utf-8")
    return module, ledger_path, report_path


def _rewrite_ledger(ledger_path: Path, **updates) -> None:
    obj = json.loads(ledger_path.read_text())
    obj.update(updates)
    ledger_path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")


def _rewrite_report(report_path: Path, ledger_path: Path, mutate) -> None:
    obj = json.loads(report_path.read_text())
    mutate(obj)
    report_path.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
    _rewrite_ledger(ledger_path, report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest())


def test_publication_gate_accepts_valid_locked_failure_level_B(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="B", passed=False)
    checked, _ = module.validate(ledger, report)
    assert checked["claim_level"] == "B"
    assert checked["gate_passed"] is False


def test_publication_gate_accepts_valid_locked_pass_level_A(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="A", passed=True)
    checked, _ = module.validate(ledger, report)
    assert checked["claim_level"] == "A"
    assert checked["gate_passed"] is True


@pytest.mark.parametrize("claim", ["E", "", "invalid"])
def test_publication_gate_rejects_non_A_to_D_claims(tmp_path: Path, claim: str) -> None:
    module, ledger, report = _write_pair(tmp_path, claim=claim, passed=False)
    with pytest.raises(ValueError, match="valid A-D scientific claim"):
        module.validate(ledger, report)


def test_publication_gate_rejects_stale_runtime(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="B", passed=False)
    _rewrite_ledger(ledger, runtime_numpy_version="2.5.0")
    with pytest.raises(ValueError, match="runtime_numpy_version"):
        module.validate(ledger, report)


def test_publication_gate_rejects_wrong_frozen_observer_commit(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="B", passed=False)
    _rewrite_ledger(ledger, pollipi_source_commit="0" * 40)
    with pytest.raises(ValueError, match="pollipi_source_commit"):
        module.validate(ledger, report)


def test_publication_gate_rejects_report_provenance_drift(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="B", passed=False)
    _rewrite_report(
        report,
        ledger,
        lambda obj: obj["provenance"].update({"runtime_python_version": "3.11.17"}),
    )
    with pytest.raises(ValueError, match="runtime_python_version"):
        module.validate(ledger, report)


def test_publication_gate_rejects_gate_claim_inconsistency(tmp_path: Path) -> None:
    module, ledger, report = _write_pair(tmp_path, claim="B", passed=True)
    with pytest.raises(ValueError, match="claim A"):
        module.validate(ledger, report)
