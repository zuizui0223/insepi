import pytest

from interaction_sensing.coupled_field_measurement_v15 import FieldCoupledTargetMeasurement
from interaction_sensing.nuisance_field_measurement_v15 import FieldNuisanceProcessMeasurement
from interaction_sensing.target_field_adapter_v15 import V15DirectTargetFieldEvidence
from interaction_sensing.v15_operational_calibration import (
    NuisanceCalibrationFeature,
    NuisanceEffectCalibration,
    OrdinalBoundary,
    STRUCTURAL_NUISANCE_HIGH,
    STRUCTURAL_TARGET_HIGH,
    STRUCTURAL_TARGET_LOW,
    V15OperationalCalibration,
    build_v15_operational_evidence,
)


A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def calibration() -> V15OperationalCalibration:
    return V15OperationalCalibration(
        coupled_boundary=OrdinalBoundary(0.2, 0.7),
        coupled_calibration_sha256=A,
        false_event=NuisanceEffectCalibration(
            NuisanceCalibrationFeature.PROCESS_INDEX,
            OrdinalBoundary(0.2, 0.6),
            B,
        ),
        missed_event=NuisanceEffectCalibration(
            NuisanceCalibrationFeature.REFERENCE_MOTION,
            OrdinalBoundary(0.1, 0.8),
            C,
        ),
        attribution=NuisanceEffectCalibration(
            NuisanceCalibrationFeature.SPATIAL_COHERENCE,
            OrdinalBoundary(0.3, 0.9),
            D,
        ),
        source_manifest_sha256=E,
    )


def coupled(score: float) -> FieldCoupledTargetMeasurement:
    # usable score is constrained to response * link; choose link=1 for simple tests.
    return FieldCoupledTargetMeasurement(
        window_id="w1",
        focal_motion_fraction=score,
        reference_motion_fraction=0.0,
        local_response_excess=1.0 if score > 0 else 0.0,
        coupled_response_score=score,
        target_link_confidence=1.0,
        usable_coupled_target_score=score,
        attribution_source="independent_contact_geometry",
        reference_zone_count=1,
        reference_layout_method="prebound",
    )


def nuisance() -> FieldNuisanceProcessMeasurement:
    return FieldNuisanceProcessMeasurement(
        focal_motion_fraction=0.7,
        reference_motion_fraction=0.5,
        scale_sensitive_spatial_coherence=0.95,
        reference_stationarity=0.4,
        reference_spectral_concentration=0.5,
        temporal_process_support=0.5,
        nuisance_process_index=0.65,
        reference_zone_count=2,
        reference_layout_method="prebound",
    )


def direct(score: float, state: str) -> V15DirectTargetFieldEvidence:
    return V15DirectTargetFieldEvidence(
        direct_target_score=score,
        source_state=state,
        source_scale="ordinal-v14-reference",
    )


def test_direct_pollipi_ordinal_is_not_rethresholded() -> None:
    output = build_v15_operational_evidence(
        direct=direct(0.5, "uncertain_local_activity"),
        coupled=coupled(0.0),
        nuisance=nuisance(),
        calibration=calibration(),
    )
    assert output.direct_target_ordinal == 0.5
    assert output.target.score == 0.5
    assert STRUCTURAL_TARGET_LOW == 0.0
    assert STRUCTURAL_TARGET_HIGH == 1.0
    assert STRUCTURAL_NUISANCE_HIGH == 1.0


def test_strong_direct_or_calibrated_coupled_route_can_supply_strong_positive_target_support() -> None:
    direct_strong = build_v15_operational_evidence(
        direct=direct(1.0, "strong_visitation_candidate"),
        coupled=coupled(0.0),
        nuisance=nuisance(),
        calibration=calibration(),
    )
    assert direct_strong.target.score == 1.0

    coupled_strong = build_v15_operational_evidence(
        direct=direct(0.0, "no_activity"),
        coupled=coupled(0.8),
        nuisance=nuisance(),
        calibration=calibration(),
    )
    assert coupled_strong.coupled_target_ordinal == 1.0
    assert coupled_strong.target.score == 1.0


def test_three_nuisance_effects_are_calibrated_separately() -> None:
    output = build_v15_operational_evidence(
        direct=direct(0.0, "environmental_noise"),
        coupled=coupled(0.0),
        nuisance=nuisance(),
        calibration=calibration(),
    )
    # process index .65 => false-event strong; reference motion .5 => missed intermediate;
    # spatial coherence .95 => attribution strong.
    assert output.false_event_ordinal == 1.0
    assert output.missed_event_ordinal == 0.5
    assert output.attribution_ordinal == 1.0
    assert output.nuisance.false_event_risk == 1.0
    assert output.nuisance.missed_event_risk == 0.5
    assert output.nuisance.attribution_risk == 1.0


def test_calibration_has_no_default_thresholds_and_rejects_nonordinal_direct_score() -> None:
    with pytest.raises(TypeError):
        V15OperationalCalibration()  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="ordinal 0/0.5/1"):
        build_v15_operational_evidence(
            direct=direct(0.65, "development-only-invalid"),
            coupled=coupled(0.0),
            nuisance=nuisance(),
            calibration=calibration(),
        )
