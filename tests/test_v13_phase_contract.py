from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v13_active_phases_are_non_cumulative_and_share_one_placebo_reference() -> None:
    contract = json.loads((ROOT / "benchmarks/v13_physical_phase_contract.json").read_text())
    rule = contract["paired_counterfactual_rule"]
    assert rule["active_interventions_are_cumulative"] is False
    assert rule["each_active_phase_starts_from_same_latent_treatment_baseline"] is True
    assert rule["washout_restores_latent_treatment_before_next_active_phase"] is True
    assert rule["all_delta_responses_use_same_placebo_reference_within_block"] is True
    assert rule["abort_block_if_latent_baseline_cannot_be_restored"] is True


def test_v13_phase_timing_matches_main_physical_protocol() -> None:
    protocol = json.loads((ROOT / "benchmarks/v13_physical_intervention_protocol.json").read_text())
    contract = json.loads((ROOT / "benchmarks/v13_physical_phase_contract.json").read_text())
    timing = contract["timing"]
    assert timing["placebo_seconds"] == protocol["diagnostic_phases"]["placebo"]["duration_seconds"] == 10
    assert timing["active_phase_seconds"] == protocol["diagnostic_phases"]["active"]["duration_seconds_each"] == 10
    assert timing["washout_seconds"] == protocol["diagnostic_phases"]["active"]["washout_seconds_between_phases"] == 5
    assert timing["discard_initial_seconds_per_recorded_phase"] == protocol["diagnostic_phases"]["phase_summary"]["discard_initial_stabilisation_seconds"] == 2


def test_v13_development_and_heldout_physical_subtypes_remain_distinct() -> None:
    contract = json.loads((ROOT / "benchmarks/v13_physical_phase_contract.json").read_text())
    development = contract["development_operationalisation"]
    heldout = contract["heldout_operationalisation"]
    for treatment in ("event_side", "nuisance_side", "shared_optical", "no_fault"):
        assert development[treatment]["latent_impairment"] != heldout[treatment]["latent_impairment"]


def test_v13_operator_may_not_condition_experiment_on_observer_output() -> None:
    contract = json.loads((ROOT / "benchmarks/v13_physical_phase_contract.json").read_text())
    boundary = contract["operator_blinding_boundary"]
    assert boundary["operator_knows_physical_treatment"] is True
    assert boundary["observer_algorithm_does_not"] is True
    assert boundary["heldout_evaluator_truth_join_occurs_after_predictions"] is True
    assert boundary["operator_may_not_change_phase_order_or_treatment_after_viewing_observer_output"] is True
