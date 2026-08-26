"""Comparable V15 visit-observation architectures on the V14c semantics.

Target, target-coupled response, nuisance and observation support remain separate.
V15 v2 adds a fifth *optional* interface: independently validated target-absence
evidence. Observation support O is necessary for safe absence inference but is not
itself biological negative evidence.

Architectures that intentionally omit O/absence certification are retained as
unsafe comparators. Their low-score negatives are recorded as
``forced_absence_call`` rather than ``negative_evidence``.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .absence_certification import TargetAbsenceEvidence
from .observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ProcessPreservingObservationTriadPolicy,
)
from .support_estimation import PrimaryStreamSupportEstimate
from .target_routes import TargetRouteEvidence
from .visit_validation import (
    VisitPredictionRecord,
    VisitTruthRecord,
    VisitValidationSummary,
    evaluate_visit_predictions,
    prediction_from_triad,
)


class VisitSystemVariant(str, Enum):
    DIRECT_TARGET_ONLY = "direct_target_only_naive"
    DIRECT_PLUS_COUPLED = "direct_plus_coupled_target_without_nuisance_or_support"
    TARGET_PLUS_NUISANCE = "target_plus_nuisance_without_support_gate"
    TARGET_PLUS_SUPPORT = "target_plus_support_without_nuisance"
    FULL_TRIAD = "full_direct_coupled_target_nuisance_observability_triad"


@dataclass(frozen=True, slots=True)
class VisitSystemInputs:
    window_id: str
    target_routes: TargetRouteEvidence
    nuisance: NuisanceEvidence
    support: PrimaryStreamSupportEstimate
    protected_random_audit: bool = False
    absence_evidence: TargetAbsenceEvidence | None = None

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id cannot be empty")


@dataclass(frozen=True, slots=True)
class VisitSystemThresholds:
    target_high: float = 0.65
    target_low: float = 0.25
    nuisance_high: float = 0.60

    def __post_init__(self) -> None:
        if not 0.0 <= self.target_low < self.target_high <= 1.0:
            raise ValueError("target thresholds must satisfy 0 <= low < high <= 1")
        if not 0.0 <= self.nuisance_high <= 1.0:
            raise ValueError("nuisance_high must lie in [0, 1]")


def _unsafe_target_only_prediction(
    window_id: str,
    *,
    target_score: float,
    direct_score: float,
    coupled_score: float | None,
    thresholds: VisitSystemThresholds,
    protected_random_audit: bool,
) -> VisitPredictionRecord:
    """Naive comparator: low positive-target score is forced to absence."""

    positive = target_score >= thresholds.target_high
    forced_absence = target_score <= thresholds.target_low
    return VisitPredictionRecord(
        window_id=window_id,
        retain_candidate=positive,
        positive_evidence=positive,
        negative_evidence=False,
        censored=False,
        audit_priority=False,
        protected_random_audit=protected_random_audit,
        target_score=target_score,
        nuisance_burden=None,
        direct_target_score=direct_score,
        coupled_target_score=coupled_score,
        forced_absence_call=forced_absence,
    )


def _support_aware_prediction(
    inputs: VisitSystemInputs,
    *,
    target_score: float,
    direct_score: float,
    coupled_score: float,
    thresholds: VisitSystemThresholds,
) -> VisitPredictionRecord:
    """Use O as a gate, never as the biological negative-evidence source."""

    availability = inputs.support.availability
    target_high = target_score >= thresholds.target_high
    target_low = target_score <= thresholds.target_low

    if availability is ObservationAvailability.UNOBSERVABLE:
        return VisitPredictionRecord(
            window_id=inputs.window_id,
            retain_candidate=target_high,
            positive_evidence=False,
            negative_evidence=False,
            censored=True,
            audit_priority=True,
            protected_random_audit=inputs.protected_random_audit,
            target_score=target_score,
            nuisance_burden=None,
            direct_target_score=direct_score,
            coupled_target_score=coupled_score,
        )

    if availability is ObservationAvailability.COMPROMISED:
        return VisitPredictionRecord(
            window_id=inputs.window_id,
            retain_candidate=target_high,
            positive_evidence=False,
            negative_evidence=False,
            censored=False,
            audit_priority=True,
            protected_random_audit=inputs.protected_random_audit,
            target_score=target_score,
            nuisance_burden=None,
            direct_target_score=direct_score,
            coupled_target_score=coupled_score,
        )

    if target_high:
        return VisitPredictionRecord(
            window_id=inputs.window_id,
            retain_candidate=True,
            positive_evidence=True,
            negative_evidence=False,
            censored=False,
            audit_priority=False,
            protected_random_audit=inputs.protected_random_audit,
            target_score=target_score,
            nuisance_burden=None,
            direct_target_score=direct_score,
            coupled_target_score=coupled_score,
        )

    absence = inputs.absence_evidence
    certified = bool(target_low and absence is not None and absence.supports_absence)
    return VisitPredictionRecord(
        window_id=inputs.window_id,
        retain_candidate=False,
        positive_evidence=False,
        negative_evidence=certified,
        censored=False,
        audit_priority=not certified,
        protected_random_audit=inputs.protected_random_audit,
        target_score=target_score,
        nuisance_burden=None,
        direct_target_score=direct_score,
        coupled_target_score=coupled_score,
        absence_certification_source=(absence.source if certified and absence is not None else None),
    )


def predict_visit_variant(
    inputs: VisitSystemInputs,
    variant: VisitSystemVariant,
    *,
    thresholds: VisitSystemThresholds | None = None,
) -> VisitPredictionRecord:
    """Predict one window under a named information architecture."""

    th = thresholds or VisitSystemThresholds()
    routes = inputs.target_routes
    direct = routes.direct_insect_score
    coupled = routes.coupled_target_score
    aggregate = max(direct, coupled)

    if variant is VisitSystemVariant.DIRECT_TARGET_ONLY:
        return _unsafe_target_only_prediction(
            inputs.window_id,
            target_score=direct,
            direct_score=direct,
            coupled_score=None,
            thresholds=th,
            protected_random_audit=inputs.protected_random_audit,
        )

    if variant is VisitSystemVariant.DIRECT_PLUS_COUPLED:
        return _unsafe_target_only_prediction(
            inputs.window_id,
            target_score=aggregate,
            direct_score=direct,
            coupled_score=coupled,
            thresholds=th,
            protected_random_audit=inputs.protected_random_audit,
        )

    if variant is VisitSystemVariant.TARGET_PLUS_NUISANCE:
        target_high = aggregate >= th.target_high
        target_low = aggregate <= th.target_low
        nuisance_high = inputs.nuisance.burden >= th.nuisance_high
        positive = target_high and not nuisance_high
        forced_absence = target_low and not nuisance_high
        ambiguous = nuisance_high and (target_high or target_low)
        return VisitPredictionRecord(
            window_id=inputs.window_id,
            retain_candidate=target_high,
            positive_evidence=positive,
            negative_evidence=False,
            censored=False,
            audit_priority=ambiguous,
            protected_random_audit=inputs.protected_random_audit,
            target_score=aggregate,
            nuisance_burden=inputs.nuisance.burden,
            direct_target_score=direct,
            coupled_target_score=coupled,
            forced_absence_call=forced_absence,
        )

    if variant is VisitSystemVariant.TARGET_PLUS_SUPPORT:
        return _support_aware_prediction(
            inputs,
            target_score=aggregate,
            direct_score=direct,
            coupled_score=coupled,
            thresholds=th,
        )

    if variant is VisitSystemVariant.FULL_TRIAD:
        triad = ProcessPreservingObservationTriadPolicy(
            target_high_threshold=th.target_high,
            target_low_threshold=th.target_low,
            nuisance_high_threshold=th.nuisance_high,
        ).decide(
            routes.to_target_evidence(),
            inputs.nuisance,
            inputs.support.support,
        )
        prediction = prediction_from_triad(
            inputs.window_id,
            triad,
            protected_random_audit=inputs.protected_random_audit,
            target_routes=routes,
            absence_evidence=inputs.absence_evidence,
        )
        # The full V15 architecture is inference-safe: a historical low-score
        # negative from the V14 triad is unresolved unless independently certified.
        if prediction.forced_absence_call:
            prediction = replace(
                prediction,
                forced_absence_call=False,
                audit_priority=True,
            )
        return prediction

    raise ValueError(f"unsupported visit system variant: {variant}")


def predict_all_visit_variants(
    inputs: VisitSystemInputs,
    *,
    thresholds: VisitSystemThresholds | None = None,
) -> dict[VisitSystemVariant, VisitPredictionRecord]:
    return {
        variant: predict_visit_variant(inputs, variant, thresholds=thresholds)
        for variant in VisitSystemVariant
    }


def evaluate_visit_system_variants(
    truth: list[VisitTruthRecord],
    inputs: list[VisitSystemInputs],
    *,
    thresholds: VisitSystemThresholds | None = None,
) -> dict[VisitSystemVariant, VisitValidationSummary]:
    """Evaluate all architectures after their predictions are emitted."""

    input_ids = [row.window_id for row in inputs]
    if len(set(input_ids)) != len(input_ids):
        raise ValueError("visit-system input window_id values must be unique")

    summaries: dict[VisitSystemVariant, VisitValidationSummary] = {}
    for variant in VisitSystemVariant:
        predictions = [predict_visit_variant(row, variant, thresholds=thresholds) for row in inputs]
        summaries[variant] = evaluate_visit_predictions(truth, predictions)
    return summaries
