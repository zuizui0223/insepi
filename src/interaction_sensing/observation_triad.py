"""Target–nuisance–observability contracts for ecological interaction sensing.

This module deliberately keeps three quantities separate:

1. target evidence: evidence for the focal biological actor/event;
2. nuisance risk: non-target processes that can mimic, hide, or misattribute it;
3. observability support: whether the focal interaction zone was measurable well
   enough that presence/absence could be interpreted at all.

The key invariant is that observability is *not* defined as one minus nuisance.
A scene may be noisy yet observable, or visually quiet yet unobservable because
of occlusion, loss of field-of-view coverage, severe blur, saturation, or another
measurement-channel failure.

The policy below is a transparent reference synthesiser, not a calibrated field
classifier. Its purpose is to make the inferential states and forbidden
interpretations explicit before a future visitation-validation generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObservationAvailability(str, Enum):
    """Whether a biological state is defensibly interpretable from the window."""

    OBSERVABLE = "observable"
    COMPROMISED = "compromised"
    UNOBSERVABLE = "unobservable"


class TriadState(str, Enum):
    """Diagnostic state after keeping target, nuisance, and support separate."""

    CLEAN_TARGET_CANDIDATE = "clean_target_candidate"
    TARGET_NUISANCE_CONFLICT = "target_nuisance_conflict"
    TARGET_OBSERVABILITY_CONFLICT = "target_observability_conflict"
    NUISANCE_DOMINATED_OR_POSSIBLE_MISS = "nuisance_dominated_or_possible_miss"
    QUIET_OBSERVABLE = "quiet_observable"
    QUIET_COMPROMISED = "quiet_compromised"
    UNOBSERVABLE_CENSORED = "unobservable_censored"
    AMBIGUOUS = "ambiguous"


class InferentialStatus(str, Enum):
    """What the current window can contribute to ecological interpretation."""

    POSITIVE_CANDIDATE = "positive_candidate"
    NEGATIVE_EVIDENCE = "negative_evidence"
    AMBIGUOUS = "ambiguous"
    CENSORED = "censored"


@dataclass(frozen=True, slots=True)
class TargetEvidence:
    """Evidence emitted by a target-focused observer (for example PolliPi)."""

    score: float
    source_state: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("target evidence score must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class NuisanceEvidence:
    """Observation-process risks emitted by a nuisance-focused observer.

    Stable flowers, static background, and other harmless non-target context are
    not automatically nuisance. A non-target process matters here only insofar as
    it can create a false event, hide an event, or corrupt attribution.
    """

    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    dominant_source: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("false_event_risk", self.false_event_risk),
            ("missed_event_risk", self.missed_event_risk),
            ("attribution_risk", self.attribution_risk),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    @property
    def burden(self) -> float:
        return max(self.false_event_risk, self.missed_event_risk, self.attribution_risk)


@dataclass(frozen=True, slots=True)
class ObservationSupport:
    """Counterfactual support for detecting a visit *if one were present*.

    These components describe the measurement channel, not the observed insect
    state. The conservative ceiling is the minimum component: a hard failure in
    field-of-view coverage, visibility, resolution, photometry, or temporal
    continuity can make a non-detection uninterpretable even when nuisance scores
    are otherwise low.
    """

    target_zone_coverage: float
    target_zone_visibility: float
    spatial_resolution: float
    photometric_sufficiency: float
    temporal_continuity: float
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in self.component_scores:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    @property
    def component_scores(self) -> tuple[tuple[str, float], ...]:
        """Stable ordered support components for provenance and diagnosis."""

        return (
            ("target_zone_coverage", self.target_zone_coverage),
            ("target_zone_visibility", self.target_zone_visibility),
            ("spatial_resolution", self.spatial_resolution),
            ("photometric_sufficiency", self.photometric_sufficiency),
            ("temporal_continuity", self.temporal_continuity),
        )

    @property
    def ceiling(self) -> float:
        return min(value for _, value in self.component_scores)

    @property
    def limiting_component(self) -> str:
        """First minimum component in a fixed order, for deterministic diagnosis."""

        return min(self.component_scores, key=lambda item: item[1])[0]


@dataclass(frozen=True, slots=True)
class ObservationInterpretation:
    """Joint interpretation without collapsing the three axes into one score."""

    state: TriadState
    availability: ObservationAvailability
    inferential_status: InferentialStatus
    target_score: float
    nuisance_burden: float
    observability_ceiling: float
    observability_limiting_component: str
    absence_interpretable: bool
    denominator_eligible: bool
    audit_priority: bool
    retain_target_clip: bool
    record_high_resolution_context: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObservationTriadPolicy:
    """Reference policy for combining separate target/nuisance/support evidence.

    Thresholds are intentionally explicit development defaults. They are not
    field-calibrated visitation probabilities and must be revalidated before any
    biological accuracy claim.
    """

    target_high_threshold: float = 0.65
    target_low_threshold: float = 0.25
    nuisance_high_threshold: float = 0.60
    observable_threshold: float = 0.70
    unobservable_threshold: float = 0.30

    def __post_init__(self) -> None:
        for name, value in (
            ("target_high_threshold", self.target_high_threshold),
            ("target_low_threshold", self.target_low_threshold),
            ("nuisance_high_threshold", self.nuisance_high_threshold),
            ("observable_threshold", self.observable_threshold),
            ("unobservable_threshold", self.unobservable_threshold),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.target_low_threshold >= self.target_high_threshold:
            raise ValueError("target_low_threshold must be below target_high_threshold")
        if self.unobservable_threshold >= self.observable_threshold:
            raise ValueError("unobservable_threshold must be below observable_threshold")

    def availability(self, support: ObservationSupport) -> ObservationAvailability:
        if support.ceiling <= self.unobservable_threshold:
            return ObservationAvailability.UNOBSERVABLE
        if support.ceiling >= self.observable_threshold:
            return ObservationAvailability.OBSERVABLE
        return ObservationAvailability.COMPROMISED

    def decide(
        self,
        target: TargetEvidence,
        nuisance: NuisanceEvidence,
        support: ObservationSupport,
    ) -> ObservationInterpretation:
        availability = self.availability(support)
        target_high = target.score >= self.target_high_threshold
        target_low = target.score <= self.target_low_threshold
        nuisance_high = nuisance.burden >= self.nuisance_high_threshold

        reasons = list(support.reasons)
        if target.source_state:
            reasons.append(f"target:{target.source_state}")
        if nuisance.dominant_source:
            reasons.append(f"nuisance:{nuisance.dominant_source}")
        reasons.append(f"support_limit:{support.limiting_component}")

        # An unobservable window is censored regardless of whether either
        # observer emitted a high/low score. A high target score is retained as a
        # candidate for audit, but it is not upgraded to a defensible visit.
        if availability is ObservationAvailability.UNOBSERVABLE:
            reasons.append("measurement support below unobservable ceiling")
            return ObservationInterpretation(
                state=TriadState.UNOBSERVABLE_CENSORED,
                availability=availability,
                inferential_status=InferentialStatus.CENSORED,
                target_score=target.score,
                nuisance_burden=nuisance.burden,
                observability_ceiling=support.ceiling,
                observability_limiting_component=support.limiting_component,
                absence_interpretable=False,
                denominator_eligible=False,
                audit_priority=True,
                retain_target_clip=target_high,
                record_high_resolution_context=True,
                reasons=tuple(reasons),
            )

        if target_high and nuisance_high:
            reasons.append("target evidence conflicts with elevated nuisance risk")
            state = TriadState.TARGET_NUISANCE_CONFLICT
            inferential_status = InferentialStatus.AMBIGUOUS
            audit_priority = True
        elif target_high and availability is ObservationAvailability.COMPROMISED:
            reasons.append("target evidence exceeds threshold but measurement support is compromised")
            state = TriadState.TARGET_OBSERVABILITY_CONFLICT
            inferential_status = InferentialStatus.AMBIGUOUS
            audit_priority = True
        elif target_high:
            reasons.append("target evidence under observable low-nuisance conditions")
            state = TriadState.CLEAN_TARGET_CANDIDATE
            inferential_status = InferentialStatus.POSITIVE_CANDIDATE
            audit_priority = False
        elif target_low and nuisance_high:
            reasons.append("low target evidence occurs where nuisance can mimic or hide the event")
            state = TriadState.NUISANCE_DOMINATED_OR_POSSIBLE_MISS
            inferential_status = InferentialStatus.AMBIGUOUS
            audit_priority = True
        elif target_low and availability is ObservationAvailability.OBSERVABLE:
            reasons.append("low target evidence under sufficient measurement support")
            state = TriadState.QUIET_OBSERVABLE
            inferential_status = InferentialStatus.NEGATIVE_EVIDENCE
            audit_priority = False
        elif target_low:
            reasons.append("low target evidence cannot be treated as absence under compromised support")
            state = TriadState.QUIET_COMPROMISED
            inferential_status = InferentialStatus.AMBIGUOUS
            audit_priority = True
        else:
            reasons.append("target evidence lies between positive and negative reference thresholds")
            state = TriadState.AMBIGUOUS
            inferential_status = InferentialStatus.AMBIGUOUS
            audit_priority = nuisance_high or availability is ObservationAvailability.COMPROMISED

        # Absence requires both sufficient observation support and no large
        # missed-event warning. Other nuisance types may still affect attribution
        # of a positive candidate without invalidating the opportunity denominator.
        absence_interpretable = (
            state is TriadState.QUIET_OBSERVABLE
            and nuisance.missed_event_risk < self.nuisance_high_threshold
        )
        denominator_eligible = (
            availability is ObservationAvailability.OBSERVABLE
            and nuisance.missed_event_risk < self.nuisance_high_threshold
        )
        return ObservationInterpretation(
            state=state,
            availability=availability,
            inferential_status=inferential_status,
            target_score=target.score,
            nuisance_burden=nuisance.burden,
            observability_ceiling=support.ceiling,
            observability_limiting_component=support.limiting_component,
            absence_interpretable=absence_interpretable,
            denominator_eligible=denominator_eligible,
            audit_priority=audit_priority,
            retain_target_clip=target_high,
            record_high_resolution_context=audit_priority,
            reasons=tuple(reasons),
        )
