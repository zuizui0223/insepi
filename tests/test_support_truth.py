from interaction_sensing.observation_triad import ObservationAvailability
from interaction_sensing.support_truth import (
    PrimaryStreamSupportTruth,
    SupportComponentState,
    SupportTruthResolution,
)


def support(**overrides: SupportComponentState) -> PrimaryStreamSupportTruth:
    values = {
        "target_zone_coverage": SupportComponentState.ADEQUATE,
        "target_zone_visibility": SupportComponentState.ADEQUATE,
        "spatial_resolution": SupportComponentState.ADEQUATE,
        "photometric_sufficiency": SupportComponentState.ADEQUATE,
        "temporal_continuity": SupportComponentState.ADEQUATE,
    }
    values.update(overrides)
    return PrimaryStreamSupportTruth(**values, annotation_method="blinded_primary_stream_review")


def test_all_components_adequate_is_observable() -> None:
    truth = support()
    assert truth.resolution is SupportTruthResolution.RESOLVED
    assert truth.availability is ObservationAvailability.OBSERVABLE
    assert truth.limiting_components == ()


def test_single_compromised_component_is_not_unobservable() -> None:
    truth = support(target_zone_visibility=SupportComponentState.COMPROMISED)
    assert truth.availability is ObservationAvailability.COMPROMISED
    assert truth.limiting_components == ("target_zone_visibility",)


def test_any_failed_necessary_component_is_unobservable() -> None:
    for component in (
        "target_zone_coverage",
        "target_zone_visibility",
        "spatial_resolution",
        "photometric_sufficiency",
        "temporal_continuity",
    ):
        truth = support(**{component: SupportComponentState.FAILED})
        assert truth.resolution is SupportTruthResolution.RESOLVED
        assert truth.availability is ObservationAvailability.UNOBSERVABLE
        assert component in truth.limiting_components


def test_unresolved_component_is_not_silently_collapsed_to_observable_or_unobservable() -> None:
    truth = support(spatial_resolution=SupportComponentState.UNRESOLVED)
    assert truth.resolution is SupportTruthResolution.UNRESOLVED
    assert truth.availability is None


def test_known_failure_is_sufficient_even_if_another_component_is_unresolved() -> None:
    truth = support(
        target_zone_coverage=SupportComponentState.FAILED,
        photometric_sufficiency=SupportComponentState.UNRESOLVED,
    )
    assert truth.resolution is SupportTruthResolution.RESOLVED
    assert truth.availability is ObservationAvailability.UNOBSERVABLE


def test_support_truth_has_no_nuisance_or_target_score_input() -> None:
    fields = set(PrimaryStreamSupportTruth.__dataclass_fields__)
    assert "nuisance" not in " ".join(fields)
    assert "target_score" not in fields
    assert "observability_score" not in fields
