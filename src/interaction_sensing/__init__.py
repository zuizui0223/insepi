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

__all__ = [
    "AuditRecord",
    "BBox",
    "Candidate",
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
    "TargetSpec",
    "TriadState",
    "profile_for",
]

__version__ = "0.1.0"
