"""Pre-data claim authorization for V15-v2.

This module deliberately does not contain default scientific thresholds.  A claim
may be evaluated only against a threshold that was fixed before held-out scoring.
Point estimates alone never authorize a claim: the relevant held-out confidence
bound must cross the frozen threshold in the predeclared direction.

Target-absence claims have an additional prerequisite.  They are not evaluable
unless an independently validated ``A-`` channel exists; good observation support
and a low positive-target score are insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimDirection(str, Enum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"


class ClaimFamily(str, Enum):
    TARGET_PRESENCE = "target_presence"
    OBSERVATION_SUPPORT = "observation_support"
    NUISANCE_DIAGNOSTIC = "nuisance_diagnostic"
    COUPLED_RESCUE = "coupled_rescue"
    SYSTEM_COMPARISON = "system_comparison"
    TARGET_ABSENCE = "target_absence"


class ClaimDecision(str, Enum):
    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    INCONCLUSIVE = "inconclusive"
    NOT_EVALUABLE = "not_evaluable"


@dataclass(frozen=True, slots=True)
class ClaimThreshold:
    claim_id: str
    family: ClaimFamily
    metric: str
    direction: ClaimDirection
    threshold: float
    requires_a_minus: bool = False
    interpretation: str = ""

    def __post_init__(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id cannot be empty")
        if not self.metric.strip():
            raise ValueError("metric cannot be empty")
        if not isinstance(self.threshold, (int, float)):
            raise TypeError("claim threshold must be numeric")
        if self.family is ClaimFamily.TARGET_ABSENCE and not self.requires_a_minus:
            raise ValueError("target-absence claims must require independently validated A_minus")
        if self.requires_a_minus and self.family is not ClaimFamily.TARGET_ABSENCE:
            raise ValueError("A_minus prerequisite is reserved for target-absence claims")


@dataclass(frozen=True, slots=True)
class HeldOutMetricInterval:
    metric: str
    estimate: float
    lower: float
    upper: float
    confidence_level: float

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("metric cannot be empty")
        if self.lower > self.estimate or self.estimate > self.upper:
            raise ValueError("held-out interval must satisfy lower <= estimate <= upper")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must lie in (0, 1)")


@dataclass(frozen=True, slots=True)
class ClaimEvaluation:
    claim_id: str
    decision: ClaimDecision
    metric: str
    threshold: float
    direction: ClaimDirection
    decisive_bound: float | None
    reason: str

    @property
    def supported(self) -> bool:
        return self.decision is ClaimDecision.SUPPORTED


def evaluate_claim(
    threshold: ClaimThreshold,
    result: HeldOutMetricInterval,
    *,
    prefreeze_ready: bool,
    a_minus_validated: bool = False,
) -> ClaimEvaluation:
    """Evaluate one frozen claim without using the point estimate as the gate.

    ``prefreeze_ready`` must be the output of the held-out readiness gate, not a
    local convenience flag.  If the design was not frozen before held-out use,
    scientific claim evaluation is refused.
    """

    if result.metric != threshold.metric:
        raise ValueError("claim threshold/result metric mismatch")

    if not prefreeze_ready:
        return ClaimEvaluation(
            claim_id=threshold.claim_id,
            decision=ClaimDecision.NOT_EVALUABLE,
            metric=threshold.metric,
            threshold=float(threshold.threshold),
            direction=threshold.direction,
            decisive_bound=None,
            reason="V15 prefreeze readiness gate was not READY before held-out scoring",
        )

    if threshold.requires_a_minus and not a_minus_validated:
        return ClaimEvaluation(
            claim_id=threshold.claim_id,
            decision=ClaimDecision.NOT_EVALUABLE,
            metric=threshold.metric,
            threshold=float(threshold.threshold),
            direction=threshold.direction,
            decisive_bound=None,
            reason="target-absence claim requires independently validated A_minus",
        )

    if threshold.direction is ClaimDirection.AT_LEAST:
        if result.lower >= threshold.threshold:
            decision = ClaimDecision.SUPPORTED
            reason = "held-out lower confidence bound meets or exceeds frozen threshold"
        elif result.upper < threshold.threshold:
            decision = ClaimDecision.NOT_SUPPORTED
            reason = "held-out upper confidence bound remains below frozen threshold"
        else:
            decision = ClaimDecision.INCONCLUSIVE
            reason = "held-out interval overlaps frozen threshold"
        decisive_bound = result.lower
    else:
        if result.upper <= threshold.threshold:
            decision = ClaimDecision.SUPPORTED
            reason = "held-out upper confidence bound is at or below frozen threshold"
        elif result.lower > threshold.threshold:
            decision = ClaimDecision.NOT_SUPPORTED
            reason = "held-out lower confidence bound remains above frozen threshold"
        else:
            decision = ClaimDecision.INCONCLUSIVE
            reason = "held-out interval overlaps frozen threshold"
        decisive_bound = result.upper

    return ClaimEvaluation(
        claim_id=threshold.claim_id,
        decision=decision,
        metric=threshold.metric,
        threshold=float(threshold.threshold),
        direction=threshold.direction,
        decisive_bound=float(decisive_bound),
        reason=reason,
    )
