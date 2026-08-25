import json
from pathlib import Path

from interaction_sensing.observation_triad import ObservationTriadPolicy


ROOT = Path(__file__).resolve().parents[1]


def load_contract() -> dict:
    return json.loads((ROOT / "benchmarks" / "v14_observation_triad_contract.json").read_text())


def test_v14_contract_matches_reference_policy_defaults() -> None:
    contract = load_contract()
    policy = ObservationTriadPolicy()
    thresholds = contract["reference_thresholds"]
    assert thresholds == {
        "target_low": policy.target_low_threshold,
        "target_high": policy.target_high_threshold,
        "nuisance_high": policy.nuisance_high_threshold,
        "unobservable_ceiling": policy.unobservable_threshold,
        "observable_ceiling": policy.observable_threshold,
    }


def test_v14_contract_keeps_three_axes_non_equivalent() -> None:
    contract = load_contract()
    axes = contract["axes"]
    assert "observability" in " ".join(axes["target_evidence"]["not_equivalent_to"])
    assert "unobservability" in axes["nuisance_risk"]["not_equivalent_to"]
    assert "one_minus_nuisance" in axes["observation_support"]["not_equivalent_to"]


def test_v14_uses_two_repositories_but_three_scientific_outputs() -> None:
    roles = load_contract()["software_roles"]
    assert roles["PolliPi"]["outputs"] == ["target_evidence"]
    assert roles["InsePi"]["outputs"] == ["nuisance_risk", "observation_support"]
    assert "one minus nuisance" in roles["InsePi"]["rule"]
    assert roles["cross_observer_diagnostic"]["inputs"] == [
        "target_evidence",
        "nuisance_risk",
        "observation_support",
    ]


def test_v14_contract_forbids_false_absence_from_unobservable_windows() -> None:
    contract = load_contract()
    invariants = set(contract["hard_invariants"])
    assert "unobservable windows are censored rather than counted as biological absence" in invariants
    assert "low nuisance does not imply observability" in invariants
    assert "high nuisance does not imply unobservability" in invariants


def test_v14_is_new_development_generation_not_reinterpretation_of_old_results() -> None:
    contract = load_contract()
    assert contract["generation"] == "V14"
    assert contract["status"] == "development-contract-no-performance-claim"
    assert "field visit accuracy" in contract["claim_ceiling"]["forbidden_before_validation"]
