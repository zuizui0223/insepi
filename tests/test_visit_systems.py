from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
)
from interaction_sensing.support_estimation import PrimaryStreamSupportEstimate
from interaction_sensing.support_truth import (
    PrimaryStreamSupportTruth,
    SupportComponentState,
)
from interaction_sensing.target_routes import TargetRouteEvidence
from interaction_sensing.visit_systems import (
    VisitSystemInputs,
    VisitSystemVariant,
    evaluate_visit_system_variants,
    predict_all_visit_variants,
    predict_visit_variant,
)
from interaction_sensing.visit_validation import VisitTruthRecord, VisitTruthState


def support_estimate(availability: ObservationAvailability, ceiling: float) -> PrimaryStreamSupportEstimate:
    support = ObservationSupport(ceiling, ceiling, ceiling, ceiling, ceiling)
    return PrimaryStreamSupportEstimate(
        availability=availability,
        support=support,
        limiting_component="target_zone_coverage",
        support_ceiling=ceiling,
    )


def support_truth(availability: ObservationAvailability) -> PrimaryStreamSupportTruth:
    adequate = SupportComponentState.ADEQUATE
    if availability is ObservationAvailability.OBSERVABLE:
        return PrimaryStreamSupportTruth(adequate, adequate, adequate, adequate, adequate, "system_test")
    if availability is ObservationAvailability.COMPROMISED:
        return PrimaryStreamSupportTruth(adequate, SupportComponentState.COMPROMISED, adequate, adequate, adequate, "system_test")
    return PrimaryStreamSupportTruth(adequate, SupportComponentState.FAILED, adequate, adequate, adequate, "system_test")


def inputs(
    *,
    direct: float,
    coupled_response: float,
    link: float,
    nuisance: float,
    availability: ObservationAvailability,
    ceiling: float,
    window_id: str = "w1",
) -> VisitSystemInputs:
    return VisitSystemInputs(
        window_id=window_id,
        target_routes=TargetRouteEvidence(direct, coupled_response, link),
        nuisance=NuisanceEvidence(nuisance, nuisance, nuisance),
        support=support_estimate(availability, ceiling),
    )


def test_explicit_support_prevents_false_absence_when_primary_stream_is_unobservable() -> None:
    row = inputs(
        direct=0.05,
        coupled_response=0.05,
        link=0.1,
        nuisance=0.05,
        availability=ObservationAvailability.UNOBSERVABLE,
        ceiling=0.10,
    )
    direct_only = predict_visit_variant(row, VisitSystemVariant.DIRECT_TARGET_ONLY)
    target_nuisance = predict_visit_variant(row, VisitSystemVariant.TARGET_PLUS_NUISANCE)
    target_support = predict_visit_variant(row, VisitSystemVariant.TARGET_PLUS_SUPPORT)
    full = predict_visit_variant(row, VisitSystemVariant.FULL_TRIAD)

    assert direct_only.negative_evidence is True
    assert target_nuisance.negative_evidence is True
    assert target_support.censored is True
    assert full.censored is True
    assert full.negative_evidence is False


def test_target_coupled_route_can_rescue_weak_direct_insect_evidence() -> None:
    row = inputs(
        direct=0.10,
        coupled_response=0.90,
        link=0.90,
        nuisance=0.05,
        availability=ObservationAvailability.OBSERVABLE,
        ceiling=0.90,
    )
    direct_only = predict_visit_variant(row, VisitSystemVariant.DIRECT_TARGET_ONLY)
    coupled = predict_visit_variant(row, VisitSystemVariant.DIRECT_PLUS_COUPLED)
    full = predict_visit_variant(row, VisitSystemVariant.FULL_TRIAD)

    assert direct_only.negative_evidence is True
    assert coupled.positive_evidence is True
    assert coupled.coupled_target_score == 0.81
    assert full.positive_evidence is True
    assert full.retain_candidate is True


def test_full_triad_preserves_observable_target_nuisance_superposition() -> None:
    row = inputs(
        direct=0.90,
        coupled_response=0.10,
        link=0.10,
        nuisance=0.90,
        availability=ObservationAvailability.OBSERVABLE,
        ceiling=0.90,
    )
    coupled_only = predict_visit_variant(row, VisitSystemVariant.DIRECT_PLUS_COUPLED)
    target_nuisance = predict_visit_variant(row, VisitSystemVariant.TARGET_PLUS_NUISANCE)
    full = predict_visit_variant(row, VisitSystemVariant.FULL_TRIAD)

    assert coupled_only.positive_evidence is True
    assert target_nuisance.retain_candidate is True
    assert target_nuisance.positive_evidence is False
    assert target_nuisance.audit_priority is True
    assert full.retain_candidate is True
    assert full.positive_evidence is True
    assert full.negative_evidence is False
    assert full.audit_priority is True


def test_compromised_support_is_ambiguous_not_false_absence() -> None:
    row = inputs(
        direct=0.05,
        coupled_response=0.05,
        link=0.10,
        nuisance=0.05,
        availability=ObservationAvailability.COMPROMISED,
        ceiling=0.50,
    )
    target_support = predict_visit_variant(row, VisitSystemVariant.TARGET_PLUS_SUPPORT)
    full = predict_visit_variant(row, VisitSystemVariant.FULL_TRIAD)
    assert target_support.negative_evidence is False
    assert target_support.censored is False
    assert target_support.audit_priority is True
    assert full.negative_evidence is False
    assert full.audit_priority is True


def test_all_variants_emit_one_prediction_for_same_window() -> None:
    row = inputs(
        direct=0.70,
        coupled_response=0.20,
        link=0.50,
        nuisance=0.20,
        availability=ObservationAvailability.OBSERVABLE,
        ceiling=0.90,
    )
    outputs = predict_all_visit_variants(row)
    assert set(outputs) == set(VisitSystemVariant)
    assert {prediction.window_id for prediction in outputs.values()} == {"w1"}


def test_system_comparison_quantifies_false_absence_and_coupled_rescue_on_same_windows() -> None:
    rows = [
        inputs(
            window_id="hidden-visit",
            direct=0.05,
            coupled_response=0.05,
            link=0.1,
            nuisance=0.05,
            availability=ObservationAvailability.UNOBSERVABLE,
            ceiling=0.10,
        ),
        inputs(
            window_id="coupled-visit",
            direct=0.10,
            coupled_response=0.90,
            link=0.90,
            nuisance=0.05,
            availability=ObservationAvailability.OBSERVABLE,
            ceiling=0.90,
        ),
        inputs(
            window_id="clean-absence",
            direct=0.05,
            coupled_response=0.05,
            link=0.10,
            nuisance=0.05,
            availability=ObservationAvailability.OBSERVABLE,
            ceiling=0.90,
        ),
    ]
    truth = [
        VisitTruthRecord(
            "hidden-visit",
            "b1",
            VisitTruthState.VISIT_EVENT,
            support_truth(ObservationAvailability.UNOBSERVABLE),
            event_id="event-hidden",
        ),
        VisitTruthRecord(
            "coupled-visit",
            "b1",
            VisitTruthState.VISIT_EVENT,
            support_truth(ObservationAvailability.OBSERVABLE),
            event_id="event-coupled",
            target_coupled_response_present=True,
        ),
        VisitTruthRecord(
            "clean-absence",
            "b1",
            VisitTruthState.NO_INSECT,
            support_truth(ObservationAvailability.OBSERVABLE),
        ),
    ]
    summaries = evaluate_visit_system_variants(truth, rows)

    direct = summaries[VisitSystemVariant.DIRECT_TARGET_ONLY]
    support = summaries[VisitSystemVariant.TARGET_PLUS_SUPPORT]
    full = summaries[VisitSystemVariant.FULL_TRIAD]

    assert direct.false_absence_count == 2  # hidden visit + weak-direct coupled visit
    assert support.false_absence_count == 0
    assert full.false_absence_count == 0
    assert full.indirect_target_rescue_count == 1
    assert full.indirect_target_rescue_rate == 1.0
