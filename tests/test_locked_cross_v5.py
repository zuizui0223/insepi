from interaction_sensing.simulation.budget_competition import BudgetResult
from interaction_sensing.simulation.locked_cross_v5 import (
    LockedGridPoint,
    evaluate_family_support_gate,
    evaluate_scarce_budget_gate,
)


def _result(policy, *, hidden, missed, event=0.5, captures=2.0, tv=0.4):
    return BudgetResult(
        policy=policy,
        budget_fraction=0.1,
        windows=100,
        selected=10,
        true_event_recall=event,
        hidden_error_recall=hidden,
        missed_event_audit_yield=missed,
        false_event_audit_yield=0.0,
        attribution_audit_yield=0.0,
        captures_per_hidden_error=captures,
        disturbance_tv_distance=tv,
    )


def _passing_point(regime, budget):
    results = (
        _result("union", hidden=0.4, missed=0.3),
        _result("intersection", hidden=0.35, missed=0.35),
        _result("disagreement", hidden=0.6, missed=0.7, captures=1.5),
        _result("disagreement_pollipi_only", hidden=0.45, missed=0.4),
        _result("disagreement_insepi_only", hidden=0.5, missed=0.5),
    )
    return LockedGridPoint(regime, budget, results, ("disagreement",))


def test_locked_gate_requires_every_prevalence_and_scarce_budget():
    points = tuple(
        _passing_point(regime, budget)
        for regime in ("rare", "balanced", "common")
        for budget in (0.1, 0.25)
    )
    assert evaluate_scarce_budget_gate(points) == ("pass", ())


def test_locked_gate_fails_instead_of_inviting_v5_tuning():
    points = [
        _passing_point(regime, budget)
        for regime in ("rare", "balanced", "common")
        for budget in (0.1, 0.25)
    ]
    failed = points[0]
    results = tuple(
        _result(row.policy, hidden=(0.3 if row.policy == "disagreement" else row.hidden_error_recall), missed=row.missed_event_audit_yield)
        for row in failed.results
    )
    points[0] = LockedGridPoint(failed.prevalence_regime, failed.budget_fraction, results, ())
    status, failures = evaluate_scarce_budget_gate(points)
    assert status == "fail"
    assert any("off the central Pareto frontier" in failure for failure in failures)
    assert any("no hidden-error gain" in failure for failure in failures)


def test_family_support_gate_rejects_single_family_explanation():
    failures = evaluate_family_support_gate({
        "rare": ("occlusion",),
        "balanced": ("occlusion", "smear"),
        "common": ("lens", "shadow"),
    })
    assert len(failures) == 1
    assert failures[0].startswith("rare:")
