import json

from interaction_sensing.simulation.contradiction import (
    CONTRADICTION_SCHEMA,
    CONTRAST_SCENARIOS,
    run_contradiction_scenarios,
    write_contradiction_trace_jsonl,
)
from interaction_sensing.simulation.disagreement import (
    compare_traces,
    summarize_disagreements,
)


def _insepi_by_id():
    return {row.scenario_id: row for row in run_contradiction_scenarios()}


def _pollipi_fixture():
    # Expected states from PolliPi's independent contradiction-v1 trace.  This is
    # a contract fixture, not an import: the repositories remain independently
    # executable and divergence becomes a visible benchmark failure/update.
    states = {
        "quiet_absence": "no_activity",
        "clean_visit": "strong_visitation_candidate",
        "wind_absence": "environmental_noise",
        "wind_visit": "environmental_noise",
        "shake_absence": "environmental_noise",
        "shake_visit": "environmental_noise",
        "shadow_absence": "environmental_noise",
        "shadow_visit": "environmental_noise",
        "occluded_visit": "uncertain_local_activity",
        "blurred_visit": "uncertain_local_activity",
        "clutter_visit": "environmental_noise",
        "unknown_visit": "uncertain_local_activity",
    }
    return [
        {
            "schema": CONTRADICTION_SCHEMA,
            "scenario_id": scenario.scenario_id,
            "true_visit": scenario.true_visit,
            "noise_source": scenario.noise_source.value,
            "pollipi_state": states[scenario.scenario_id],
        }
        for scenario in CONTRAST_SCENARIOS
    ]


def test_noise_first_policy_keeps_clean_windows_clean_and_disturbances_visible():
    rows = _insepi_by_id()
    assert rows["quiet_absence"].observability_state == "clean"
    assert rows["clean_visit"].observability_state == "clean"

    for scenario_id in (
        "wind_visit",
        "shake_visit",
        "shadow_visit",
        "occluded_visit",
        "blurred_visit",
        "clutter_visit",
    ):
        assert rows[scenario_id].observability_state == "audit_priority"
        assert rows[scenario_id].capture_audit is True
        assert rows[scenario_id].record_high_resolution_context is True


def test_same_true_visit_can_be_suppressed_by_pollipi_but_audit_prioritized_by_insepi():
    insepi_rows = [row.to_dict() for row in run_contradiction_scenarios()]
    compared = {row.scenario_id: row for row in compare_traces(_pollipi_fixture(), insepi_rows)}

    for scenario_id in ("wind_visit", "shake_visit", "shadow_visit", "clutter_visit"):
        row = compared[scenario_id]
        assert row.true_visit is True
        assert row.category == "visit_suppressed_where_observation_is_risky"
        assert row.disagreement_score == 1.0
        assert row.requires_audit is True


def test_occlusion_and_blur_create_candidate_vs_observability_tension():
    insepi_rows = [row.to_dict() for row in run_contradiction_scenarios()]
    compared = {row.scenario_id: row for row in compare_traces(_pollipi_fixture(), insepi_rows)}
    assert compared["occluded_visit"].category == "candidate_requires_audit"
    assert compared["blurred_visit"].category == "candidate_requires_audit"


def test_benchmark_summary_exposes_high_disagreement_cases():
    insepi_rows = [row.to_dict() for row in run_contradiction_scenarios()]
    summary = summarize_disagreements(compare_traces(_pollipi_fixture(), insepi_rows))
    assert summary["n_scenarios"] == 12
    assert summary["n_high_disagreement"] == 6
    assert summary["by_category"]["visit_suppressed_where_observation_is_risky"] == 4
    assert summary["by_category"]["candidate_requires_audit"] == 2


def test_trace_is_portable_jsonl(tmp_path):
    output = write_contradiction_trace_jsonl(tmp_path / "insepi.jsonl")
    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(records) == len(CONTRAST_SCENARIOS)
    assert records[0]["schema"] == CONTRADICTION_SCHEMA
