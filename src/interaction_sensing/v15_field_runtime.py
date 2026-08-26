"""Field-safe V15-v2 runtime composition.

This module is the only intended route from calibrated field measurements into
the V15 comparison-system decision layer.  It prevents the historical raw
``VisitSystemThresholds`` defaults from leaking into held-out field execution.

Requirements are explicit:
- a frozen PolliPi direct-target record;
- a field coupled-response measurement (which may safely remain C=0 if no
  independent attribution source was validated);
- a field nuisance-process measurement;
- an already-frozen V15 operational calibration;
- an already-calibrated primary-stream support estimate.

The operational evidence is ordinal 0 / 0.5 / 1.  The downstream decision layer
therefore uses structural thresholds target_low=0, target_high=1, nuisance_high=1.
No fitted boundary is searched inside this runtime.
"""
from __future__ import annotations

from dataclasses import dataclass

from .coupled_field_measurement_v15 import FieldCoupledTargetMeasurement
from .nuisance_field_measurement_v15 import FieldNuisanceProcessMeasurement
from .support_estimation import PrimaryStreamSupportEstimate
from .target_field_adapter_v15 import V15DirectTargetFieldEvidence
from .v15_operational_calibration import (
    STRUCTURAL_NUISANCE_HIGH,
    STRUCTURAL_TARGET_HIGH,
    STRUCTURAL_TARGET_LOW,
    V15OperationalCalibration,
    V15OperationalEvidence,
    build_v15_operational_evidence,
)
from .visit_systems import (
    VisitSystemInputs,
    VisitSystemThresholds,
    VisitSystemVariant,
    predict_all_visit_variants,
    predict_visit_variant,
)
from .visit_validation import VisitPredictionRecord


FIELD_STRUCTURAL_THRESHOLDS = VisitSystemThresholds(
    target_high=STRUCTURAL_TARGET_HIGH,
    target_low=STRUCTURAL_TARGET_LOW,
    nuisance_high=STRUCTURAL_NUISANCE_HIGH,
)


@dataclass(frozen=True, slots=True)
class V15FieldRuntimeInputs:
    window_id: str
    direct: V15DirectTargetFieldEvidence
    coupled: FieldCoupledTargetMeasurement
    nuisance_measurement: FieldNuisanceProcessMeasurement
    support: PrimaryStreamSupportEstimate
    operational_calibration: V15OperationalCalibration
    protected_random_audit: bool = False

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        if self.coupled.window_id != self.window_id:
            raise ValueError("coupled measurement window_id must match runtime window_id")


def build_v15_field_system_inputs(
    inputs: V15FieldRuntimeInputs,
) -> tuple[VisitSystemInputs, V15OperationalEvidence]:
    """Compose already-calibrated T/C/N/O without fitting or threshold search."""

    operational = build_v15_operational_evidence(
        direct=inputs.direct,
        coupled=inputs.coupled,
        nuisance=inputs.nuisance_measurement,
        calibration=inputs.operational_calibration,
    )
    # Preserve calibrated route scores exactly. The direct route stays PolliPi
    # ordinal; the coupled route is represented by the already ordinalised value.
    target_routes = inputs.coupled.to_target_routes(
        direct_target_score=operational.direct_target_ordinal,
    )
    # TargetRouteEvidence recomputes coupled response * link from raw fields, so
    # for field runtime we intentionally carry the calibrated coupled ordinal as a
    # response with link=1.0.  This is an operational representation only; the raw
    # C components remain in `operational` and in the original measurement.
    target_routes = type(target_routes)(
        direct_insect_score=operational.direct_target_ordinal,
        coupled_response_score=operational.coupled_target_ordinal,
        target_link_confidence=1.0,
        source_state=(
            f"field_ordinal|direct:{operational.direct_target_ordinal:.1f}|"
            f"coupled:{operational.coupled_target_ordinal:.1f}"
        ),
    )
    system_inputs = VisitSystemInputs(
        window_id=inputs.window_id,
        target_routes=target_routes,
        nuisance=operational.nuisance,
        support=inputs.support,
        protected_random_audit=inputs.protected_random_audit,
        absence_evidence=None,
    )
    return system_inputs, operational


def predict_v15_field_variant(
    inputs: V15FieldRuntimeInputs,
    variant: VisitSystemVariant,
) -> VisitPredictionRecord:
    system_inputs, _ = build_v15_field_system_inputs(inputs)
    return predict_visit_variant(
        system_inputs,
        variant,
        thresholds=FIELD_STRUCTURAL_THRESHOLDS,
    )


def predict_all_v15_field_variants(
    inputs: V15FieldRuntimeInputs,
) -> dict[VisitSystemVariant, VisitPredictionRecord]:
    system_inputs, _ = build_v15_field_system_inputs(inputs)
    return predict_all_visit_variants(
        system_inputs,
        thresholds=FIELD_STRUCTURAL_THRESHOLDS,
    )
