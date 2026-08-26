"""Operational V15-v2 target/coupled/nuisance calibration layer.

PolliPi's direct field evidence is already a frozen ordinal 0 / 0.5 / 1 contract.
It must not be treated as a continuous probability and therefore does not need a
new arbitrary 0.25/0.65 field threshold.

The still-continuous coupled route and nuisance process measurements are instead
mapped, using development-only frozen calibration objects, onto the same ordinal
support scale:

- 0.0 = no positive support retained;
- 0.5 = intermediate / unresolved support;
- 1.0 = strong positive support.

The three nuisance effects are calibrated independently and may use different
predeclared measurement features. A single nuisance scalar cannot silently be
copied into false-event, missed-event and attribution risks.

This module defines runtime application of a *frozen* calibration. It does not
choose calibration values and provides no default thresholds.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from .coupled_field_measurement_v15 import FieldCoupledTargetMeasurement
from .nuisance_field_measurement_v15 import FieldNuisanceProcessMeasurement
from .observation_triad import NuisanceEvidence, TargetEvidence
from .target_field_adapter_v15 import V15DirectTargetFieldEvidence

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
STRUCTURAL_TARGET_HIGH = 1.0
STRUCTURAL_TARGET_LOW = 0.0
STRUCTURAL_NUISANCE_HIGH = 1.0


@dataclass(frozen=True, slots=True)
class OrdinalBoundary:
    low: float
    high: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.low < self.high <= 1.0:
            raise ValueError("ordinal boundary must satisfy 0 <= low < high <= 1")

    def encode(self, value: float) -> float:
        if not 0.0 <= value <= 1.0:
            raise ValueError("ordinal input must lie in [0, 1]")
        if value <= self.low:
            return 0.0
        if value >= self.high:
            return 1.0
        return 0.5


class NuisanceCalibrationFeature(str, Enum):
    """Positive exogenous-process measurements eligible for effect calibration."""

    REFERENCE_MOTION = "reference_motion_fraction"
    SPATIAL_COHERENCE = "scale_sensitive_spatial_coherence"
    REFERENCE_STATIONARITY = "reference_stationarity"
    REFERENCE_SPECTRAL_CONCENTRATION = "reference_spectral_concentration"
    TEMPORAL_PROCESS_SUPPORT = "temporal_process_support"
    PROCESS_INDEX = "nuisance_process_index"


@dataclass(frozen=True, slots=True)
class NuisanceEffectCalibration:
    feature: NuisanceCalibrationFeature
    boundary: OrdinalBoundary
    calibration_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.feature, NuisanceCalibrationFeature):
            raise TypeError("feature must be a NuisanceCalibrationFeature")
        if _SHA256_RE.fullmatch(self.calibration_sha256) is None:
            raise ValueError("calibration_sha256 must be lowercase 64-hex")


@dataclass(frozen=True, slots=True)
class V15OperationalCalibration:
    """Frozen runtime calibration object; all values must come from development."""

    coupled_boundary: OrdinalBoundary
    coupled_calibration_sha256: str
    false_event: NuisanceEffectCalibration
    missed_event: NuisanceEffectCalibration
    attribution: NuisanceEffectCalibration
    source_manifest_sha256: str

    def __post_init__(self) -> None:
        for name, value in (
            ("coupled_calibration_sha256", self.coupled_calibration_sha256),
            ("source_manifest_sha256", self.source_manifest_sha256),
        ):
            if _SHA256_RE.fullmatch(value) is None:
                raise ValueError(f"{name} must be lowercase 64-hex")


@dataclass(frozen=True, slots=True)
class V15OperationalEvidence:
    target: TargetEvidence
    nuisance: NuisanceEvidence
    direct_target_ordinal: float
    coupled_target_raw: float
    coupled_target_ordinal: float
    false_event_ordinal: float
    missed_event_ordinal: float
    attribution_ordinal: float


def _nuisance_feature_value(
    measurement: FieldNuisanceProcessMeasurement,
    feature: NuisanceCalibrationFeature,
) -> float:
    return float(getattr(measurement, feature.value))


def _effect_ordinal(
    measurement: FieldNuisanceProcessMeasurement,
    calibration: NuisanceEffectCalibration,
) -> float:
    return calibration.boundary.encode(
        _nuisance_feature_value(measurement, calibration.feature)
    )


def build_v15_operational_evidence(
    *,
    direct: V15DirectTargetFieldEvidence,
    coupled: FieldCoupledTargetMeasurement,
    nuisance: FieldNuisanceProcessMeasurement,
    calibration: V15OperationalCalibration,
) -> V15OperationalEvidence:
    """Apply an already-frozen ordinal calibration without tuning on this window."""

    direct_ordinal = float(direct.direct_target_score)
    if direct_ordinal not in {0.0, 0.5, 1.0}:
        raise ValueError("V15 direct field route must remain PolliPi ordinal 0/0.5/1")

    coupled_raw = float(coupled.usable_coupled_target_score)
    coupled_ordinal = calibration.coupled_boundary.encode(coupled_raw)
    target_ordinal = max(direct_ordinal, coupled_ordinal)

    false_event = _effect_ordinal(nuisance, calibration.false_event)
    missed_event = _effect_ordinal(nuisance, calibration.missed_event)
    attribution = _effect_ordinal(nuisance, calibration.attribution)

    nuisance_values = {
        "false_event": false_event,
        "missed_event": missed_event,
        "attribution": attribution,
    }
    dominant = max(nuisance_values, key=nuisance_values.get)

    return V15OperationalEvidence(
        target=TargetEvidence(
            score=target_ordinal,
            source_state=(
                f"pollipi:{direct.source_state}|direct:{direct_ordinal:.1f}|"
                f"coupled_ordinal:{coupled_ordinal:.1f}"
            ),
        ),
        nuisance=NuisanceEvidence(
            false_event_risk=false_event,
            missed_event_risk=missed_event,
            attribution_risk=attribution,
            dominant_source=f"ordinal:{dominant}",
        ),
        direct_target_ordinal=direct_ordinal,
        coupled_target_raw=coupled_raw,
        coupled_target_ordinal=coupled_ordinal,
        false_event_ordinal=false_event,
        missed_event_ordinal=missed_event,
        attribution_ordinal=attribution,
    )
