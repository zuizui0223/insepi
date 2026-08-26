from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np
import pytest

from interaction_sensing.simulation import causal_intervention_v12 as v12

ROOT = Path(__file__).resolve().parents[1]


def test_v12_protocol_is_pre_result_and_preserves_prior_failures() -> None:
    protocol = json.loads((ROOT / "benchmarks/v12_causal_intervention_protocol.json").read_text())
    assert protocol["status"] == "pre-result-frozen"
    assert protocol["historical_boundaries"]["v7_locked_gate"] == "FAIL"
    assert protocol["historical_boundaries"]["v7_claim_level"] == "C"
    assert protocol["historical_boundaries"]["v11_locked_claim_level"] == "D"
    assert protocol["historical_boundaries"]["v11_result_sha256"] == (
        "654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1"
    )
    assert protocol["historical_boundaries"]["v11_may_not_be_retuned"] is True


def test_v12_mechanism_subtypes_are_disjoint_across_development_and_heldout() -> None:
    protocol = v12.load_protocol()
    dev = set(protocol["mechanism_subtypes"]["development"].values())
    heldout = set(protocol["mechanism_subtypes"]["heldout"].values())
    assert dev.isdisjoint(heldout)


def test_v12_episode_generation_is_deterministic_and_strategy_independent() -> None:
    first = v12.generate_episode("heldout", "shared_representation", 0.65, 37)
    second = v12.generate_episode("heldout", "shared_representation", 0.65, 37)
    assert first == second
    assert set(first.observed.responses) == set(v12.ACTIVE_INTERVENTIONS)
    assert first.observed.audit_available == second.observed.audit_available
    assert first.observed.audit_fault_present == second.observed.audit_fault_present


def test_v12_protected_audit_reveals_fault_presence_not_failure_class() -> None:
    for label in v12.CLASSES:
        found = None
        for replicate in range(100):
            ep = v12.generate_episode("heldout", label, 0.65, replicate)
            if ep.observed.audit_available:
                found = ep
                break
        assert found is not None
        assert found.observed.audit_fault_present is (label != "no_fault")
        fields = set(found.observed.__dataclass_fields__)
        assert "failure_class" not in fields
        assert "mechanism" not in fields


def test_v12_representations_keep_dual_channel_minimal_and_unexpanded() -> None:
    response = (0.4, 0.8)
    assert v12.representation(response, "event_only").shape == (1,)
    assert v12.representation(response, "observability_only").shape == (1,)
    assert v12.representation(response, "early_scalar_fusion").shape == (1,)
    dual = v12.representation(response, "interventional_dual_observer")
    assert dual.shape == (2,)
    assert np.array_equal(dual, np.asarray([0.4, 0.8]))


def test_v12_diagnose_signature_has_no_truth_argument() -> None:
    names = set(inspect.signature(v12.diagnose).parameters)
    assert names == {"model", "observed", "budget"}
    assert "failure_class" not in names
    assert "mechanism" not in names


def _mini_development() -> list[v12.CausalEpisode]:
    return [
        v12.generate_episode("development", label, intensity, replicate)
        for label in v12.CLASSES
        for intensity in (0.35, 0.65, 0.95)
        for replicate in range(20)
    ]


@pytest.mark.parametrize("strategy", v12.STRATEGIES)
def test_v12_all_strategies_use_same_budget_and_unique_interventions(strategy: str) -> None:
    model = v12.fit_model(_mini_development(), strategy)
    ep = next(
        v12.generate_episode("heldout", "shared_representation", 0.95, replicate)
        for replicate in range(100)
        if not v12.generate_episode("heldout", "shared_representation", 0.95, replicate).observed.audit_available
    )
    result = v12.diagnose(model, ep.observed, budget=2)
    assert len(result.intervention_order) == 3
    assert len(set(result.intervention_order)) == 3
    assert set(result.intervention_order) == set(v12.ACTIVE_INTERVENTIONS)
    assert len(result.predictions_by_prefix) == 3
    assert result.predicted_class == result.predictions_by_prefix[1]
    assert result.full_battery_prediction == result.predictions_by_prefix[2]


def test_v12_decisive_no_fault_audit_can_stop_without_causal_intervention() -> None:
    model = v12.fit_model(_mini_development(), "interventional_dual_observer")
    ep = next(
        v12.generate_episode("heldout", "no_fault", 0.65, replicate)
        for replicate in range(100)
        if v12.generate_episode("heldout", "no_fault", 0.65, replicate).observed.audit_available
    )
    result = v12.diagnose(model, ep.observed, budget=2)
    assert result.predicted_class == "no_fault"
    assert result.intervention_order == ()
    assert result.full_battery_prediction == "no_fault"


def test_v12_causal_topology_has_expected_directional_controls() -> None:
    protocol = v12.load_protocol()
    dev = protocol["causal_response_topology"]["development"]
    assert dev["event_module"]["event_restore"][0] > dev["event_module"]["observability_restore"][0]
    assert dev["observability_module"]["observability_restore"][1] > dev["observability_module"]["event_restore"][1]
    shared = dev["shared_representation"]["shared_restore"]
    assert shared[0] > dev["shared_representation"]["event_restore"][0]
    assert shared[1] > dev["shared_representation"]["observability_restore"][1]
    assert all(value < 0 for pair in dev["no_fault"].values() for value in pair)


def test_v12_repair_contract_does_not_make_unrelated_wrong_repairs_helpful() -> None:
    protocol = v12.load_protocol()
    assert v12._repair_fraction("event_module", "event_module", protocol) == pytest.approx(0.80)
    assert v12._repair_fraction("event_module", "shared_representation", protocol) == pytest.approx(0.30)
    assert v12._repair_fraction("shared_representation", "event_module", protocol) == pytest.approx(0.35)
    assert v12._repair_fraction("event_module", "observability_module", protocol) == pytest.approx(-0.05)
    assert v12._repair_fraction("event_module", "no_fault", protocol) == 0.0


@pytest.mark.parametrize(
    ("dual_acc", "best_comp", "shared", "wrong", "repair", "full", "expected"),
    [
        (0.90, 0.75, 0.90, 0.10, 0.85, 0.92, "A"),
        (0.80, 0.80, 0.70, 0.30, 0.65, 0.82, "B"),
        (0.78, 0.75, 0.60, 0.30, 0.55, 0.80, "C"),
        (0.60, 0.70, 0.80, 0.10, 0.80, 0.90, "D"),
        (0.90, 0.75, 0.40, 0.10, 0.80, 0.90, "D"),
    ],
)
def test_v12_claim_precedence_is_frozen(
    dual_acc: float,
    best_comp: float,
    shared: float,
    wrong: float,
    repair: float,
    full: float,
    expected: str,
) -> None:
    base = {
        "heldout_localisation_accuracy_budget2": best_comp,
        "shared_representation_recall_budget2": 0.5,
        "wrong_module_intervention_rate_budget2": 0.5,
        "heldout_repair_positive_transfer_rate": 0.5,
        "heldout_full_battery_localisation_accuracy": 0.5,
    }
    summaries = {
        "event_only": dict(base),
        "observability_only": dict(base),
        "early_scalar_fusion": dict(base),
        "interventional_dual_observer": {
            "heldout_localisation_accuracy_budget2": dual_acc,
            "shared_representation_recall_budget2": shared,
            "wrong_module_intervention_rate_budget2": wrong,
            "heldout_repair_positive_transfer_rate": repair,
            "heldout_full_battery_localisation_accuracy": full,
        },
    }
    level, _ = v12._claim(summaries)
    assert level == expected


def test_v12_protocol_hash_is_bound_to_file_bytes() -> None:
    expected = hashlib.sha256((ROOT / "benchmarks/v12_causal_intervention_protocol.json").read_bytes()).hexdigest()
    assert v12.protocol_sha256() == expected
    assert len(expected) == 64
