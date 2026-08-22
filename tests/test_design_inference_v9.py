from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing.guarded_portfolio import GuardedPortfolio, select_guarded_indices
from interaction_sensing.simulation.design_inference_v9 import (
    _hypergeom_cdf_table,
    binary_srs_variance,
    exact_hypergeometric_interval,
    protected_exploration_indices,
    select_frozen_v6_with_reference,
)
from interaction_sensing.simulation.generality_v8 import Regime, generate_world


ROOT = Path(__file__).resolve().parents[1]


def test_protocol_is_frozen_before_result() -> None:
    protocol = json.loads((ROOT / "benchmarks" / "v9_design_inference_protocol.json").read_text())
    assert protocol["schema"] == "interaction-sensing-v9-design-inference-protocol-v1"
    assert protocol["frozen_candidate"] == {
        "exploration": 0.50,
        "evidence": 0.10,
        "observability": 0.40,
        "disagreement": 0.00,
    }
    world = protocol["world"]
    regime_count = (
        len(world["event_prevalence"])
        * len(world["budget_fraction"])
        * len(world["evidence_quality"])
        * len(world["observability_quality"])
        * len(world["residual_correlation"])
        * len(world["disturbance_prevalence"])
    )
    assert regime_count == 576
    assert world["paired_replicates"] == 100


def test_protected_reference_matches_initial_generic_exploration() -> None:
    regime = Regime(
        event_prevalence=0.1,
        budget_fraction=0.25,
        evidence_quality=0.75,
        observability_quality=0.75,
        residual_correlation=0.5,
        disturbance_prevalence=0.5,
    )
    world = generate_world(n=160, regime=regime, seed=123)
    selection = select_frozen_v6_with_reference(world, budget_fraction=0.25, seed=456)
    portfolio = GuardedPortfolio.frozen_v6_reference()
    rows = [{"evidence": row.evidence, "observability": row.observability} for row in world]
    selected, provenance = select_guarded_indices(
        rows, budget_fraction=0.25, portfolio=portfolio, seed=456
    )
    reconstructed = protected_exploration_indices(
        len(world), budget_fraction=0.25, seed=456, portfolio=portfolio
    )
    assert selection.selected == frozenset(selected)
    assert selection.protected_exploration == reconstructed
    assert selection.protected_exploration.issubset(selection.selected)
    assert len(selection.protected_exploration) == provenance["exploration"]


def test_binary_srs_variance_has_finite_population_correction() -> None:
    variance = binary_srs_variance(population_size=100, sample_size=20, prevalence=0.5)
    expected = (100 - 20) / (20 * 99) * 0.5 * 0.5
    assert abs(variance - expected) < 1e-15
    assert binary_srs_variance(population_size=100, sample_size=100, prevalence=0.5) == 0.0


def test_exact_hypergeometric_interval_respects_feasible_bounds() -> None:
    interval0 = exact_hypergeometric_interval(100, 20, 0)
    interval20 = exact_hypergeometric_interval(100, 20, 20)
    assert interval0.lower == 0.0
    assert 0.0 <= interval0.upper < 1.0
    assert 0.0 < interval20.lower <= 1.0
    assert interval20.upper == 1.0


def test_exact_interval_has_at_least_nominal_small_population_coverage() -> None:
    # Exhaustive design-coverage check over every finite-population K for a small
    # population. This validates the inversion logic without Monte Carlo noise.
    population_size = 30
    sample_size = 6
    confidence = 0.95
    worst_coverage = 1.0
    for successes in range(population_size + 1):
        cdf = _hypergeom_cdf_table(population_size, successes, sample_size)
        previous = 0.0
        coverage = 0.0
        for observed in range(sample_size + 1):
            probability = cdf[observed] - previous
            previous = cdf[observed]
            interval = exact_hypergeometric_interval(
                population_size, sample_size, observed, confidence
            )
            target = successes / population_size
            if interval.covers(target):
                coverage += probability
        worst_coverage = min(worst_coverage, coverage)
    assert worst_coverage >= confidence - 1e-12


def test_v9_module_does_not_depend_on_v7() -> None:
    source = (ROOT / "src" / "interaction_sensing" / "simulation" / "design_inference_v9.py").read_text()
    assert "v7_" not in source.lower()
    assert "locked_world_v7" not in source
