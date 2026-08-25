from __future__ import annotations

import inspect
import itertools
import json
from pathlib import Path

import numpy as np

from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    IndeterminacyReasonA2,
    SpatiotemporalPoint,
    VisitInferenceA2,
    analyse_point,
    normalized_spatial_structure,
    nuisance_field,
    sampling_support,
    signature_for,
    spatial_shared_weight,
    temporally_resolved,
    truth,
)

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"


def test_protocol_is_prefrozen_and_full_sweep_is_blocked() -> None:
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert payload["status"] == "prefrozen-before-first-scientific-sweep"
    assert payload["parent_negative_result"] == "P3 Pi2-near-one ambiguity prediction not supported"
    assert payload["execution_gate"]["current_state"] == "BLOCKED_BY_DESIGN_PREFREEZE"
    assert payload["execution_gate"]["scientific_sweep_must_not_run_in_this_prefreeze_pr"] is True
    assert payload["anti_tuning_rules"]["first_full_sweep_must_be_retained_if_unfavorable"] is True


def test_prefrozen_grid_cardinalities_are_exact() -> None:
    payload = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for name in ("coarse_sweep", "focused_collision_sweep"):
        sweep = payload[name]
        axes = [
            sweep["pi1_values"], sweep["pi2_values"], sweep["pi3_values"],
            sweep["pi4_values"], sweep["pi5_values"], sweep["pi6_values"],
        ]
        coordinates = 1
        for values in axes:
            coordinates *= len(values)
        assert coordinates == sweep["expected_coordinate_count"]
        worlds = coordinates * len(sweep["latent_deviation_regimes"]) * sweep["replicates_per_coordinate_regime"]
        assert worlds == sweep["expected_deviation_world_count"]


def test_point_exposes_sampling_geometry_without_absolute_units() -> None:
    point = SpatiotemporalPoint(3.0, 0.5, 0.2, 0.4, 1.0, 16.0)
    assert point.samples_per_target_timescale == 16.0
    assert point.samples_per_nuisance_timescale == 8.0
    assert point.nuisance_timescales_per_window == 6.0


def test_spatial_kernel_is_an_independent_monotone_coordinate() -> None:
    narrow = spatial_shared_weight(1.0, 0.1)
    matched = spatial_shared_weight(1.0, 1.0)
    broad = spatial_shared_weight(1.0, 10.0)
    assert 0.0 <= narrow < matched < broad <= 1.0


def test_structure_function_is_scale_sensitive_unlike_correlation() -> None:
    x = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    identical = normalized_spatial_structure(x, x)
    scaled = normalized_spatial_structure(x, 0.5 * x)
    assert identical == 0.0
    assert scaled > 0.0


def test_nuisance_field_is_deterministic_and_pi5_changes_the_spatial_world() -> None:
    narrow = SpatiotemporalPoint(2.0, 1.0, 0.2, 0.2, 0.1, 16.0)
    broad = SpatiotemporalPoint(2.0, 1.0, 0.2, 0.2, 10.0, 16.0)
    first = nuisance_field(narrow, seed=7)
    second = nuisance_field(narrow, seed=7)
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    broad_world = nuisance_field(broad, seed=7)
    assert not np.array_equal(first[2], broad_world[2])


def test_pi6_controls_sampling_support_and_resolved_slice() -> None:
    low = SpatiotemporalPoint(3.0, 1.0, 0.2, 0.2, 1.0, 2.0)
    high = SpatiotemporalPoint(3.0, 1.0, 0.2, 0.2, 1.0, 16.0)
    assert sampling_support(low)[0] < sampling_support(high)[0]
    assert temporally_resolved(low) is False
    assert temporally_resolved(high) is True


def test_signatures_remain_dimensionless_and_bounded_on_construction_smoke_points() -> None:
    point = SpatiotemporalPoint(3.0, 1.0, 0.3, 0.3, 1.0, 16.0)
    for regime, seed in zip(
        (
            LatentRegime.TARGET_ONLY,
            LatentRegime.NUISANCE_ONLY,
            LatentRegime.TARGET_COUPLED,
            LatentRegime.TARGET_NUISANCE_SUPERPOSED,
            LatentRegime.TARGET_NUISANCE_COUPLED,
        ),
        itertools.count(1),
    ):
        vector = signature_for(point, regime, seed=seed).vector()
        assert np.all(np.isfinite(vector))
        assert np.all(vector >= 0.0)
        assert np.all(vector <= 1.0)


def test_baseline_stays_outside_the_discrimination_question() -> None:
    point = SpatiotemporalPoint(1.0, 1.0, 0.3, 0.3, 1.0, 8.0)
    result = analyse_point(point, LatentRegime.BASELINE, seed=1)
    assert result.inference is VisitInferenceA2.NO_QUERY
    assert result.indeterminacy_reason is IndeterminacyReasonA2.NONE


def test_target_and_nuisance_truth_are_nonexclusive() -> None:
    t, n, c = truth(LatentRegime.TARGET_NUISANCE_SUPERPOSED)
    assert (t, n, c) == (True, True, False)
    t, n, c = truth(LatentRegime.TARGET_NUISANCE_COUPLED)
    assert (t, n, c) == (True, True, True)


def test_new_generator_has_no_pollipi_dependency() -> None:
    import interaction_sensing.simulation.dimensionless_observability_v14a2 as module

    source = inspect.getsource(module).lower()
    assert "pollipi" not in source
