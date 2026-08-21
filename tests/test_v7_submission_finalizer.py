from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
FINALIZER_PATH = ROOT / "scripts" / "finalize_submission_from_v7.py"
SPEC = importlib.util.spec_from_file_location("v7_submission_finalizer", FINALIZER_PATH)
assert SPEC is not None and SPEC.loader is not None
FINALIZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FINALIZER
SPEC.loader.exec_module(FINALIZER)
VerifiedV7 = FINALIZER.VerifiedV7
claim_texts = FINALIZER.claim_texts
verify_v7 = FINALIZER.verify_v7


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _provenance() -> dict[str, str]:
    return {
        "materialisation_receipt_sha256": "1" * 64,
        "pollipi_trace_sha256": "2" * 64,
        "insepi_trace_sha256": "3" * 64,
        "pollipi_source_commit": "a" * 40,
        "insepi_source_commit": "b" * 40,
        "allocator_sha": "c" * 40,
        "generator_sha": "d" * 40,
        "baseline_registry_sha256": "4" * 64,
        "world_spec_sha256": "5" * 64,
        "world_fingerprint": "6" * 64,
        "pixel_artifact_sha256": "7" * 64,
        "orchestrator_sha": "e" * 40,
        "evaluator_freeze_sha": "f" * 40,
        "materializer_freeze_sha": "0" * 40,
    }


def _write_locked_fixture(tmp_path: Path, *, claim_level: str = "A", passed: bool = True) -> tuple[Path, Path]:
    provenance = _provenance()
    metrics = []
    for prevalence in (0.1, 0.5, 0.9):
        for budget in (0.1, 0.25, 0.5):
            base = max(0.05, budget * 0.8)
            metrics.extend(
                [
                    {
                        "prevalence": prevalence,
                        "budget": budget,
                        "policy": "uniform",
                        "true_event_recall": base,
                        "hidden_error_recall": base,
                        "captures_per_hidden_error": 2.0,
                        "disturbance_tv_distance": 0.02,
                    },
                    {
                        "prevalence": prevalence,
                        "budget": budget,
                        "policy": "v6_frozen",
                        "true_event_recall": base * 1.05,
                        "hidden_error_recall": base * 1.04,
                        "captures_per_hidden_error": 1.8,
                        "disturbance_tv_distance": 0.12,
                    },
                ]
            )
    failures = [] if passed else ["joint_ratio_below_floor:p=0.1:b=0.1:0.970000"]
    v6 = {
        "policy": "v6_frozen",
        "worst_joint_ratio": 1.04 if passed else 0.97,
        "mean_joint_ratio": 1.04,
        "max_tv": 0.12,
    }
    gate = {
        "passed": passed,
        "failures": failures,
        "v6": v6,
        "policy_robustness": [
            {"policy": "uniform", "worst_joint_ratio": 1.0, "mean_joint_ratio": 1.0, "max_tv": 0.02},
            v6,
        ],
    }
    report = {
        "schema": "pollipi-insepi-v7-report-v1",
        "provenance": provenance,
        "metrics": metrics,
        "gate": gate,
        "claim_level": claim_level,
        "report_sha256": "8" * 64,
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ledger = {
        "schema": "pollipi-insepi-v7-execution-ledger-v1",
        "claim_level": claim_level,
        "gate_passed": passed,
        "gate_failures": failures,
        "v6_robustness": v6,
        "report_sha256": _sha256(report_path),
        **provenance,
    }
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ledger_path, report_path


def test_locked_fixture_verifies_and_tampering_is_rejected(tmp_path: Path) -> None:
    ledger, report = _write_locked_fixture(tmp_path)
    verified = verify_v7(ledger, report)
    assert verified.claim_level == "A"
    report.write_text(report.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="report file hash"):
        verify_v7(ledger, report)


@pytest.mark.parametrize(
    ("level", "passed", "required_phrase"),
    [
        ("A", True, "passed all preregistered hard rules"),
        ("B", False, "conditional rather than generally robust"),
        ("C", False, "did not establish a general recovery advantage"),
        ("D", False, "rejected a superior-allocation claim"),
    ],
)
def test_claim_level_wording_is_fixed(level: str, passed: bool, required_phrase: str) -> None:
    v7 = VerifiedV7(
        ledger={},
        report={},
        claim_level=level,
        gate_passed=passed,
        failures=() if passed else ("example_failure",),
        worst_joint=1.01 if passed else 0.97,
        mean_joint=1.08 if level != "C" else 0.99,
        max_tv=0.20,
    )
    texts = claim_texts(v7)
    assert required_phrase in texts["abstract"]
    assert f"claim level {level}" in texts["results"]


def test_full_finalizer_fills_all_placeholders_and_renders_figure6(tmp_path: Path) -> None:
    ledger, report = _write_locked_fixture(tmp_path)
    pre_manuscript = tmp_path / "pre.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/build_mee_submission_manuscript.py",
            "--output",
            str(pre_manuscript),
        ],
        cwd=ROOT,
        check=True,
    )
    output_manuscript = tmp_path / "final.md"
    output_supplement = tmp_path / "supp.md"
    fig_svg = tmp_path / "fig6.svg"
    fig_csv = tmp_path / "fig6.csv"
    receipt = tmp_path / "receipt.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/finalize_submission_from_v7.py",
            "--ledger",
            str(ledger),
            "--report",
            str(report),
            "--pre-manuscript",
            str(pre_manuscript),
            "--pre-supplement",
            "manuscript/SUPPLEMENTARY_INFORMATION_PRE_V7.md",
            "--output-manuscript",
            str(output_manuscript),
            "--output-supplement",
            str(output_supplement),
            "--figure-svg",
            str(fig_svg),
            "--figure-csv",
            str(fig_csv),
            "--receipt",
            str(receipt),
        ],
        cwd=ROOT,
        check=True,
    )
    manuscript = output_manuscript.read_text(encoding="utf-8")
    supplement = output_supplement.read_text(encoding="utf-8")
    assert "[[V7_LOCKED_RESULT" not in manuscript
    assert "[[V7_LOCKED_RESULT" not in supplement
    assert "claim level A" in manuscript
    assert "Complete policy metrics" in supplement
    assert fig_svg.exists() and "One-shot locked V7 validation" in fig_svg.read_text(encoding="utf-8")
    assert fig_csv.exists() and len(fig_csv.read_text(encoding="utf-8").splitlines()) == 10
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))
    assert receipt_payload["claim_level"] == "A"
    assert receipt_payload["outputs"]["figure6_svg"]["sha256"] == _sha256(fig_svg)
    # Reviewer-facing final text never exposes exact 40-character source commits.
    assert "a" * 40 not in manuscript
    assert "b" * 40 not in manuscript
