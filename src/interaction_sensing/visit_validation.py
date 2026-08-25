"""Pre-data evaluator contracts for V15 real visit-observation validation.

The evaluator keeps biological truth and observation-support truth separate. It
also distinguishes retaining a candidate clip from making an interpretable
positive biological claim. This matters when a target-focused observer fires in a
window that the V14 support gate marks unobservable: the clip may still deserve
review, but the window remains censored for ecological inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observation_triad import (
    InferentialStatus,
    ObservationAvailability,
    ObservationInterpretation,
)


class VisitTruthState(str, Enum):
    NO_INSECT = "no_insect"
    INSECT_IN_CONTEXT = "insect_in_context"
    TARGET_CONTACT = "target_contact"
    VISIT_EVENT = "visit_event"

    @property
    def is_visit(self) -> bool:
        return self is VisitTruthState.VISIT_EVENT


@dataclass(frozen=True, slots=True)
class VisitTruthRecord:
    window_id: str
    block_id: str
    biological_state: VisitTruthState
    support_truth: ObservationAvailability
    nuisance_labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if not self.block_id:
            raise ValueError("block_id cannot be empty")


@dataclass(frozen=True, slots=True)
class VisitPredictionRecord:
    """System output expressed in inference-safe actions rather than one score."""

    window_id: str
    retain_candidate: bool
    positive_evidence: bool
    negative_evidence: bool
    censored: bool
    audit_priority: bool
    protected_random_audit: bool = False
    target_score: float | None = None
    nuisance_burden: float | None = None

    def __post_init__(self) -> None:
        if not self.window_id:
            raise ValueError("window_id cannot be empty")
        if self.positive_evidence and self.negative_evidence:
            raise ValueError("a window cannot be both positive and negative evidence")
        if self.censored and (self.positive_evidence or self.negative_evidence):
            raise ValueError("a censored window cannot be used as interpretable positive/negative evidence")
        for name, value in (("target_score", self.target_score), ("nuisance_burden", self.nuisance_burden)):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class VisitValidationSummary:
    n_windows: int
    observable_true_visit_windows: int
    retained_observable_true_visits: int
    visit_recall_on_observable_truth: float
    candidate_false_positive_rate: float
    negative_calls: int
    false_absence_count: int
    false_absence_rate: float
    missed_visit_as_absence_rate: float
    true_unobservable_windows: int
    unobservable_recall: float
    observable_false_censor_rate: float
    fraction_censored: float
    audit_fraction: float
    retained_candidate_fraction: float
    shared_blind_spot_truth_windows: int
    shared_blind_spot_audited: int
    shared_blind_spot_discovery_rate: float


def prediction_from_triad(window_id: str, result: ObservationInterpretation, *, protected_random_audit: bool = False) -> VisitPredictionRecord:
    """Convert a V14 triad interpretation to the V15 evaluator contract."""

    return VisitPredictionRecord(
        window_id=window_id,
        retain_candidate=result.retain_target_clip,
        positive_evidence=result.inferential_status is InferentialStatus.POSITIVE_CANDIDATE,
        negative_evidence=result.inferential_status is InferentialStatus.NEGATIVE_EVIDENCE,
        censored=result.inferential_status is InferentialStatus.CENSORED,
        audit_priority=result.audit_priority,
        protected_random_audit=protected_random_audit,
        target_score=result.target_score,
        nuisance_burden=result.nuisance_burden,
    )


def _ratio(num: int, den: int) -> float:
    return 0.0 if den == 0 else num / den


def evaluate_visit_predictions(
    truth: list[VisitTruthRecord],
    predictions: list[VisitPredictionRecord],
    *,
    target_low_threshold: float = 0.25,
    nuisance_low_threshold: float = 0.60,
) -> VisitValidationSummary:
    """Evaluate inference and censoring without treating frames as replicates.

    This function reports window-level diagnostic quantities only. Confidence
    intervals and block-level visit-rate estimators belong to the final V15 freeze
    once a sample-size/cluster design is fixed.
    """

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
    observable_visits = [
        (t, p)
        for t, p in rows
        if t.biological_state.is_visit and t.support_truth is ObservationAvailability.OBSERVABLE
    ]
    retained_observable_visits = sum(p.retain_candidate for _, p in observable_visits)

    nonvisit_rows = [(t, p) for t, p in rows if not t.biological_state.is_visit]
    candidate_false_positives = sum(p.retain_candidate for _, p in nonvisit_rows)

    negative_rows = [(t, p) for t, p in rows if p.negative_evidence]
    false_absences = sum(t.biological_state.is_visit for t, _ in negative_rows)
    all_visits = [(t, p) for t, p in rows if t.biological_state.is_visit]
    visits_called_negative = sum(p.negative_evidence for _, p in all_visits)

    unobservable_rows = [(t, p) for t, p in rows if t.support_truth is ObservationAvailability.UNOBSERVABLE]
    censored_unobservable = sum(p.censored for _, p in unobservable_rows)
    observable_rows = [(t, p) for t, p in rows if t.support_truth is ObservationAvailability.OBSERVABLE]
    censored_observable = sum(p.censored for _, p in observable_rows)

    shared_blind_spots = [
        (t, p)
        for t, p in rows
        if (t.biological_state.is_visit or t.support_truth is ObservationAvailability.UNOBSERVABLE)
        and p.target_score is not None
        and p.nuisance_burden is not None
        and p.target_score <= target_low_threshold
        and p.nuisance_burden < nuisance_low_threshold
    ]
    shared_blind_spot_audited = sum(p.protected_random_audit for _, p in shared_blind_spots)

    return VisitValidationSummary(
        n_windows=len(rows),
        observable_true_visit_windows=len(observable_visits),
        retained_observable_true_visits=retained_observable_visits,
        visit_recall_on_observable_truth=_ratio(retained_observable_visits, len(observable_visits)),
        candidate_false_positive_rate=_ratio(candidate_false_positives, len(nonvisit_rows)),
        negative_calls=len(negative_rows),
        false_absence_count=false_absences,
        false_absence_rate=_ratio(false_absences, len(negative_rows)),
        missed_visit_as_absence_rate=_ratio(visits_called_negative, len(all_visits)),
        true_unobservable_windows=len(unobservable_rows),
        unobservable_recall=_ratio(censored_unobservable, len(unobservable_rows)),
        observable_false_censor_rate=_ratio(censored_observable, len(observable_rows)),
        fraction_censored=_ratio(sum(p.censored for _, p in rows), len(rows)),
        audit_fraction=_ratio(sum(p.audit_priority for _, p in rows), len(rows)),
        retained_candidate_fraction=_ratio(sum(p.retain_candidate for _, p in rows), len(rows)),
        shared_blind_spot_truth_windows=len(shared_blind_spots),
        shared_blind_spot_audited=shared_blind_spot_audited,
        shared_blind_spot_discovery_rate=_ratio(shared_blind_spot_audited, len(shared_blind_spots)),
    )
