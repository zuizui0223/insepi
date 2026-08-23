from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def _load_script():
    path = ROOT / "scripts/v7_evaluate_locked.py"
    spec = importlib.util.spec_from_file_location("v7_claim_mapping_test_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gate(*, passed: bool, failures=(), worst=1.0, mean=1.0, tv=0.2):
    return SimpleNamespace(
        passed=passed,
        failures=tuple(failures),
        v6=SimpleNamespace(
            worst_joint_ratio=worst,
            mean_joint_ratio=mean,
            max_tv=tv,
        ),
    )


def test_v7_claim_mapping_freeze_defines_only_valid_scientific_A_to_D() -> None:
    freeze = json.loads((ROOT / "benchmarks/v7_claim_mapping_freeze.json").read_text())
    assert freeze["schema"] == "pollipi-insepi-v7-claim-mapping-v1"
    assert freeze["status"] == "pre-result-frozen"
    assert freeze["valid_scientific_claim_levels"] == ["A", "B", "C", "D"]
    assert freeze["execution_integrity_failure"]["claim_level"] is None
    assert freeze["execution_integrity_failure"]["status"] == "no_valid_v7_claim"


def test_v7_executable_claim_precedence_matches_freeze() -> None:
    module = _load_script()
    cases = [
        (_gate(passed=True, mean=1.01, tv=0.2), "A"),
        (_gate(passed=False, failures=("arm_removal_strictly_dominates:v6_no_pollipi",), mean=1.1, tv=0.2), "D"),
        (_gate(passed=False, failures=("max_tv_above_0.25:0.300000",), mean=1.1, tv=0.3), "D"),
        (_gate(passed=False, failures=("mean_joint_ratio_not_above_1.0",), mean=0.99, tv=0.2), "C"),
        (_gate(passed=False, failures=("joint_ratio_below_floor:p=0.9:b=0.25:0.970000",), mean=1.02, tv=0.2), "B"),
        (_gate(passed=False, failures=("legacy_worst_joint_superior:insepi_audit",), mean=1.02, tv=0.2), "B"),
        (_gate(passed=False, failures=("unexpected_but_valid_scientific_failure",), mean=1.02, tv=0.2), "D"),
    ]
    for gate, expected in cases:
        assert module._claim_level(gate) == expected


def test_v7_executable_claim_mapper_can_never_emit_E() -> None:
    module = _load_script()
    gates = [
        _gate(passed=True, mean=1.1, tv=0.1),
        _gate(passed=False, failures=("joint_ratio_below_floor:x",), mean=1.1, tv=0.2),
        _gate(passed=False, failures=("mean_joint_ratio_not_above_1.0",), mean=0.9, tv=0.2),
        _gate(passed=False, failures=("max_tv_above_0.25:0.5",), mean=1.2, tv=0.5),
    ]
    assert {module._claim_level(gate) for gate in gates} <= {"A", "B", "C", "D"}


def test_v7_claim_document_separates_integrity_failure_from_scientific_negative_result() -> None:
    text = (ROOT / "docs/V7_CLAIM_CEILING.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    assert "no V7 claim level is assigned" in normalized
    assert "Level E" not in text
    assert "A–D" in text
