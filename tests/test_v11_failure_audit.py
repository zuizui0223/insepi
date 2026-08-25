from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_v11_failure.py"

spec = importlib.util.spec_from_file_location("v11_failure_audit_script", AUDIT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load {AUDIT_PATH}")
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


def test_v11_failure_audit_is_bound_to_canonical_negative_result() -> None:
    summary = json.loads((ROOT / "benchmarks/v11_contradiction_development_result_summary.json").read_text())
    assert summary["claim"] == {"level": "D", "label": "no_general_localisation_advantage"}
    assert summary["result_sha256"] == audit.CANONICAL_RESULT_SHA256
    assert summary["protocol_sha256"] == audit.CANONICAL_PROTOCOL_SHA256


def test_v11_failure_audit_is_descriptive_only() -> None:
    result = audit.audit()
    assert result["status"] == "descriptive-post-result-not-a-new-gate"
    assert result["canonical_result_sha256"] == audit.CANONICAL_RESULT_SHA256
    assert set(result["strategies"]) == {
        "event_only", "observability_only", "early_scalar_fusion", "contradiction_guided"
    }
    assert set(result["diagnostic_state_prevalence"]) == {"development", "heldout"}
    assert "This audit cannot change V11 claim level D." in result["interpretation_limits"]
