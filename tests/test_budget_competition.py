from interaction_sensing.simulation.budget_competition import (
    CORE_POLICIES,
    SINGLE_VIEW_ABLATIONS,
    allocation_score,
    run_budget_competition,
)


def _traces():
    pollipi = [
        {"scenario_id": "clean_visit", "true_visit": True, "noise_source": "stable_scene", "pollipi_state": "strong_visitation_candidate"},
        {"scenario_id": "wind_visit", "true_visit": True, "noise_source": "background_vegetation_motion", "pollipi_state": "environmental_noise"},
        {"scenario_id": "clutter_visit", "true_visit": True, "noise_source": "multi_object_clutter", "pollipi_state": "environmental_noise"},
        {"scenario_id": "quiet_absence", "true_visit": False, "noise_source": "stable_scene", "pollipi_state": "no_activity"},
    ]
    insepi = [
        {"scenario_id": "clean_visit", "true_visit": True, "noise_source": "stable_scene", "observability_state": "clean", "false_event_risk": 0.0, "missed_event_risk": 0.0, "attribution_risk": 0.0},
        {"scenario_id": "wind_visit", "true_visit": True, "noise_source": "background_vegetation_motion", "observability_state": "audit_priority", "false_event_risk": 0.70, "missed_event_risk": 0.25, "attribution_risk": 0.40},
        {"scenario_id": "clutter_visit", "true_visit": True, "noise_source": "multi_object_clutter", "observability_state": "audit_priority", "false_event_risk": 0.30, "missed_event_risk": 0.0, "attribution_risk": 0.85},
        {"scenario_id": "quiet_absence", "true_visit": False, "noise_source": "stable_scene", "observability_state": "clean", "false_event_risk": 0.0, "missed_event_risk": 0.0, "attribution_risk": 0.0},
    ]
    return pollipi, insepi


def test_allocation_score_never_depends_on_hidden_truth():
    p, i = _traces()
    original = allocation_score("disagreement", p[1], i[1])
    p_changed = dict(p[1], true_visit=False)
    i_changed = dict(i[1], true_visit=False)
    assert allocation_score("disagreement", p_changed, i_changed) == original


def test_equal_budget_competition_is_reproducible_and_equal_cost():
    p, i = _traces()
    first = run_budget_competition(p, i, world_windows=300, replicates=8, seed=7)
    second = run_budget_competition(p, i, world_windows=300, replicates=8, seed=7)
    assert [row.to_dict() for row in first] == [row.to_dict() for row in second]
    assert len({row.selected for row in first}) == 1
    assert {row.policy for row in first} == {
        "uniform", "pollipi_candidate", "insepi_audit", "union", "intersection", "disagreement"
    }


def test_single_view_ablations_remove_the_other_observer():
    p, i = _traces()
    pollipi_only = allocation_score("disagreement_pollipi_only", p[0], i[0])
    changed_risks = dict(i[0], false_event_risk=1.0, missed_event_risk=1.0, attribution_risk=1.0)
    assert allocation_score("disagreement_pollipi_only", p[0], changed_risks) == pollipi_only

    insepi_only = allocation_score("disagreement_insepi_only", p[1], i[1])
    changed_state = dict(p[1], pollipi_state="strong_visitation_candidate")
    assert allocation_score("disagreement_insepi_only", changed_state, i[1]) == insepi_only

    results = run_budget_competition(
        p,
        i,
        policies=CORE_POLICIES + SINGLE_VIEW_ABLATIONS,
        world_windows=100,
        replicates=2,
        seed=11,
    )
    assert {row.policy for row in results} >= set(SINGLE_VIEW_ABLATIONS)
