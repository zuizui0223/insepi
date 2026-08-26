"""Public facade for the V15 empirical visit-validation bridge.

V14b/V14c remains the closed-world decision framework. This module exposes the
real-data validation layer without rewriting the V14 package-level API.
"""
from .absence_certification import TargetAbsenceEvidence
from .nuisance_field_measurement_v15 import (
    FieldNuisanceProcessMeasurement,
    NuisanceReferenceLayout,
    measure_field_nuisance_process,
)
from .support_estimation import (
    PrimaryStreamSupportEstimate,
    PrimaryStreamSupportEstimator,
    PrimaryStreamSupportMeasurements,
    SupportComponentMeasurement,
    SupportEstimatorValidationSummary,
    SupportMeasurementProvenance,
    evaluate_support_estimates,
)
from .v15_prefreeze import (
    A_MINUS_VALIDATION_ITEM,
    CORE_FREEZE_ITEMS,
    AbsenceStrategy,
    FreezeItem,
    FreezeStatus,
    PrefreezeGateState,
    PrefreezeReadiness,
    assert_ready_for_heldout,
    evaluate_prefreeze_registry,
    load_prefreeze_registry,
)
from .visit_systems import (
    VisitSystemInputs,
    VisitSystemThresholds,
    VisitSystemVariant,
    evaluate_visit_system_variants,
    predict_all_visit_variants,
    predict_visit_variant,
)
from .visit_validation import (
    CoupledResponseResolution,
    VisitPredictionRecord,
    VisitTruthRecord,
    VisitTruthResolution,
    VisitTruthState,
    VisitValidationSummary,
    evaluate_visit_predictions,
    prediction_from_triad,
)

__all__ = [
    "A_MINUS_VALIDATION_ITEM",
    "AbsenceStrategy",
    "CORE_FREEZE_ITEMS",
    "CoupledResponseResolution",
    "FieldNuisanceProcessMeasurement",
    "FreezeItem",
    "FreezeStatus",
    "NuisanceReferenceLayout",
    "PrefreezeGateState",
    "PrefreezeReadiness",
    "PrimaryStreamSupportEstimate",
    "PrimaryStreamSupportEstimator",
    "PrimaryStreamSupportMeasurements",
    "SupportComponentMeasurement",
    "SupportEstimatorValidationSummary",
    "SupportMeasurementProvenance",
    "TargetAbsenceEvidence",
    "VisitPredictionRecord",
    "VisitSystemInputs",
    "VisitSystemThresholds",
    "VisitSystemVariant",
    "VisitTruthRecord",
    "VisitTruthResolution",
    "VisitTruthState",
    "VisitValidationSummary",
    "assert_ready_for_heldout",
    "evaluate_prefreeze_registry",
    "evaluate_support_estimates",
    "evaluate_visit_predictions",
    "evaluate_visit_system_variants",
    "load_prefreeze_registry",
    "measure_field_nuisance_process",
    "predict_all_visit_variants",
    "predict_visit_variant",
    "prediction_from_triad",
]
