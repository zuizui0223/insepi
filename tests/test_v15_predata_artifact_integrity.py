import hashlib
import json
from pathlib import Path


REGISTRY = Path("benchmarks/v15_prefreeze_readiness_registry.json")
ABSENCE = Path("benchmarks/v15_absence_strategy_v1.json")
CLAIMS = Path("benchmarks/v15_claim_thresholds_v1_template.json")


def test_absence_strategy_artifact_matches_registered_sha256() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    strategy = json.loads(ABSENCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(ABSENCE.read_bytes()).hexdigest()

    assert registry["absence_strategy"] == "retain_upper_bound_1_without_A_minus"
    assert registry["absence_strategy_evidence_path"] == str(ABSENCE)
    assert registry["absence_strategy_sha256"] == digest
    assert strategy["strategy"] == registry["absence_strategy"]
    assert strategy["safe_target_presence_upper_bound"] == 1.0
    assert registry["safe_target_presence_upper_bound"] == 1.0


def test_claim_template_contains_no_invented_numerical_thresholds() -> None:
    payload = json.loads(CLAIMS.read_text(encoding="utf-8"))
    slots = payload["claim_slots"]
    assert slots
    assert all(slot["threshold"] is None for slot in slots)
    assert any(slot["requires_A_minus"] for slot in slots)
    assert payload["decision_policy"]["point_estimate_alone_can_authorize_claim"] is False
