from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from interaction_sensing.simulation import contradiction_development_v11 as v11

ROOT = Path(__file__).resolve().parents[1]


def protocol() -> dict[str, object]:
    return json.loads((ROOT / v11.PROTOCOL_PATH).read_text())


def test_v11_protocol_is_frozen_before_result_and_preserves_prior_generations() -> None:
    p = protocol()
    assert p["status"] == "pre-result-frozen"
    assert p["scientific_object"] == "development strategy, not a new allocation score"
    assert p["prior_result_boundary"]["v7_gate"] == "FAIL"
    assert p["prior_result_boundary"]["v7_claim_level"] == "C"
    assert p["non_interference"] == {
        "v6_weights_changed": False,
        "v7_result_changed_or_rescued": False,
        "v10_protocol_or_pixels_changed": False,
        "v8_or_v9_retuned": False,
        "direct_disagreement_allocation_restored": False,
    }


def test_v11_development_and_heldout_mechanisms_are_disjoint() -> None:
    p = protocol()
    dev = set(p["mechanisms"]["development"].values())
    heldout = set(p["mechanisms"]["heldout"].values())
    assert dev.isdisjoint(heldout)
    assert set(p["mechanisms"]["development"]) == set(v11.CLASSES)
    assert set(p["mechanisms"]["heldout"]) == set(v11.CLASSES)


def test_v11_same_probe_order_and_audit_assignment_are_shared_by_all_strategies() -> None:
    p = protocol()
    assert p["experiments_to_stable_falsification"]["same_probe_order_for_all_strategies"] is True
    assert p["protected_audit"]["same_audit_assignments_for_all_strategies"] is True
    episode = v11.generate_episode("heldout", "shared_representation", 0.65, 17)
    assert tuple(row.probe for row in episode.probes) == tuple(row[0] for row in v11.PROBES)
    # Audit is part of the episode, not strategy-specific state.
    masks = [tuple(row.protected_audit for row in episode.probes) for _ in v11.STRATEGIES]
    assert len(set(masks)) == 1


def test_v11_truth_factorial_design_contains_all_four_controlled_states() -> None:
    assert [(event, disturbance) for _name, event, disturbance, known in v11.PROBES[:4]] == [
        (0, 0), (1, 0), (0, 1), (1, 1)
    ]
    assert all(known for _name, _e, _d, known in v11.PROBES[:4])


def test_v11_blind_truth_is_not_exposed_without_protected_audit() -> None:
    for replicate in range(50):
        ep = v11.generate_episode("heldout", "shared_representation", 0.95, replicate)
        for row in ep.probes[4:]:
            if not row.protected_audit:
                assert row.truth_known is False


def test_v11_diagnostic_state_has_exact_four_way_partition() -> None:
    cases = {
        (0.8, 0.2): (1.0, 0.0, 0.0, 0.0),
        (0.2, 0.8): (0.0, 1.0, 0.0, 0.0),
        (0.8, 0.8): (0.0, 0.0, 1.0, 0.0),
        (0.2, 0.2): (0.0, 0.0, 0.0, 1.0),
    }
    for pair, expected in cases.items():
        assert v11.diagnostic_state(*pair) == expected


def test_v11_feature_channels_match_frozen_strategy_contract() -> None:
    ep = v11.generate_episode("development", "event_module", 0.65, 3)
    assert v11.features(ep, "event_only").shape == (18,)
    assert v11.features(ep, "observability_only").shape == (18,)
    assert v11.features(ep, "early_scalar_fusion").shape == (18,)
    assert v11.features(ep, "contradiction_guided").shape == (60,)


def test_v11_episode_generation_is_byte_deterministic_in_arrays() -> None:
    a = v11.generate_episode("heldout", "observability_module", 0.95, 111)
    b = v11.generate_episode("heldout", "observability_module", 0.95, 111)
    assert a == b
    assert np.array_equal(v11.features(a, "contradiction_guided"), v11.features(b, "contradiction_guided"))


def test_v11_correct_repair_reduces_expected_loss_on_each_failure_class() -> None:
    for failure_class in ("event_module", "observability_module", "shared_representation"):
        before = []
        after = []
        for replicate in range(40):
            base = v11.generate_episode("heldout", failure_class, 0.95, replicate)
            repaired = v11.generate_episode(
                "heldout", failure_class, 0.95, replicate, repair_action=failure_class
            )
            before.append(v11._loss(base))
            after.append(v11._loss(repaired))
        assert np.mean(after) < np.mean(before)


def test_v11_wrong_repairs_are_not_forced_to_be_helpful() -> None:
    changes = []
    for replicate in range(60):
        base = v11.generate_episode("heldout", "event_module", 0.95, replicate)
        wrong = v11.generate_episode(
            "heldout", "event_module", 0.95, replicate, repair_action="observability_module"
        )
        changes.append(v11._loss(base) - v11._loss(wrong))
    assert any(change <= 0.0 for change in changes)


def test_v11_smoke_run_uses_only_heldout_for_scoring() -> None:
    result = v11.run_v11(development_replicates=8, heldout_replicates=8)
    assert result["development_episode_count"] == 4 * 3 * 8
    assert result["heldout_episode_count"] == 4 * 3 * 8
    assert set(result["strategies"]) == set(v11.STRATEGIES)
    assert result["claim"]["level"] in {"A", "B", "C", "D"}
    assert result["v7_locked_result_retained"] == {"gate": "FAIL", "claim_level": "C"}
    assert result["v6_weights_changed"] is False
    assert result["v10_changed"] is False
