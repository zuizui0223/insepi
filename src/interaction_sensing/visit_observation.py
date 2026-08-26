"""Visit-observation semantics built on the V14 target–nuisance–support triad.

The important distinction is between a biological non-detection and a failed
observation opportunity. A low target score can contribute negative evidence
only when the focal interaction zone was sufficiently observable and missed-event
risk was acceptably low. Otherwise the window is ambiguous or censored.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .observation_triad import (
    InferentialStatus,
    ObservationInterpretation,
    TriadState,
)


class VisitObservationStatus(str, Enum):
    """Ecological status of one fixed observation opportunity."""

    VISIT_CANDIDATE = "visit_candidate"
    OBSERVABLE_NONDETECTION = "observable_nondetection"
    CONFLICT_AUDIT = "conflict_audit"
    AMBIGUOUS = "ambiguous"
    CENSORED_UNOBSERVABLE = "censored_unobservable"


class DiagnosticAction(str, Enum):
    """Next action requested by a triad state.

    These actions are not truth labels. They specify what evidence should be
    preserved or what controlled check should be made next.
    """

    RETAIN_TARGET_CLIP = "retain_target_clip"
    AUDIT_NUISANCE = "audit_nuisance"
    RESTORE_OBSERVABILITY = "restore_observability"
    RECORD_HIGH_RES_CONTEXT = "record_high_resolution_context"
    PROTECTED_RANDOM_AUDIT = "protected_random_audit"
    CENSOR_FROM_DENOMINATOR = "censor_from_denominator"
    NO_EXTRA_ACTION = "no_extra_action"


@dataclass(frozen=True, slots=True)
class VisitObservationRecord:
    """One fixed-duration visit-observation opportunity.

    `opportunity_seconds` belongs in an ecological denominator only when
    `denominator_eligible` is true. Censored time is retained explicitly rather
    than silently converted to zero visits. The limiting observation-support
    component is stored so lost effort can be attributed to coverage, visibility,
    resolution, photometry, or temporal continuity rather than to a generic
    "noise" bucket.
    """

    window_id: str
    opportunity_seconds: float
    status: VisitObservationStatus
    denominator_eligible: bool
    absence_interpretable: bool
    target_score: float
    nuisance_burden: float
    observability_ceiling: float
    observability_limiting_component: str
    triad_state: TriadState
    actions: tuple[DiagnosticAction, ...]

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if self.opportunity_seconds <= 0:
            raise ValueError("opportunity_seconds must be positive")
        if not self.observability_limiting_component:
            raise ValueError("observability_limiting_component cannot be empty")
        if self.status is VisitObservationStatus.CENSORED_UNOBSERVABLE and self.denominator_eligible:
            raise ValueError("censored windows cannot enter the conservative denominator")
        if self.status is VisitObservationStatus.OBSERVABLE_NONDETECTION and not self.absence_interpretable:
            raise ValueError("observable non-detection requires interpretable absence")


@dataclass(frozen=True, slots=True)
class VisitObservationSummary:
    """Design-aware summary retaining all recorded observation effort.

    The three effort classes are disjoint and exhaustive:

    - eligible: can enter the conservative ecological opportunity denominator;
    - censored: structurally unobservable and explicitly censored;
    - uncertain_noneligible: not structurally censored, but still excluded from
      the denominator because nuisance/missed-event risk or compromised support
      prevents a defensible negative interpretation.

    This prevents compromised or ambiguous time from disappearing between the
    "observable" and "unobservable" buckets.
    """

    n_windows: int
    total_seconds: float
    eligible_windows: int
    eligible_seconds: float
    censored_windows: int
    censored_seconds: float
    uncertain_noneligible_windows: int
    uncertain_noneligible_seconds: float
    visit_candidate_windows: int
    observable_nondetection_windows: int
    audit_or_ambiguous_windows: int
    censored_limiting_components: tuple[tuple[str, int], ...]

    @property
    def observable_fraction(self) -> float:
        return 0.0 if self.total_seconds <= 0 else self.eligible_seconds / self.total_seconds

    @property
    def censored_fraction(self) -> float:
        return 0.0 if self.total_seconds <= 0 else self.censored_seconds / self.total_seconds

    @property
    def uncertain_noneligible_fraction(self) -> float:
        return (
            0.0
            if self.total_seconds <= 0
            else self.uncertain_noneligible_seconds / self.total_seconds
        )


def diagnostic_actions(interpretation: ObservationInterpretation) -> tuple[DiagnosticAction, ...]:
    """Route a triad state to evidence-preserving next actions."""

    state = interpretation.state
    actions: list[DiagnosticAction] = []

    if interpretation.retain_target_clip:
        actions.append(DiagnosticAction.RETAIN_TARGET_CLIP)
    if interpretation.record_high_resolution_context:
        actions.append(DiagnosticAction.RECORD_HIGH_RES_CONTEXT)

    if state in {
        TriadState.TARGET_NUISANCE_CONFLICT,
        TriadState.TARGET_NUISANCE_SUPERPOSITION,
    }:
        actions.append(DiagnosticAction.AUDIT_NUISANCE)
    elif state is TriadState.NUISANCE_DOMINATED_OR_POSSIBLE_MISS:
        actions.extend((DiagnosticAction.AUDIT_NUISANCE, DiagnosticAction.PROTECTED_RANDOM_AUDIT))
    elif state in {TriadState.TARGET_OBSERVABILITY_CONFLICT, TriadState.QUIET_COMPROMISED}:
        actions.extend((DiagnosticAction.RESTORE_OBSERVABILITY, DiagnosticAction.PROTECTED_RANDOM_AUDIT))
    elif state is TriadState.UNOBSERVABLE_CENSORED:
        actions.extend(
            (
                DiagnosticAction.RESTORE_OBSERVABILITY,
                DiagnosticAction.CENSOR_FROM_DENOMINATOR,
                DiagnosticAction.PROTECTED_RANDOM_AUDIT,
            )
        )
    elif state is TriadState.AMBIGUOUS:
        actions.append(DiagnosticAction.PROTECTED_RANDOM_AUDIT)
    elif not actions:
        actions.append(DiagnosticAction.NO_EXTRA_ACTION)

    # Preserve order while removing duplicates introduced by generic retention.
    return tuple(dict.fromkeys(actions))


def visit_record_from_interpretation(
    window_id: str,
    opportunity_seconds: float,
    interpretation: ObservationInterpretation,
) -> VisitObservationRecord:
    """Convert V14 interpretation into a visit-observation record."""

    if interpretation.inferential_status is InferentialStatus.POSITIVE_CANDIDATE:
        status = VisitObservationStatus.VISIT_CANDIDATE
    elif interpretation.inferential_status is InferentialStatus.NEGATIVE_EVIDENCE:
        status = VisitObservationStatus.OBSERVABLE_NONDETECTION
    elif interpretation.inferential_status is InferentialStatus.CENSORED:
        status = VisitObservationStatus.CENSORED_UNOBSERVABLE
    elif interpretation.audit_priority:
        status = VisitObservationStatus.CONFLICT_AUDIT
    else:
        status = VisitObservationStatus.AMBIGUOUS

    return VisitObservationRecord(
        window_id=window_id,
        opportunity_seconds=opportunity_seconds,
        status=status,
        denominator_eligible=interpretation.denominator_eligible,
        absence_interpretable=interpretation.absence_interpretable,
        target_score=interpretation.target_score,
        nuisance_burden=interpretation.nuisance_burden,
        observability_ceiling=interpretation.observability_ceiling,
        observability_limiting_component=interpretation.observability_limiting_component,
        triad_state=interpretation.state,
        actions=diagnostic_actions(interpretation),
    )


def summarise_visit_observations(records: Iterable[VisitObservationRecord]) -> VisitObservationSummary:
    """Summarise effort without turning censored or unresolved effort into zeros."""

    rows = tuple(records)
    eligible = tuple(row for row in rows if row.denominator_eligible)
    censored = tuple(row for row in rows if row.status is VisitObservationStatus.CENSORED_UNOBSERVABLE)
    uncertain_noneligible = tuple(
        row
        for row in rows
        if not row.denominator_eligible
        and row.status is not VisitObservationStatus.CENSORED_UNOBSERVABLE
    )
    candidates = sum(row.status is VisitObservationStatus.VISIT_CANDIDATE for row in rows)
    negative = sum(row.status is VisitObservationStatus.OBSERVABLE_NONDETECTION for row in rows)
    uncertain = sum(
        row.status in {VisitObservationStatus.CONFLICT_AUDIT, VisitObservationStatus.AMBIGUOUS}
        for row in rows
    )
    limiting_counts = Counter(row.observability_limiting_component for row in censored)
    return VisitObservationSummary(
        n_windows=len(rows),
        total_seconds=sum(row.opportunity_seconds for row in rows),
        eligible_windows=len(eligible),
        eligible_seconds=sum(row.opportunity_seconds for row in eligible),
        censored_windows=len(censored),
        censored_seconds=sum(row.opportunity_seconds for row in censored),
        uncertain_noneligible_windows=len(uncertain_noneligible),
        uncertain_noneligible_seconds=sum(row.opportunity_seconds for row in uncertain_noneligible),
        visit_candidate_windows=candidates,
        observable_nondetection_windows=negative,
        audit_or_ambiguous_windows=uncertain,
        censored_limiting_components=tuple(sorted(limiting_counts.items())),
    )
