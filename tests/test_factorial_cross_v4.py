import json

import pytest

from interaction_sensing.simulation.factorial_cross_v4 import read_pollipi_factorial_trace
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
