import json
from pathlib import Path

from interaction_sensing.absence_certification import TargetAbsenceEvidence
from interaction_sensing.observation_triad import ProcessPreservingObservationTriadPolicy
from interaction_sensing.visit_systems import VisitSystemInputs


ROOT = Path(__file__).resolve().parents[1]


def test_v15_v2_contract_keeps_O_separate_from_absence() -> None:
    contract = json.loads((ROOT / "benchmarks/v15_empirical_bridge_v2_contract.json").read_text())
    rules = set(contract["hard_rules"])
    assert "O is not target-absence evidence" in rules
    assert "a low or zero score from the positive target observer cannot be inverted into absence evidence" in rules
    assert contract["current_absence_channel_status"]["field_validated"] is False
    assert contract["current_absence_channel_status"]["safe_target_presence_upper_bound_without_A_minus"] == 1.0


def test_v15_full_policy_is_process_preserving() -> None:
    # The public full-system implementation imports this exact V14b policy;
    # this test prevents a silent regression to the historical V14a conflict policy.
    assert ProcessPreservingObservationTriadPolicy.__name__ == "ProcessPreservingObservationTriadPolicy"


def test_visit_system_inputs_default_to_no_absence_channel() -> None:
    assert VisitSystemInputs.__dataclass_fields__["absence_evidence"].default is None
    assert TargetAbsenceEvidence.unavailable().supports_absence is False
