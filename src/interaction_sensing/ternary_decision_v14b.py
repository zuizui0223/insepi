"""Frozen V14b baseline + ternary decision layer.

This module combines the independently frozen target and nuisance observers only
at the decision layer. It never changes either observer representation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .nuisance_observer_v14b import NuisanceObservationV14b
from .target_observer_v14b import TargetObservationV14b


class TernaryState(str, Enum):
    BASELINE = "baseline"
    TARGET = "target"
    NUISANCE = "nuisance"
    UNDETERMINED = "undetermined"


class UndeterminedReason(str, Enum):
    NONE = "none"
    INFORMATION_ABSENT = "information_absent"
    OVERLAP_OR_ATTRIBUTION = "overlap_or_attribution"


@dataclass(frozen=True, slots=True)
class TernaryDecisionV14b:
    state: TernaryState
    reason: UndeterminedReason
    target_supported: bool
    nuisance_supported: bool
    dynamic_gate: bool


def decide_v14b(
    target: TargetObservationV14b,
    nuisance: NuisanceObservationV14b,
    *,
    nuisance_threshold: float,
    minimum_nuisance_observation_support: float = 0.20,
) -> TernaryDecisionV14b:
    """Return baseline or one of the three deviation-side decisions.

    The dynamic gate is observation-side: any direct actor signal, local focal
    response, or nuisance-process signature triggers the attribution question.
    Simultaneous positive T and N evidence is preserved as a legitimate latent
    superposition but maps to U at the *exclusive attribution* layer.
    """
    if nuisance_threshold < 0:
        raise ValueError("nuisance_threshold must be non-negative")
    if not 0 <= minimum_nuisance_observation_support <= 1:
        raise ValueError("minimum_nuisance_observation_support must lie in [0,1]")

    t = bool(target.target_supported)
    n = bool(
        nuisance.nuisance_process_support >= nuisance_threshold
        and nuisance.nuisance_observation_support >= minimum_nuisance_observation_support
    )
    dynamic = bool(
        target.direct_signal_fraction > 0.0
        or target.local_response_fraction > 0.0
        or nuisance.nuisance_process_support > 0.0
    )

    if not dynamic:
        return TernaryDecisionV14b(TernaryState.BASELINE, UndeterminedReason.NONE, t, n, False)
    if t and n:
        return TernaryDecisionV14b(TernaryState.UNDETERMINED, UndeterminedReason.OVERLAP_OR_ATTRIBUTION, t, n, True)
    if t:
        return TernaryDecisionV14b(TernaryState.TARGET, UndeterminedReason.NONE, t, n, True)
    if n:
        return TernaryDecisionV14b(TernaryState.NUISANCE, UndeterminedReason.NONE, t, n, True)
    if target.unresolved_indirect_only:
        return TernaryDecisionV14b(TernaryState.UNDETERMINED, UndeterminedReason.OVERLAP_OR_ATTRIBUTION, t, n, True)
    return TernaryDecisionV14b(TernaryState.UNDETERMINED, UndeterminedReason.INFORMATION_ABSENT, t, n, True)
