"""Noise-first, error-aware sensing for complex natural scenes."""

from .domain import (
    AuditRecord,
    BBox,
    Candidate,
    ErrorClass,
    InteractionEvent,
    InteractionState,
    SceneState,
    TargetSpec,
)
from .noise import (
    NoiseFirstPolicy,
    NoiseObservation,
    NoiseSource,
    ObservabilityDecision,
    ObservabilityState,
)
from .nuisance_effects import NuisanceEffect, NuisanceProfile, profile_for
from .observation_triad import (
    InferentialStatus,
    NuisanceEvidence,
    ObservationAvailability,
    ObservationInterpretation,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
    TriadState,
)
from .target_routes import TargetEvidenceRoute, TargetRouteEvidence
from .visit_observation import (
    DiagnosticAction,
    VisitObservationRecord,
    VisitObservationStatus,
    VisitObservationSummary,
    diagnostic_actions,
    summarise_visit_observations,
    visit_record_from_interpretation,
)

__all__ = [
    "AuditRecord",
    "BBox",
    "Candidate",
    "DiagnosticAction",
    "ErrorClass",
    "InferentialStatus",
    "InteractionEvent",
    "InteractionState",
    "NoiseFirstPolicy",
    "NoiseObservation",
    "NoiseSource",
    "NuisanceEffect",
    "NuisanceEvidence",
    "NuisanceProfile",
    "ObservationAvailability",
    "ObservationInterpretation",
    "ObservationSupport",
    "ObservationTriadPolicy",
    "ObservabilityDecision",
    "ObservabilityState",
    "SceneState",
    "TargetEvidence",
    "TargetEvidenceRoute",
    "TargetRouteEvidence",
    "TargetSpec",
    "TriadState",
    "VisitObservationRecord",
    "VisitObservationStatus",
    "VisitObservationSummary",
    "diagnostic_actions",
    "profile_for",
    "summarise_visit_observations",
    "visit_record_from_interpretation",
]

__version__ = "0.1.0"
