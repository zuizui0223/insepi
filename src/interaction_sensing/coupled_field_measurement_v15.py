"""Development field bridge for V15-v2 target-coupled response evidence.

This module deliberately separates two quantities that were only abstract inputs
before V15-v2:

1. ``coupled_response_score`` -- a continuous, uncalibrated measurement that the
   focal biological target shows local motion in excess of neighbouring context;
2. ``target_link_confidence`` -- independent attribution evidence that the local
   response is linked to the focal actor/interaction.

A local flower response alone is *not* enough to claim a target interaction. If no
independent attribution cue is supplied, ``target_link_confidence`` and the usable
coupled target route are exactly zero. This preserves the V14b result that
indirect-only local response can remain fundamentally unattributable.

Runtime inputs never include biological truth, coupling truth, nuisance truth, O
labels, or PolliPi target scores. This is a development measurement baseline, not
a field-calibrated coupled observer and not a held-out-ready component.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import sqrt
import re

import numpy as np

from .domain import BBox
from .target_routes import TargetRouteEvidence

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CoupledAttributionSource(str, Enum):
    """Allowed independent source classes for target-link evidence.

    The enum intentionally has no PolliPi/direct-target or nuisance-derived source.
    A concrete field implementation still requires its own development calibration
    and provenance before V15-v2 may be frozen.
    """

    CONTACT_GEOMETRY = "independent_contact_geometry"
    SECONDARY_SENSOR = "independent_secondary_sensor"
    PREVALIDATED_LINK_MODEL = "prevalidated_independent_link_model"


@dataclass(frozen=True, slots=True)
class CoupledResponseReferenceLayout:
    """Neighbour/reference regions chosen without system-output or truth leakage."""

    reference_zones: tuple[BBox, ...]
    method: str

    def __post_init__(self) -> None:
        if not self.reference_zones:
            raise ValueError("at least one coupled-response reference zone is required")
        if not self.method.strip():
            raise ValueError("reference-zone selection method cannot be empty")


@dataclass(frozen=True, slots=True)
class IndependentAttributionCue:
    """Externally supplied evidence linking a local response to the focal actor.

    ``evidence_sha256`` binds the cue to retained raw/provenance material.
    ``calibration_sha256`` binds the scoring rule used to create ``score``. The
    actual source must be independently validated before the coupled-field core
    item can become FROZEN.
    """

    window_id: str
    score: float
    source: CoupledAttributionSource
    source_id: str
    evidence_sha256: str
    calibration_sha256: str

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("attribution score must lie in [0, 1]")
        if not isinstance(self.source, CoupledAttributionSource):
            raise TypeError("source must be a CoupledAttributionSource")
        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")
        if _SHA256_RE.fullmatch(self.evidence_sha256) is None:
            raise ValueError("evidence_sha256 must be lowercase 64-hex")
        if _SHA256_RE.fullmatch(self.calibration_sha256) is None:
            raise ValueError("calibration_sha256 must be lowercase 64-hex")


@dataclass(frozen=True, slots=True)
class FieldCoupledTargetMeasurement:
    """Continuous coupled-response measurement before field calibration."""

    window_id: str
    focal_motion_fraction: float
    reference_motion_fraction: float
    local_response_excess: float
    coupled_response_score: float
    target_link_confidence: float
    usable_coupled_target_score: float
    attribution_source: str | None
    reference_zone_count: int
    reference_layout_method: str

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        for name, value in (
            ("focal_motion_fraction", self.focal_motion_fraction),
            ("reference_motion_fraction", self.reference_motion_fraction),
            ("local_response_excess", self.local_response_excess),
            ("coupled_response_score", self.coupled_response_score),
            ("target_link_confidence", self.target_link_confidence),
            ("usable_coupled_target_score", self.usable_coupled_target_score),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.reference_zone_count <= 0:
            raise ValueError("reference_zone_count must be positive")
        if not self.reference_layout_method.strip():
            raise ValueError("reference_layout_method cannot be empty")
        if self.target_link_confidence == 0.0 and self.usable_coupled_target_score != 0.0:
            raise ValueError("usable coupled score must be zero without attribution support")

    def to_target_routes(self, *, direct_target_score: float = 0.0) -> TargetRouteEvidence:
        """Compose with a separately supplied direct route without changing either."""

        return TargetRouteEvidence(
            direct_insect_score=direct_target_score,
            coupled_response_score=self.coupled_response_score,
            target_link_confidence=self.target_link_confidence,
            source_state=f"field_coupled:{self.attribution_source or 'unattributed'}",
        )


def _validate_frames(frames: np.ndarray) -> np.ndarray:
    array = np.asarray(frames)
    if array.ndim != 3:
        raise ValueError("frames must have shape (time, height, width)")
    if min(array.shape) <= 0 or array.shape[0] < 3:
        raise ValueError("coupled field measurement requires at least three non-empty frames")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError("frames must contain numeric grayscale values")
    array = array.astype(np.float64, copy=False)
    if not np.all(np.isfinite(array)):
        raise ValueError("frames must contain only finite values")
    if float(np.min(array)) < 0.0 or float(np.max(array)) > 255.0:
        raise ValueError("coupled field baseline expects grayscale values in [0,255]")
    return array


def _roi_slices(zone: BBox, *, height: int, width: int, name: str) -> tuple[slice, slice]:
    left = max(0.0, zone.left)
    top = max(0.0, zone.top)
    right = min(float(width), zone.right)
    bottom = min(float(height), zone.bottom)
    if right <= left or bottom <= top:
        raise ValueError(f"{name} does not intersect the frame")
    x0 = max(0, min(width - 1, int(np.floor(left))))
    y0 = max(0, min(height - 1, int(np.floor(top))))
    x1 = max(x0 + 1, min(width, int(np.ceil(right))))
    y1 = max(y0 + 1, min(height, int(np.ceil(bottom))))
    return slice(y0, y1), slice(x0, x1)


def _motion_trace(array: np.ndarray, zone: BBox, *, name: str) -> np.ndarray:
    _, height, width = array.shape
    ys, xs = _roi_slices(zone, height=height, width=width, name=name)
    region = array[:, ys, xs]
    return np.mean(np.abs(np.diff(region, axis=0)), axis=(1, 2)) / 255.0


def _rms(trace: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(trace))))


def measure_field_coupled_response(
    frames: np.ndarray,
    *,
    window_id: str,
    focal_zone: BBox,
    reference_layout: CoupledResponseReferenceLayout,
    attribution_cue: IndependentAttributionCue | None = None,
) -> FieldCoupledTargetMeasurement:
    """Measure local target response and combine only with independent attribution.

    The response index is the geometric mean of (a) local response excess over the
    median neighbour/reference trace and (b) absolute focal motion magnitude.
    It is an uncalibrated process score, not a probability.

    Crucially, no attribution cue means ``target_link_confidence = 0`` even if a
    strong local response is observed. This blocks arbitrary flower motion from
    becoming positive target evidence.
    """

    if not window_id.strip():
        raise ValueError("window_id cannot be empty")
    if attribution_cue is not None and attribution_cue.window_id != window_id:
        raise ValueError("attribution cue window_id must match the measured window")

    array = _validate_frames(frames)
    focal_trace = _motion_trace(array, focal_zone, name="focal_zone")
    reference_traces = np.vstack(
        [
            _motion_trace(array, zone, name=f"reference_zone[{index}]")
            for index, zone in enumerate(reference_layout.reference_zones)
        ]
    )
    reference_trace = np.median(reference_traces, axis=0)

    focal_rms = _rms(focal_trace)
    reference_rms = _rms(reference_trace)
    total = focal_rms + reference_rms
    local_excess = 0.0 if total <= 1e-15 else max(0.0, (focal_rms - reference_rms) / total)
    response = sqrt(max(0.0, local_excess * focal_rms))

    link = 0.0 if attribution_cue is None else attribution_cue.score
    usable = response * link
    return FieldCoupledTargetMeasurement(
        window_id=window_id,
        focal_motion_fraction=max(0.0, min(1.0, focal_rms)),
        reference_motion_fraction=max(0.0, min(1.0, reference_rms)),
        local_response_excess=max(0.0, min(1.0, local_excess)),
        coupled_response_score=max(0.0, min(1.0, response)),
        target_link_confidence=link,
        usable_coupled_target_score=max(0.0, min(1.0, usable)),
        attribution_source=None if attribution_cue is None else attribution_cue.source.value,
        reference_zone_count=len(reference_layout.reference_zones),
        reference_layout_method=reference_layout.method,
    )
