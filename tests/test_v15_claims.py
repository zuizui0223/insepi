import pytest

from interaction_sensing.v15_claims import (
    ClaimDecision,
    ClaimDirection,
    ClaimFamily,
    ClaimThreshold,
    HeldOutMetricInterval,
    evaluate_claim,
)


def interval(metric: str, estimate: float, lower: float, upper: float) -> HeldOutMetricInterval:
    return HeldOutMetricInterval(metric, estimate, lower, upper, 0.95)


def test_point_estimate_alone_cannot_authorize_at_least_claim() -> None:
    threshold = ClaimThreshold(
        "recall",
        ClaimFamily.TARGET_PRESENCE,
        "visit_recall",
        ClaimDirection.AT_LEAST,
        0.80,
    )
    result = interval("visit_recall", 0.85, 0.76, 0.90)
    evaluation = evaluate_claim(threshold, result, prefreeze_ready=True)
    assert evaluation.decision is ClaimDecision.INCONCLUSIVE
    assert not evaluation.supported


def test_at_least_claim_requires_lower_bound_to_cross_threshold() -> None:
    threshold = ClaimThreshold(
        "recall",
        ClaimFamily.TARGET_PRESENCE,
        "visit_recall",
        ClaimDirection.AT_LEAST,
        0.80,
    )
    supported = evaluate_claim(threshold, interval("visit_recall", 0.88, 0.82, 0.92), prefreeze_ready=True)
    failed = evaluate_claim(threshold, interval("visit_recall", 0.70, 0.62, 0.75), prefreeze_ready=True)
    assert supported.decision is ClaimDecision.SUPPORTED
    assert supported.decisive_bound == 0.82
    assert failed.decision is ClaimDecision.NOT_SUPPORTED


def test_at_most_claim_requires_upper_bound_to_cross_threshold() -> None:
    threshold = ClaimThreshold(
        "fpr",
        ClaimFamily.TARGET_PRESENCE,
        "candidate_fpr",
        ClaimDirection.AT_MOST,
        0.10,
    )
    supported = evaluate_claim(threshold, interval("candidate_fpr", 0.04, 0.02, 0.08), prefreeze_ready=True)
    inconclusive = evaluate_claim(threshold, interval("candidate_fpr", 0.08, 0.04, 0.13), prefreeze_ready=True)
    failed = evaluate_claim(threshold, interval("candidate_fpr", 0.18, 0.14, 0.22), prefreeze_ready=True)
    assert supported.decision is ClaimDecision.SUPPORTED
    assert supported.decisive_bound == 0.08
    assert inconclusive.decision is ClaimDecision.INCONCLUSIVE
    assert failed.decision is ClaimDecision.NOT_SUPPORTED


def test_prefreeze_not_ready_makes_claim_not_evaluable() -> None:
    threshold = ClaimThreshold(
        "recall",
        ClaimFamily.TARGET_PRESENCE,
        "visit_recall",
        ClaimDirection.AT_LEAST,
        0.80,
    )
    evaluation = evaluate_claim(threshold, interval("visit_recall", 0.95, 0.90, 0.98), prefreeze_ready=False)
    assert evaluation.decision is ClaimDecision.NOT_EVALUABLE


def test_absence_claim_requires_independent_A_minus_even_when_interval_is_favorable() -> None:
    threshold = ClaimThreshold(
        "absence-error",
        ClaimFamily.TARGET_ABSENCE,
        "false_certified_absence_rate",
        ClaimDirection.AT_MOST,
        0.05,
        requires_a_minus=True,
    )
    result = interval("false_certified_absence_rate", 0.01, 0.0, 0.03)
    blocked = evaluate_claim(threshold, result, prefreeze_ready=True, a_minus_validated=False)
    allowed = evaluate_claim(threshold, result, prefreeze_ready=True, a_minus_validated=True)
    assert blocked.decision is ClaimDecision.NOT_EVALUABLE
    assert allowed.decision is ClaimDecision.SUPPORTED


def test_absence_family_cannot_omit_A_minus_prerequisite() -> None:
    with pytest.raises(ValueError, match="must require"):
        ClaimThreshold(
            "bad-absence",
            ClaimFamily.TARGET_ABSENCE,
            "false_absence_rate",
            ClaimDirection.AT_MOST,
            0.05,
        )


def test_claim_metric_mismatch_fails_closed() -> None:
    threshold = ClaimThreshold(
        "recall",
        ClaimFamily.TARGET_PRESENCE,
        "visit_recall",
        ClaimDirection.AT_LEAST,
        0.80,
    )
    with pytest.raises(ValueError, match="metric mismatch"):
        evaluate_claim(threshold, interval("different_metric", 0.9, 0.8, 1.0), prefreeze_ready=True)
