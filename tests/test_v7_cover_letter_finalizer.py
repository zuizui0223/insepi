from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finalize_cover_letter_from_v7.py"
SPEC = importlib.util.spec_from_file_location("v7_cover_finalizer_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_cover_letter_uses_same_preregistered_claim_wording() -> None:
    v7 = MODULE.FINALIZER.VerifiedV7(
        ledger={},
        report={},
        claim_level="B",
        gate_passed=False,
        failures=("example_failure",),
        worst_joint=0.97,
        mean_joint=1.03,
        max_tv=0.20,
    )
    template = (ROOT / "editor" / "EDITOR_COVER_LETTER_TEMPLATE.md").read_text(encoding="utf-8")
    final = MODULE.finalize_cover(template, v7)
    assert "[[V7_EDITOR_RESULT_SUMMARY]]" not in final
    assert "conditional rather than generally robust" in final
    assert "claim level B" in final


def test_cover_letter_requires_exactly_one_marker() -> None:
    v7 = MODULE.FINALIZER.VerifiedV7(
        ledger={}, report={}, claim_level="A", gate_passed=True, failures=(), worst_joint=1.01, mean_joint=1.05, max_tv=0.20
    )
    try:
        MODULE.finalize_cover("no marker", v7)
    except ValueError as exc:
        assert "exactly one" in str(exc)
    else:
        raise AssertionError("cover finalizer accepted a template without its locked marker")
