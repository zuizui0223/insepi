"""Semantic clarification layer for the locked V14b ternary surface.

This module does not alter the frozen V14b observers, thresholds, alpha, seeds,
world generator, or decisions.  It only gives scientifically safer names and
identification statements to outputs already produced by the locked surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ternary_decision_v14b import TernaryDecisionV14b, UndeterminedReason


class ClarifiedUndeterminedReason(str, Enum):
    NONE = "none"
    NO_SUPPORTED_EVIDENCE = "no_supported_evidence"
    OVERLAP_OR_ATTRIBUTION = "overlap_or_attribution"


def clarified_reason(decision: TernaryDecisionV14b) -> ClarifiedUndeterminedReason:
    """Translate the locked V14b reason without strengthening its causal meaning.

    V14b's historical ``INFORMATION_ABSENT`` label means only that the frozen
    target and nuisance observers produced no safe positive support.  That fact
    alone cannot distinguish true information absence from a representation or
    model limitation, so V14c names it ``NO_SUPPORTED_EVIDENCE``.
    """
    if decision.reason is UndeterminedReason.NONE:
        return ClarifiedUndeterminedReason.NONE
    if decision.reason is UndeterminedReason.INFORMATION_ABSENT:
        return ClarifiedUndeterminedReason.NO_SUPPORTED_EVIDENCE
    if decision.reason is UndeterminedReason.OVERLAP_OR_ATTRIBUTION:
        return ClarifiedUndeterminedReason.OVERLAP_OR_ATTRIBUTION
    raise ValueError(f"unexpected V14b reason: {decision.reason!r}")


@dataclass(frozen=True, slots=True)
class VisitPresenceBounds:
    lower: float
    upper: float
    width: float
    absence_certifying_channel_available: bool


def visit_presence_bounds(
    *,
    target_supported_rate: float,
    certified_target_absence_rate: float | None = None,
) -> VisitPresenceBounds:
    """Return logically valid prevalence bounds from positive/negative evidence.

    The frozen V14b target observer is positive-only: TARGET safely certifies
    target presence, but BASELINE, NUISANCE and U do not certify target absence.
    Without an independent absence-certifying channel, the safe upper bound is 1.
    If such a channel is supplied in a later generation, the upper bound becomes
    ``1 - certified_target_absence_rate``.
    """
    if not 0.0 <= target_supported_rate <= 1.0:
        raise ValueError("target_supported_rate must lie in [0,1]")
    if certified_target_absence_rate is None:
        upper = 1.0
        absence_available = False
    else:
        if not 0.0 <= certified_target_absence_rate <= 1.0:
            raise ValueError("certified_target_absence_rate must lie in [0,1]")
        upper = 1.0 - certified_target_absence_rate
        absence_available = True
    lower = target_supported_rate
    if lower > upper + 1e-12:
        raise ValueError("presence and certified-absence rates imply inconsistent bounds")
    return VisitPresenceBounds(
        lower=lower,
        upper=upper,
        width=upper - lower,
        absence_certifying_channel_available=absence_available,
    )


def legacy_non_target_decision_width(*, baseline_rate: float, undetermined_rate: float) -> float:
    """Return the historical V14b ``baseline + U`` descriptive quantity.

    This is retained for provenance only.  It is *not* a target-presence partial-
    identification width because NUISANCE does not certify target absence.
    """
    for value in (baseline_rate, undetermined_rate):
        if not 0.0 <= value <= 1.0:
            raise ValueError("rates must lie in [0,1]")
    width = baseline_rate + undetermined_rate
    if width > 1.0 + 1e-12:
        raise ValueError("baseline_rate + undetermined_rate cannot exceed 1")
    return width


PI3_CLAIM_BOUNDARY = (
    "In V14b the target rule is structural: direct_target_signal_fraction > 0 "
    "is sufficient for target support in the closed generator. Therefore the strong "
    "Pi3=0 versus Pi3>0 boundary is a consequence of direct-channel availability "
    "under this observer, not evidence that positive direct-signal amplitude is "
    "universally irrelevant."
)
