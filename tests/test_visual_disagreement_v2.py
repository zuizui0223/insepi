from interaction_sensing.simulation.visual_disagreement_v2 import (
    compare_visual_traces,
    observable_disagreement_priority,
)


def test_priority_uses_observable_outputs_only():
    kind, score = observable_disagreement_priority(
        "no_activity",
        "audit_priority",
        false_event_risk=0.2,
        missed_event_risk=0.85,
        attribution_risk=0.1,
    )
    assert kind == "absence_vs_high_missed_risk"
    assert score == 0.98


def test_visual_trace_comparator_separates_priority_from_latent_evaluation():
    p = [{
        "schema": "pollipi-insepi-visual-contradiction-v2",
        "scenario_id": "x",
        "true_visit": True,
        "pollipi_state": "no_activity",
    }]
    i = [{
        "schema": "pollipi-insepi-visual-contradiction-v2",
        "scenario_id": "x",
        "true_visit": True,
        "inferred_noise_source": "blur_or_focus_loss",
        "observability_state": "audit_priority",
        "false_event_risk": 0.2,
        "missed_event_risk": 0.8,
        "attribution_risk": 0.0,
    }]
    row = compare_visual_traces(p, i)[0]
    assert row.observable_priority == 0.98
    assert row.latent_error == "missed_visit"
