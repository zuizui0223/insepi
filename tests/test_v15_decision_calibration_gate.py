import json
from pathlib import Path

from interaction_sensing.v15_prefreeze import CORE_FREEZE_ITEMS, evaluate_prefreeze_registry


REGISTRY = Path("benchmarks/v15_prefreeze_readiness_registry.json")
COUPLED = Path("benchmarks/v15_coupled_field_adapter_v1_contract.json")
DECISION = Path("benchmarks/v15_target_nuisance_decision_calibration_v1_contract.json")


def test_expanded_core_requires_coupled_field_and_operational_decision_calibration() -> None:
    assert "coupled_field_adapter" in CORE_FREEZE_ITEMS
    assert "target_nuisance_decision_calibration" in CORE_FREEZE_ITEMS
    readiness = evaluate_prefreeze_registry(json.loads(REGISTRY.read_text(encoding="utf-8")))
    assert "coupled_field_adapter" in readiness.blockers
    assert "target_nuisance_decision_calibration" in readiness.blockers


def test_coupled_field_contract_has_no_invented_runtime_measurement_or_calibration() -> None:
    payload = json.loads(COUPLED.read_text(encoding="utf-8"))
    state = payload["current_state"]
    assert state["field_measurement_implementation"] is None
    assert state["field_calibration"] is None
    assert state["frozen_threshold_or_mapping"] is None
    assert payload["runtime_combination"] == "usable coupled target route = coupled_response_score * target_link_confidence"


def test_operational_decision_contract_marks_old_numbers_as_unfrozen_defaults() -> None:
    payload = json.loads(DECISION.read_text(encoding="utf-8"))
    defaults = payload["current_development_defaults_not_frozen"]
    assert defaults == {
        "target_high": 0.65,
        "target_low": 0.25,
        "nuisance_high": 0.60,
        "source": "VisitSystemThresholds / ObservationTriadPolicy development defaults",
    }
    assert payload["target_boundary_required"]["target_high"] is None
    assert payload["target_boundary_required"]["target_low"] is None
    assert payload["nuisance_boundary_required"]["nuisance_high"] is None
    assert payload["nuisance_boundary_required"]["effect_risk_mapping"] is None
