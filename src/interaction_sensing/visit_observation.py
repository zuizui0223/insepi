"""Visit-observation semantics built on the V14 target–nuisance–support triad.

The important distinction is between a biological non-detection and a failed
observation opportunity. A low target score can contribute negative evidence
only when the focal interaction zone was sufficiently observable and missed-event
risk was acceptably low. Otherwise the window is ambiguous or censored.
"""
from __future__ import annotations

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
    than silently converted to zero visits.
    """

    window_id: str
    opportunity_seconds: float
    status: VisitObservationStatus
    denominator_eligible: bool
    absence_interpretable: bool
    target_score: float
    nuisance_burden: float
    observability_ceiling: float
    triad_state: TriadState
    actions: tuple[DiagnosticAction, ...]

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if self.opportunity_seconds <= 0:
            raise ValueError("opportunity_seconds must be positive")
        if self.status is VisitObservationStatus.CENSORED_UNOBSERVABLE and self.denominator_eligible:
            raise ValueError("censored windows cannot enter the conservative denominator")
        if self.status is VisitObservationStatus.OBSERVABLE_NONDETECTION and not self.absence_interpretable:
            raise ValueError("observable non-detection requires interpretable absence")


@dataclass(frozen=True, slots=True)
class VisitObservationSummary:
    """Design-aware summary that never treats censored effort as observed absence."""

    n_windows: int
    eligible_windows: int
    eligible_seconds: float
    censored_windows: int
    censored_seconds: float
    visit_candidate_windows: int
    observable_nondetection_windows: int
    audit_or_ambiguous_windows: int

    @property
    def observable_fraction(self) -> float:
        total = self.eligible_seconds + self.censored_seconds
        return 0.0 if total <= 0 else self.eligible_seconds / total


def diagnostic_actions(interpretation: ObservationInterpretation) -> tuple[DiagnosticAction, ...]:
    """Route a triad state to evidence-preserving next actions."""

    state = interpretation.state
    actions: list[DiagnosticAction] = []

    if interpretation.retain_target_clip:
        actions.append(DiagnosticAction.RETAIN_TARGET_CLIP)
    if interpretation.record_high_resolution_context:
        actions.append(DiagnosticAction.RECORD_HIGH_RES_CONTEXT)

    if state is TriadState.TARGET_NUISANCE_CONFLICT:
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
        triad_state=interpretation.state,
        actions=diagnostic_actions(interpretation),
    )


def summarise_visit_observations(records: Iterable[VisitObservationRecord]) -> VisitObservationSummary:
    """Summarise observation effort without turning censored effort into zeros."""

    rows = tuple(records)
    eligible = tuple(row for row in rows if row.denominator_eligible)
    censored = tuple(row for row in rows if row.status is VisitObservationStatus.CENSORED_UNOBSERVABLE)
    candidates = sum(row.status is VisitObservationStatus.VISIT_CANDIDATE for row in rows)
    negative = sum(row.status is VisitObservationStatus.OBSERVABLE_NONDETECTION for row in rows)
    uncertain = sum(
        row.status in {VisitObservationStatus.CONFLICT_AUDIT, VisitObservationStatus.AMBIGUOUS}
        for row in rows
    )
    return VisitObservationSummary(
        n_windows=len(rows),
        eligible_windows=len(eligible),
        eligible_seconds=sum(row.opportunity_seconds for row in eligible),
        censored_windows=len(censored),
        censored_seconds=sum(row.opportunity_seconds for row in censored),
        visit_candidate_windows=candidates,
        observable_nondetection_windows=negative,
        audit_or_ambiguous_windows=uncertain,
    )
