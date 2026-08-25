from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing.guarded_portfolio import (
    GuardedPortfolio,
    select_guarded_indices,
)
from interaction_sensing.simulation.generality_v8 import (
    Regime,
    generate_world,
    protocol_regimes,
    select_with_provenance,
)


ROOT = Path(__file__).resolve().parents[1]


def _protocol() -> dict[str, object]:
    return json.loads((ROOT / "benchmarks" / "v8_generality_protocol.json").read_text())


def test_protocol_is_large_factorial_and_freezes_v6_vector() -> None:
    protocol = _protocol()
    assert protocol["status"] == "pre_registered_before_result_inspection"
    assert protocol["frozen_candidate"] == {
        "exploration": 0.50,
        "evidence": 0.10,
        "observability": 0.40,
        "disagreement": 0.00,
    }
    assert len(protocol_regimes(protocol)) == 864
    assert "must not change" in str(protocol["no_tuning_rule"])


def test_v8_guarded_v6_selector_matches_generic_public_api() -> None:
    regime = Regime(
        event_prevalence=0.10,
        budget_fraction=0.25,
        evidence_quality=0.75,
        observability_quality=0.75,
        residual_correlation=0.50,
        disturbance_prevalence=0.40,
    )
    world = generate_world(n=240, regime=regime, seed=1234)
    score_rows = [
        {"evidence": row.evidence, "observability": row.observability}
        for row in world
    ]
    generic_selected, _counts = select_guarded_indices(
        score_rows,
        budget_fraction=0.25,
        portfolio=GuardedPortfolio.frozen_v6_reference(),
        seed=4321,
    )
    v8 = select_with_provenance(
        world,
        budget_fraction=0.25,
        policy="guarded_v6",
        seed=4321,
    )
    assert set(v8.selected) == generic_selected
    assert len(v8.selected) == 60
    assert len(v8.exploration) >= 30


def test_same_alpha_comparators_retain_half_budget_exploration() -> None:
    regime = Regime(0.50, 0.10, 0.75, 0.75, 0.0, 0.10)
    world = generate_world(n=400, regime=regime, seed=9)
    for policy in (
        "guarded_v6",
        "guarded_e_only",
        "guarded_o_only",
        "guarded_fused_20_80",
        "guarded_max",
    ):
        selection = select_with_provenance(
            world,
            budget_fraction=0.10,
            policy=policy,
            seed=10,
        )
        assert len(selection.selected) == 40
        assert len(selection.exploration) >= 20


def test_uniform_policy_is_simple_random_budget_sample() -> None:
    regime = Regime(0.10, 0.05, 0.60, 0.90, 0.90, 0.40)
    world = generate_world(n=800, regime=regime, seed=11)
    selection = select_with_provenance(
        world,
        budget_fraction=0.05,
        policy="uniform",
        seed=12,
    )
    assert len(selection.selected) == 40
    assert selection.selected == selection.exploration
