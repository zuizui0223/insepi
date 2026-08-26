from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from interaction_sensing.simulation.visit_inference_v14 import (
    POLICIES,
    diagnostic_slice,
    evaluate_policy,
    generate_world,
)


ROOT = Path(__file__).resolve().parents[1]


def test_v14_benchmark_contract_preserves_three_axis_question() -> None:
    contract = json.loads((ROOT / "benchmarks/v14_visit_inference_benchmark.json").read_text())
    assert contract["status"] == "development-benchmark-preregistered-before-result"
    assert contract["latent_axes"]["visit_truth"] == [False, True]
    assert set(contract["latent_axes"]["nuisance_mechanism"]) == {
        "clean", "mimic", "mask", "attribution", "support_loss"
    }
    assert contract["latent_axes"]["support_truth"] == ["observable", "compromised", "unobservable"]
    assert set(contract["policies"]) == set(POLICIES)
    assert "Do not collapse the primary metrics into one scalar winner." in contract["interpretation_rules"]


def test_world_generation_is_deterministic() -> None:
    first = generate_world(140314, 25)
    second = generate_world(140314, 25)
    assert first == second
    assert first != generate_world(140315, 25)


def test_low_nuisance_unobservable_is_not_safe_absence_under_triad() -> None:
    world = generate_world(140314, 250)
    target = diagnostic_slice(world, "target_only", "low_nuisance_unobservable")
    two_axis = diagnostic_slice(world, "target_plus_nuisance", "low_nuisance_unobservable")
    triad = diagnostic_slice(world, "triad", "low_nuisance_unobservable")

    assert triad["censor_rate"] > 0.99
    assert triad["denominator_eligible_rate"] < 0.01
    assert triad["false_absence_rate"] < target["false_absence_rate"]
    assert triad["false_absence_rate"] < two_axis["false_absence_rate"]


def test_high_nuisance_observable_is_not_automatically_censored() -> None:
    world = generate_world(140316, 250)
    triad = diagnostic_slice(world, "triad", "high_nuisance_observable")
    assert triad["censor_rate"] < 0.01
    assert triad["denominator_eligible_rate"] > 0.95


def test_triad_reduces_unobservable_denominator_contamination_without_losing_observable_effort() -> None:
    world = generate_world(140317, 300)
    metrics = {policy: asdict(evaluate_policy(policy, world)) for policy in POLICIES}

    assert metrics["target_only"]["unobservable_denominator_contamination"] == 1.0
    assert metrics["triad"]["unobservable_denominator_contamination"] < 0.01
    assert metrics["triad"]["unobservable_censor_recall"] > 0.99
    assert metrics["triad"]["observable_opportunity_retention"] > 0.70


def test_support_loss_slice_exposes_false_absence_problem() -> None:
    world = generate_world(140318, 300)
    target = diagnostic_slice(world, "target_only", "support_loss_low_target")
    two_axis = diagnostic_slice(world, "target_plus_nuisance", "support_loss_low_target")
    triad = diagnostic_slice(world, "triad", "support_loss_low_target")

    assert target["false_absence_rate"] > 0.80
    assert two_axis["false_absence_rate"] > 0.80
    assert triad["false_absence_rate"] < 0.01
    assert triad["censor_rate"] > 0.99


def test_full_metric_set_remains_multiobjective() -> None:
    metrics = asdict(evaluate_policy("triad", generate_world(140319, 20)))
    assert set(metrics) == {
        "policy",
        "false_absence_rate_among_true_visits",
        "false_positive_candidate_rate_among_true_absences",
        "unobservable_denominator_contamination",
        "observable_opportunity_retention",
        "observable_true_visit_candidate_recall",
        "unobservable_censor_recall",
    }
