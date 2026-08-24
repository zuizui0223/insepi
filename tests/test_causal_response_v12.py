from __future__ import annotations

import pytest

from interaction_sensing.causal_response_v12 import ObserverOutput, estimate_factorial_responses
from interaction_sensing.physical_validation_v12 import PhysicalBlock, build_trial_plan

SEED = "cd" * 32


def small_plan():
    return build_trial_plan(
        seed_hex=SEED,
        blocks=[
            PhysicalBlock("day1", "cam1", "sceneA"),
            PhysicalBlock("day2", "cam1", "sceneB"),
        ],
        heldout_block_ids={"day2|cam1|sceneB"},
        disturbance_families=("wind_like",),
        intensity_labels=("mid",),
        replicates_per_cell=3,
    )


def test_v12_factorial_response_recovers_known_main_and_interaction_effects() -> None:
    trials = small_plan()
    outputs = []
    for trial in trials:
        e = trial.event_intervention
        d = trial.disturbance_intervention
        # evidence = .10 + .40 E - .08 D - .12 E*D
        # observability = .15 + .03 E + .50 D + .06 E*D
        evidence = 0.10 + 0.40 * e - 0.08 * d - 0.12 * e * d
        observability = 0.15 + 0.03 * e + 0.50 * d + 0.06 * e * d
        outputs.append(ObserverOutput(trial.trial_id, evidence, observability))
    responses = estimate_factorial_responses(trials, outputs)
    assert len(responses) == 2
    for row in responses:
        # Factorial main effects average over the other factor, so coefficient + half interaction.
        assert row.event_effect_on_evidence == pytest.approx(0.40 - 0.06)
        assert row.disturbance_effect_on_evidence == pytest.approx(-0.08 - 0.06)
        assert row.interaction_on_evidence == pytest.approx(-0.12)
        assert row.event_effect_on_observability == pytest.approx(0.03 + 0.03)
        assert row.disturbance_effect_on_observability == pytest.approx(0.50 + 0.03)
        assert row.interaction_on_observability == pytest.approx(0.06)
        assert row.response_matrix == (
            (row.event_effect_on_evidence, row.disturbance_effect_on_evidence),
            (row.event_effect_on_observability, row.disturbance_effect_on_observability),
        )


def test_v12_response_estimator_refuses_missing_or_extra_truth_output_join() -> None:
    trials = small_plan()
    outputs = [ObserverOutput(trial.trial_id, 0.2, 0.3) for trial in trials[:-1]]
    with pytest.raises(ValueError, match="identical trial ids"):
        estimate_factorial_responses(trials, outputs)


def test_v12_response_estimator_refuses_unbalanced_factorial_cells() -> None:
    trials = list(small_plan())
    heldout = [trial for trial in trials if trial.split == "heldout"]
    development = [trial for trial in trials if trial.split == "development"]
    # Drop one development trial but retain its output-set equality: grouping must detect imbalance.
    reduced = development[:-1] + heldout
    outputs = [ObserverOutput(trial.trial_id, 0.2, 0.3) for trial in reduced]
    with pytest.raises(RuntimeError, match="unbalanced or incomplete"):
        estimate_factorial_responses(reduced, outputs)


def test_v12_outputs_keep_evidence_and_observability_as_separate_fields() -> None:
    row = ObserverOutput("trial", 0.6, 0.4)
    assert row.evidence == 0.6
    assert row.observability == 0.4
    assert not hasattr(row, "winner_score")
    assert not hasattr(row, "disagreement_score")
