"""Separate direct-insect and target-coupled evidence routes for visit sensing.

A visit-focused observer need not rely only on visible insect pixels. A focal
insect can also leave a local response in the biological target (for example,
flower displacement after contact). That response is not exogenous nuisance by
definition, but neither is every flower motion evidence of an insect.

This module therefore preserves two target-side routes before any nuisance
comparison:

- direct route: evidence for the insect/actor itself;
- coupled route: evidence for a local target response attributed to the actor.

Nuisance outputs are deliberately not inputs here. The later triad is where
independent target and nuisance hypotheses are compared.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observation_triad import TargetEvidence


class TargetEvidenceRoute(str, Enum):
    NONE = "none"
    DIRECT = "direct"
    COUPLED = "coupled"
    BOTH = "both"
    INTERMEDIATE = "intermediate"


@dataclass(frozen=True, slots=True)
class TargetRouteEvidence:
    """Target-focused evidence that preserves direct and indirect routes.

    `coupled_response_score` measures a local response at the focal target.
    `target_link_confidence` measures whether that local response is attributable
    to the focal actor/interaction rather than arbitrary scene motion. Their
    product is the usable coupled target route.
    """

    direct_insect_score: float
    coupled_response_score: float
    target_link_confidence: float
    source_state: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("direct_insect_score", self.direct_insect_score),
            ("coupled_response_score", self.coupled_response_score),
            ("target_link_confidence", self.target_link_confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    @property
    def coupled_target_score(self) -> float:
        return self.coupled_response_score * self.target_link_confidence

    @property
    def aggregate_score(self) -> float:
        """Conservative OR across independently retained target-side routes."""

        return max(self.direct_insect_score, self.coupled_target_score)

    def route(self, *, high_threshold: float = 0.65, low_threshold: float = 0.25) -> TargetEvidenceRoute:
        if not 0.0 <= low_threshold < high_threshold <= 1.0:
            raise ValueError("require 0 <= low_threshold < high_threshold <= 1")
        direct = self.direct_insect_score >= high_threshold
        coupled = self.coupled_target_score >= high_threshold
        if direct and coupled:
            return TargetEvidenceRoute.BOTH
        if direct:
            return TargetEvidenceRoute.DIRECT
        if coupled:
            return TargetEvidenceRoute.COUPLED
        if self.aggregate_score <= low_threshold:
            return TargetEvidenceRoute.NONE
        return TargetEvidenceRoute.INTERMEDIATE

    def to_target_evidence(self) -> TargetEvidence:
        route = self.route().value
        source = route if self.source_state is None else f"{self.source_state}|route:{route}"
        return TargetEvidence(score=self.aggregate_score, source_state=source)
