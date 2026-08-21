from pathlib import Path

from interaction_sensing.simulation.portfolio_development_v6 import (
    DevelopmentResult,
    mark_pareto,
    read_pollipi_v4_tsv,
)
from interaction_sensing.simulation.factorial_world_v4 import suite_fingerprint


SNAPSHOT = Path("benchmarks/pollipi_factorial_v4_5541201.tsv")


def _row(method, event, error, cost, tv):
    return DevelopmentResult(
        method=method,
        prevalence=0.5,
        budget_fraction=0.25,
        true_event_recall=event,
        hidden_error_recall=error,
        captures_per_hidden_error=cost,
        disturbance_tv_distance=tv,
        false_event_audit_yield=0.0,
        missed_event_audit_yield=0.0,
        attribution_audit_yield=0.0,
    )


def test_compact_pollipi_snapshot_has_provenance_and_all_rows():
    provenance, rows = read_pollipi_v4_tsv(SNAPSHOT)
    assert provenance["source_commit"] == "5541201b376689c32aaabeafbc8e7e9592150d23"
    assert provenance["world_fingerprint"] == suite_fingerprint()
    assert len(rows) == 120
    assert {row["split"] for row in rows} == {"calibration", "test"}


def test_pareto_marks_dominated_method_off_frontier():
    dominant = _row("dominant", 0.7, 0.8, 1.5, 0.2)
    dominated = _row("dominated", 0.6, 0.7, 2.0, 0.3)
    tradeoff = _row("tradeoff", 0.9, 0.5, 1.2, 0.1)
    marked = {row.method: row for row in mark_pareto([dominant, dominated, tradeoff])}
    assert marked["dominant"].pareto is True
    assert marked["tradeoff"].pareto is True
    assert marked["dominated"].pareto is False
