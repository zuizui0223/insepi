from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationAvailability,
    ObservationSupport,
)
from interaction_sensing.support_estimation import PrimaryStreamSupportEstimate
from interaction_sensing.target_routes import TargetRouteEvidence
from interaction_sensing.visit_systems import (
    VisitSystemInputs,
    VisitSystemVariant,
    predict_all_visit_variants,
    predict_visit_variant,
)


def support_estimate(availability: ObservationAvailability, ceiling: float) -> PrimaryStreamSupportEstimate:
    support = ObservationSupport(ceiling, ceiling, ceiling, ceiling, ceiling)
    return PrimaryStreamSupportEstimate(
        availability=availability,
        support=support,
        limiting_component="target_zone_coverage",
        support_ceiling=ceiling,
    )


def inputs(
    *,
    direct: float,
    coupled_response: float,
    link: float,
    nuisance: float,
    availability: ObservationAvailability,
    ceiling: float,
) -> VisitSystemInputs:
    return VisitSystemInputs(
        window_id="w1",
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


def test_high_nuisance_keeps_target_candidate_but_prevents_clean_positive_claim() -> None:
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
    assert full.positive_evidence is False
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
