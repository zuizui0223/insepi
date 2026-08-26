"""Pre-data evaluator contracts for V15 real visit-observation validation.

Biological truth, target-coupled response truth, exogenous nuisance truth, and
primary-stream observation support remain separate. V15 v2 additionally keeps
**certified target absence** separate from a forced negative call.

A low score from a positive-only target observer is not target-absence evidence.
Observation support O can make a window interpretable, but O does not itself
supply the missing biological negative evidence. Historical/naive architectures
may still emit a ``forced_absence_call`` so their false-certainty cost can be
measured without misnaming that call as evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .absence_certification import TargetAbsenceEvidence
from .observation_triad import InferentialStatus, ObservationAvailability, ObservationInterpretation
from .support_truth import PrimaryStreamSupportTruth, SupportTruthResolution
from .target_routes import TargetRouteEvidence


class VisitTruthState(str, Enum):
    NO_INSECT = "no_insect"
    INSECT_IN_CONTEXT = "insect_in_context"
    TARGET_CONTACT = "target_contact"
    VISIT_EVENT = "visit_event"

    @property
    def is_visit(self) -> bool:
        return self is VisitTruthState.VISIT_EVENT


class VisitTruthResolution(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


class CoupledResponseResolution(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class VisitTruthRecord:
    window_id: str
    block_id: str
    biological_state: VisitTruthState | None
    primary_support_truth: PrimaryStreamSupportTruth
    nuisance_labels: tuple[str, ...] = ()
    biological_truth_resolution: VisitTruthResolution = VisitTruthResolution.RESOLVED
    reference_truth_source: str | None = None
    event_id: str | None = None
    target_coupled_response_present: bool | None = False
    target_coupled_response_resolution: CoupledResponseResolution = CoupledResponseResolution.RESOLVED

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if not self.block_id:
            raise ValueError("block_id cannot be empty")
        if self.biological_truth_resolution is VisitTruthResolution.RESOLVED and self.biological_state is None:
            raise ValueError("resolved biological truth requires biological_state")
        if self.biological_truth_resolution is VisitTruthResolution.UNRESOLVED and self.biological_state is not None:
            raise ValueError("unresolved biological truth must not carry a biological_state")
        if self.biological_truth_resolution is VisitTruthResolution.UNRESOLVED and self.event_id is not None:
            raise ValueError("unresolved biological truth must not carry event_id")
        if self.biological_state is VisitTruthState.VISIT_EVENT and not self.event_id:
            raise ValueError("resolved visit_event requires a stable event_id")
        if self.biological_state is not VisitTruthState.VISIT_EVENT and self.event_id is not None:
            raise ValueError("event_id is reserved for visit_event truth")

        if self.target_coupled_response_resolution is CoupledResponseResolution.RESOLVED:
            if self.target_coupled_response_present is None:
                raise ValueError("resolved coupled-response truth requires a boolean state")
        elif self.target_coupled_response_present is not None:
            raise ValueError("unresolved coupled-response truth must not carry a present/absent state")

        if self.target_coupled_response_present is True:
            if self.biological_truth_resolution is not VisitTruthResolution.RESOLVED:
                raise ValueError("resolved target-coupled response requires resolved biological truth")
            if self.biological_state not in {VisitTruthState.TARGET_CONTACT, VisitTruthState.VISIT_EVENT}:
                raise ValueError("target-coupled response requires target_contact or visit_event truth")

    @property
    def biological_truth_resolved(self) -> bool:
        return self.biological_truth_resolution is VisitTruthResolution.RESOLVED

    @property
    def coupled_response_truth_resolved(self) -> bool:
        return self.target_coupled_response_resolution is CoupledResponseResolution.RESOLVED

    @property
    def support_truth_resolved(self) -> bool:
        return self.primary_support_truth.resolution is SupportTruthResolution.RESOLVED

    @property
    def support_truth(self) -> ObservationAvailability | None:
        return self.primary_support_truth.availability

    @property
    def is_visit(self) -> bool:
        return self.biological_truth_resolved and self.biological_state is VisitTruthState.VISIT_EVENT


@dataclass(frozen=True, slots=True)
class VisitPredictionRecord:
    """Window output with safe absence separated from forced binarisation.

    ``negative_evidence`` now means an absence call backed by an independently
    validated target-absence channel. ``forced_absence_call`` records an unsafe or
    deliberately naive negative decision made without that certification. A
    window with neither positive/negative evidence nor censoring is unresolved.
    """

    window_id: str
    retain_candidate: bool
    positive_evidence: bool
    negative_evidence: bool
    censored: bool
    audit_priority: bool
    protected_random_audit: bool = False
    target_score: float | None = None
    nuisance_burden: float | None = None
    direct_target_score: float | None = None
    coupled_target_score: float | None = None
    forced_absence_call: bool = False
    absence_certification_source: str | None = None

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if self.positive_evidence and self.negative_evidence:
            raise ValueError("a window cannot be both positive and certified negative evidence")
        if self.censored and (self.positive_evidence or self.negative_evidence or self.forced_absence_call):
            raise ValueError("a censored window cannot carry positive, certified-negative, or forced-absence calls")
        if self.forced_absence_call and (self.positive_evidence or self.negative_evidence):
            raise ValueError("forced absence is an unsafe comparator and cannot also be positive/certified negative")
        if self.absence_certification_source is not None and not self.negative_evidence:
            raise ValueError("absence certification source is only valid for certified negative evidence")
        for name, value in (
            ("target_score", self.target_score),
            ("nuisance_burden", self.nuisance_burden),
            ("direct_target_score", self.direct_target_score),
            ("coupled_target_score", self.coupled_target_score),
        ):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")

    @property
    def unresolved(self) -> bool:
        return not (self.positive_evidence or self.negative_evidence or self.censored)


@dataclass(frozen=True, slots=True)
class VisitValidationSummary:
    n_windows: int
    resolved_biological_truth_windows: int
    unresolved_biological_truth_windows: int
    reference_truth_unresolved_fraction: float
    resolved_primary_support_windows: int
    unresolved_primary_support_windows: int
    primary_support_unresolved_fraction: float
    resolved_visit_events: int
    observable_true_visit_windows: int
    retained_observable_true_visits: int
    visit_recall_on_observable_truth: float
    candidate_false_positive_rate: float
    certified_absence_calls_on_resolved_truth: int
    false_certified_absence_count: int
    false_certified_absence_rate: float
    missed_visit_as_certified_absence_rate: float
    forced_absence_calls_on_resolved_truth: int
    forced_false_absence_count: int
    forced_false_absence_rate: float
    forced_missed_visit_as_absence_rate: float
    true_unobservable_windows: int
    unobservable_recall: float
    observable_false_censor_rate: float
    fraction_censored: float
    unresolved_fraction: float
    audit_fraction: float
    retained_candidate_fraction: float
    shared_blind_spot_truth_windows: int
    shared_blind_spot_audited: int
    shared_blind_spot_discovery_rate: float
    resolved_coupled_response_windows: int
    unresolved_coupled_response_windows: int
    weak_direct_coupled_visit_windows: int
    indirect_target_rescue_count: int
    indirect_target_rescue_rate: float
    observable_no_insect_windows: int
    spurious_coupled_candidate_count: int
    spurious_coupled_candidate_rate: float


def prediction_from_triad(
    window_id: str,
    result: ObservationInterpretation,
    *,
    protected_random_audit: bool = False,
    target_routes: TargetRouteEvidence | None = None,
    absence_evidence: TargetAbsenceEvidence | None = None,
) -> VisitPredictionRecord:
    """Convert a V14 interpretation without inverting low target evidence.

    Historical V14 triad policies can emit ``NEGATIVE_EVIDENCE`` from low target
    score plus adequate support. V15 v2 does not accept that as certified absence
    unless an independent ``TargetAbsenceEvidence`` record is supplied. Without
    certification the historical negative is retained only as a forced comparator
    and routed to audit.
    """

    historical_negative = result.inferential_status is InferentialStatus.NEGATIVE_EVIDENCE
    certified = bool(historical_negative and absence_evidence is not None and absence_evidence.supports_absence)
    forced = bool(historical_negative and not certified)
    return VisitPredictionRecord(
        window_id=window_id,
        retain_candidate=result.retain_target_clip,
        positive_evidence=result.inferential_status is InferentialStatus.POSITIVE_CANDIDATE,
        negative_evidence=certified,
        censored=result.inferential_status is InferentialStatus.CENSORED,
        audit_priority=result.audit_priority or forced,
        protected_random_audit=protected_random_audit,
        target_score=result.target_score,
        nuisance_burden=result.nuisance_burden,
        direct_target_score=None if target_routes is None else target_routes.direct_insect_score,
        coupled_target_score=None if target_routes is None else target_routes.coupled_target_score,
        forced_absence_call=forced,
        absence_certification_source=(absence_evidence.source if certified and absence_evidence is not None else None),
    )


def _ratio(num: int, den: int) -> float:
    return 0.0 if den == 0 else num / den


def evaluate_visit_predictions(
    truth: list[VisitTruthRecord],
    predictions: list[VisitPredictionRecord],
    *,
    target_low_threshold: float = 0.25,
    target_high_threshold: float = 0.65,
    nuisance_low_threshold: float = 0.60,
) -> VisitValidationSummary:
    """Evaluate target retention, certified absence, forced absence and censoring."""

    truth_by_id = {row.window_id: row for row in truth}
    pred_by_id = {row.window_id: row for row in predictions}
    if len(truth_by_id) != len(truth):
        raise ValueError("truth window_id values must be unique")
    if len(pred_by_id) != len(predictions):
        raise ValueError("prediction window_id values must be unique")
    if set(truth_by_id) != set(pred_by_id):
        missing_pred = sorted(set(truth_by_id) - set(pred_by_id))
        missing_truth = sorted(set(pred_by_id) - set(truth_by_id))
        raise ValueError(f"truth/prediction window mismatch: missing_pred={missing_pred}, missing_truth={missing_truth}")

    rows = [(truth_by_id[key], pred_by_id[key]) for key in sorted(truth_by_id)]
    resolved_rows = [(t, p) for t, p in rows if t.biological_truth_resolved]
    unresolved_rows = [(t, p) for t, p in rows if not t.biological_truth_resolved]
    resolved_support_rows = [(t, p) for t, p in rows if t.support_truth_resolved]
    unresolved_support_rows = [(t, p) for t, p in rows if not t.support_truth_resolved]
    resolved_visit_event_ids = {t.event_id for t, _ in resolved_rows if t.is_visit and t.event_id is not None}

    observable_visits = [
        (t, p) for t, p in resolved_rows
        if t.is_visit and t.support_truth is ObservationAvailability.OBSERVABLE
    ]
    retained_observable_visits = sum(p.retain_candidate for _, p in observable_visits)

    nonvisit_rows = [(t, p) for t, p in resolved_rows if not t.is_visit]
    candidate_false_positives = sum(p.retain_candidate for _, p in nonvisit_rows)

    certified_rows = [(t, p) for t, p in resolved_rows if p.negative_evidence]
    false_certified = sum(t.is_visit for t, _ in certified_rows)
    forced_rows = [(t, p) for t, p in resolved_rows if p.forced_absence_call]
    false_forced = sum(t.is_visit for t, _ in forced_rows)
    all_visits = [(t, p) for t, p in resolved_rows if t.is_visit]
    visits_certified_absent = sum(p.negative_evidence for _, p in all_visits)
    visits_forced_absent = sum(p.forced_absence_call for _, p in all_visits)

    unobservable_rows = [
        (t, p) for t, p in resolved_support_rows
        if t.support_truth is ObservationAvailability.UNOBSERVABLE
    ]
    censored_unobservable = sum(p.censored for _, p in unobservable_rows)
    observable_rows = [
        (t, p) for t, p in resolved_support_rows
        if t.support_truth is ObservationAvailability.OBSERVABLE
    ]
    censored_observable = sum(p.censored for _, p in observable_rows)

    shared_blind_spots = [
        (t, p)
        for t, p in rows
        if (t.is_visit or t.support_truth is ObservationAvailability.UNOBSERVABLE)
        and p.target_score is not None
        and p.nuisance_burden is not None
        and p.target_score <= target_low_threshold
        and p.nuisance_burden < nuisance_low_threshold
    ]
    shared_blind_spot_audited = sum(p.protected_random_audit for _, p in shared_blind_spots)

    resolved_coupling = [(t, p) for t, p in rows if t.coupled_response_truth_resolved]
    unresolved_coupling = [(t, p) for t, p in rows if not t.coupled_response_truth_resolved]
    weak_direct_coupled_visits = [
        (t, p)
        for t, p in resolved_rows
        if t.is_visit
        and t.support_truth is ObservationAvailability.OBSERVABLE
        and t.target_coupled_response_present is True
        and p.direct_target_score is not None
        and p.direct_target_score <= target_low_threshold
        and p.coupled_target_score is not None
    ]
    indirect_rescues = sum(
        p.retain_candidate
        and p.coupled_target_score is not None
        and p.coupled_target_score >= target_high_threshold
        for _, p in weak_direct_coupled_visits
    )

    observable_no_insect = [
        (t, p)
        for t, p in resolved_rows
        if t.biological_state is VisitTruthState.NO_INSECT
        and t.support_truth is ObservationAvailability.OBSERVABLE
    ]
    spurious_coupled = sum(
        p.retain_candidate
        and p.coupled_target_score is not None
        and p.coupled_target_score >= target_high_threshold
        for _, p in observable_no_insect
    )

    return VisitValidationSummary(
        n_windows=len(rows),
        resolved_biological_truth_windows=len(resolved_rows),
        unresolved_biological_truth_windows=len(unresolved_rows),
        reference_truth_unresolved_fraction=_ratio(len(unresolved_rows), len(rows)),
        resolved_primary_support_windows=len(resolved_support_rows),
        unresolved_primary_support_windows=len(unresolved_support_rows),
        primary_support_unresolved_fraction=_ratio(len(unresolved_support_rows), len(rows)),
        resolved_visit_events=len(resolved_visit_event_ids),
        observable_true_visit_windows=len(observable_visits),
        retained_observable_true_visits=retained_observable_visits,
        visit_recall_on_observable_truth=_ratio(retained_observable_visits, len(observable_visits)),
        candidate_false_positive_rate=_ratio(candidate_false_positives, len(nonvisit_rows)),
        certified_absence_calls_on_resolved_truth=len(certified_rows),
        false_certified_absence_count=false_certified,
        false_certified_absence_rate=_ratio(false_certified, len(certified_rows)),
        missed_visit_as_certified_absence_rate=_ratio(visits_certified_absent, len(all_visits)),
        forced_absence_calls_on_resolved_truth=len(forced_rows),
        forced_false_absence_count=false_forced,
        forced_false_absence_rate=_ratio(false_forced, len(forced_rows)),
        forced_missed_visit_as_absence_rate=_ratio(visits_forced_absent, len(all_visits)),
        true_unobservable_windows=len(unobservable_rows),
        unobservable_recall=_ratio(censored_unobservable, len(unobservable_rows)),
        observable_false_censor_rate=_ratio(censored_observable, len(observable_rows)),
        fraction_censored=_ratio(sum(p.censored for _, p in rows), len(rows)),
        unresolved_fraction=_ratio(sum(p.unresolved for _, p in rows), len(rows)),
        audit_fraction=_ratio(sum(p.audit_priority for _, p in rows), len(rows)),
        retained_candidate_fraction=_ratio(sum(p.retain_candidate for _, p in rows), len(rows)),
        shared_blind_spot_truth_windows=len(shared_blind_spots),
        shared_blind_spot_audited=shared_blind_spot_audited,
        shared_blind_spot_discovery_rate=_ratio(shared_blind_spot_audited, len(shared_blind_spots)),
        resolved_coupled_response_windows=len(resolved_coupling),
        unresolved_coupled_response_windows=len(unresolved_coupling),
        weak_direct_coupled_visit_windows=len(weak_direct_coupled_visits),
        indirect_target_rescue_count=indirect_rescues,
        indirect_target_rescue_rate=_ratio(indirect_rescues, len(weak_direct_coupled_visits)),
        observable_no_insect_windows=len(observable_no_insect),
        spurious_coupled_candidate_count=spurious_coupled,
        spurious_coupled_candidate_rate=_ratio(spurious_coupled, len(observable_no_insect)),
    )
