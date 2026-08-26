import json
from pathlib import Path

from interaction_sensing.development.visit_contradiction import (
    VisitDevelopmentCause,
    VisitDiagnosticPattern,
    VisitSubsystem,
)


ROOT = Path(__file__).resolve().parents[1]


def contract() -> dict:
    return json.loads((ROOT / "benchmarks" / "v15_contradiction_guided_development_contract.json").read_text())


def test_contract_cause_classes_match_code() -> None:
    data = contract()
    assert set(data["post_truth_cause_classes"]) == {item.value for item in VisitDevelopmentCause}


def test_contract_alternating_subsystems_match_code() -> None:
    data = contract()
    assert set(data["alternating_development"]["subsystems"]) == {item.value for item in VisitSubsystem}


def test_key_runtime_patterns_are_implemented() -> None:
    data = contract()
    names = {row["pattern"] for row in data["pattern_rules"]}
    implemented = {item.value for item in VisitDiagnosticPattern}
    assert names <= implemented
    assert {
        "target_nuisance_superposition",
        "quiet_unobservable",
        "target_support_conflict",
        "nuisance_possible_miss",
        "coupled_rescue_candidate",
    } <= names


def test_stop_rule_is_type_saturation_not_zero_disagreement() -> None:
    data = contract()
    assert data["stop_rule"]["criterion"] == "contradiction-type saturation across required strata"
    assert data["stop_rule"]["not_criterion"] == "zero contradiction count"


def test_truth_is_joined_only_after_observer_outputs() -> None:
    data = contract()
    assert data["truth_timing"] == {
        "observer_outputs_first": True,
        "independent_truth_join_after_outputs": True,
        "cause_class_assigned_after_truth_join": True,
    }
