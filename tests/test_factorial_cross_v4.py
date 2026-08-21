import json

import pytest

from interaction_sensing.simulation.budget_competition import BudgetResult
from interaction_sensing.simulation.factorial_cross_v4 import (
    _validate_and_select_rows,
    dominates,
    pareto_frontier,
    read_pollipi_factorial_trace,
)
from interaction_sensing.simulation.factorial_world_v4 import suite_fingerprint


def _write_trace(path, fingerprint):
    records = [
        {
            "record_type": "provenance",
            "schema": "pollipi-insepi-factorial-v4",
            "world_fingerprint": fingerprint,
            "source_commit": "abc123",
        },
        {
            "record_type": "result",
            "schema": "pollipi-insepi-factorial-v4",
            "condition_id": "test-clean-101-0",
            "split": "test",
            "true_visit": False,
            "disturbance_family": "clean",
            "pollipi_state": "no_activity",
            "pollipi_reason": "below_active_cell_threshold",
        },
    ]
    path.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")


def test_pollipi_factorial_trace_accepts_matching_world(tmp_path):
    path = tmp_path / "trace.jsonl"
    _write_trace(path, suite_fingerprint())
    provenance, rows = read_pollipi_factorial_trace(path)
    assert provenance["source_commit"] == "abc123"
    assert len(rows) == 1
    assert rows[0]["condition_id"] == "test-clean-101-0"


def test_pollipi_factorial_trace_rejects_world_mismatch(tmp_path):
    path = tmp_path / "trace.jsonl"
    _write_trace(path, "0" * 64)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        read_pollipi_factorial_trace(path)


def test_trace_alignment_is_fail_closed_and_selects_test_only():
    common = {
        "schema": "pollipi-insepi-factorial-v4",
        "true_visit": False,
        "disturbance_family": "clean",
    }
    pollipi = [
        dict(common, condition_id="cal", split="calibration", pollipi_state="no_activity"),
        dict(common, condition_id="test", split="test", pollipi_state="no_activity"),
    ]
    insepi = [
        dict(common, condition_id="cal", split="calibration", observability_state="clean"),
        dict(common, condition_id="test", split="test", observability_state="clean"),
    ]
    selected_pollipi, selected_insepi = _validate_and_select_rows(
        pollipi, insepi, evaluation_split="test"
    )
    assert [row["condition_id"] for row in selected_pollipi] == ["test"]
    assert [row["condition_id"] for row in selected_insepi] == ["test"]

    with pytest.raises(ValueError, match="duplicate PolliPi"):
        _validate_and_select_rows(pollipi + [pollipi[1]], insepi, evaluation_split="test")

    mismatched = [dict(insepi[0]), dict(insepi[1], true_visit=True)]
    with pytest.raises(ValueError, match="true_visit mismatch"):
        _validate_and_select_rows(pollipi, mismatched, evaluation_split="test")


def _budget_result(policy, *, event, hidden, missed, captures, tv):
    return BudgetResult(
        policy=policy,
        budget_fraction=0.25,
        windows=100,
        selected=25,
        true_event_recall=event,
        hidden_error_recall=hidden,
        missed_event_audit_yield=missed,
        false_event_audit_yield=0.0,
        attribution_audit_yield=0.0,
        captures_per_hidden_error=captures,
        disturbance_tv_distance=tv,
    )


def test_pareto_frontier_reports_dominance_without_scalarising_endpoints():
    dominant = _budget_result("dominant", event=0.8, hidden=0.7, missed=0.6, captures=1.0, tv=0.1)
    dominated = _budget_result("dominated", event=0.7, hidden=0.6, missed=0.5, captures=1.2, tv=0.2)
    tradeoff = _budget_result("tradeoff", event=0.6, hidden=0.8, missed=0.7, captures=0.9, tv=0.3)
    assert dominates(dominant, dominated)
    assert pareto_frontier((dominant, dominated, tradeoff)) == ("dominant", "tradeoff")
