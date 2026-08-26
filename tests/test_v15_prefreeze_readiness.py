import json
from pathlib import Path

import pytest

from interaction_sensing.v15_prefreeze import (
    A_MINUS_VALIDATION_ITEM,
    AbsenceStrategy,
    CORE_FREEZE_ITEMS,
    PrefreezeGateState,
    assert_ready_for_heldout,
    evaluate_prefreeze_registry,
)


REGISTRY = Path("benchmarks/v15_prefreeze_readiness_registry.json")
HEX = "a" * 64


def current_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def frozen_item(name: str) -> dict:
    return {
        "name": name,
        "status": "frozen",
        "evidence_path": f"freeze/{name}.json",
        "sha256": HEX,
    }


def strategy_fields(strategy: str) -> dict:
    return {
        "absence_strategy": strategy,
        "absence_strategy_evidence_path": "freeze/absence-strategy.json",
        "absence_strategy_sha256": HEX,
    }


def test_current_v15_prefreeze_registry_has_seven_frozen_core_items() -> None:
    readiness = evaluate_prefreeze_registry(current_registry())
    assert readiness.state is PrefreezeGateState.BLOCKED_SAFE
    assert readiness.design_complete is True
    assert readiness.absence_strategy is AbsenceStrategy.RETAIN_UPPER_BOUND_1
    assert readiness.safe_target_presence_upper_bound == 1.0
    assert readiness.unset_items == ()
    assert set(readiness.frozen_items) == {
        "biological_truth_annotation",
        "coupling_truth_annotation",
        "nuisance_truth_annotation",
        "support_truth_annotation",
        "target_field_adapter",
        "forced_vs_certified_absence_metrics",
        "cluster_exposure_estimand",
    }
    assert len(readiness.frozen_items) == 7
    assert len(readiness.development_defined_items) == 5
    assert set(readiness.blockers) == set(CORE_FREEZE_ITEMS) - set(readiness.frozen_items)
    assert "split_blinding_protocol" in readiness.development_defined_items
    assert "o_measurement_calibration" in readiness.development_defined_items
    assert "nuisance_field_adapter" in readiness.development_defined_items
    assert "sampling_power_plan" in readiness.development_defined_items
    assert "claim_thresholds" in readiness.development_defined_items


def test_current_registry_cannot_start_heldout() -> None:
    with pytest.raises(RuntimeError, match="BLOCKED_SAFE"):
        assert_ready_for_heldout(current_registry())


def test_ready_without_A_minus_requires_explicit_upper_bound_one_strategy() -> None:
    payload = {
        "generation": "V15-v2",
        **strategy_fields("retain_upper_bound_1_without_A_minus"),
        "safe_target_presence_upper_bound": 1.0,
        "items": [frozen_item(name) for name in CORE_FREEZE_ITEMS],
    }
    readiness = assert_ready_for_heldout(payload)
    assert readiness.ready
    assert readiness.design_complete
    assert readiness.state is PrefreezeGateState.READY


def test_no_A_minus_strategy_cannot_silently_tighten_upper_bound() -> None:
    payload = {
        "generation": "V15-v2",
        **strategy_fields("retain_upper_bound_1_without_A_minus"),
        "safe_target_presence_upper_bound": 0.9,
        "items": [frozen_item(name) for name in CORE_FREEZE_ITEMS],
    }
    with pytest.raises(ValueError, match="upper bound at 1"):
        evaluate_prefreeze_registry(payload)


def test_decided_absence_strategy_requires_predata_provenance() -> None:
    payload = {
        "generation": "V15-v2",
        "absence_strategy": "retain_upper_bound_1_without_A_minus",
        "safe_target_presence_upper_bound": 1.0,
        "items": [frozen_item(name) for name in CORE_FREEZE_ITEMS],
    }
    with pytest.raises(ValueError, match="evidence_path"):
        evaluate_prefreeze_registry(payload)

    payload["absence_strategy_evidence_path"] = "freeze/absence.json"
    with pytest.raises(ValueError, match="64-hex"):
        evaluate_prefreeze_registry(payload)


def test_validated_A_minus_path_requires_its_own_frozen_protocol() -> None:
    payload = {
        "generation": "V15-v2",
        **strategy_fields("validated_independent_A_minus"),
        "safe_target_presence_upper_bound": 1.0,
        "items": [frozen_item(name) for name in CORE_FREEZE_ITEMS],
    }
    readiness = evaluate_prefreeze_registry(payload)
    assert readiness.state is PrefreezeGateState.BLOCKED_SAFE
    assert A_MINUS_VALIDATION_ITEM in readiness.blockers

    payload["items"].append(frozen_item(A_MINUS_VALIDATION_ITEM))
    assert assert_ready_for_heldout(payload).ready


def test_frozen_item_requires_hash_and_evidence_path() -> None:
    payload = current_registry()
    payload["items"][0] = {
        "name": CORE_FREEZE_ITEMS[0],
        "status": "frozen",
        "evidence_path": "freeze/example.json",
        "sha256": None,
    }
    with pytest.raises(ValueError, match="requires lowercase 64-hex sha256"):
        evaluate_prefreeze_registry(payload)


def test_missing_or_unknown_freeze_item_fails_closed() -> None:
    payload = current_registry()
    payload["items"] = payload["items"][:-1]
    with pytest.raises(ValueError, match="missing core freeze items"):
        evaluate_prefreeze_registry(payload)

    payload = current_registry()
    payload["items"].append({"name": "invented_gate", "status": "unset"})
    with pytest.raises(ValueError, match="unknown freeze items"):
        evaluate_prefreeze_registry(payload)
