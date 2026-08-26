"""Primary-stream nuisance-process measurement baseline for V15-v2.

This adapter closes one implementation gap between the frozen V14b synthetic
nuisance observer and later field validation.  It measures continuous process
features directly from grayscale primary-stream frames while deliberately not
consuming:

- PolliPi/target scores;
- biological-event truth;
- target-coupling truth;
- nuisance truth;
- observation-support labels.

The output is an **uncalibrated process index**, not a nuisance probability or a
field decision threshold.  A later development/freeze step must map these
measurements to the false-event / missed-event / attribution effects used by the
V15 system.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .domain import BBox


@dataclass(frozen=True, slots=True)
class NuisanceReferenceLayout:
    """Reference regions selected independently of target-observer output."""

    reference_zones: tuple[BBox, ...]
    method: str

    def __post_init__(self) -> None:
        if not self.reference_zones:
            raise ValueError("at least one nuisance reference zone is required")
        if not self.method.strip():
            raise ValueError("reference-zone selection method cannot be empty")


@dataclass(frozen=True, slots=True)
class FieldNuisanceProcessMeasurement:
    """Continuous field measurements before nuisance-risk calibration."""

    focal_motion_fraction: float
    reference_motion_fraction: float
    scale_sensitive_spatial_coherence: float
    reference_stationarity: float
    reference_spectral_concentration: float
    temporal_process_support: float
    nuisance_process_index: float
    reference_zone_count: int
    reference_layout_method: str

    def __post_init__(self) -> None:
        for name, value in (
            ("focal_motion_fraction", self.focal_motion_fraction),
            ("reference_motion_fraction", self.reference_motion_fraction),
            ("scale_sensitive_spatial_coherence", self.scale_sensitive_spatial_coherence),
            ("reference_stationarity", self.reference_stationarity),
            ("reference_spectral_concentration", self.reference_spectral_concentration),
            ("temporal_process_support", self.temporal_process_support),
            ("nuisance_process_index", self.nuisance_process_index),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.reference_zone_count <= 0:
            raise ValueError("reference_zone_count must be positive")
        if not self.reference_layout_method.strip():
            raise ValueError("reference_layout_method cannot be empty")


def _validate_frames(frames: np.ndarray) -> np.ndarray:
    array = np.asarray(frames)
    if array.ndim != 3:
        raise ValueError("frames must have shape (time, height, width)")
    if min(array.shape) <= 0:
        raise ValueError("frames cannot contain an empty dimension")
    if array.shape[0] < 3:
        raise ValueError("at least three frames are required for temporal nuisance measurement")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError("frames must contain numeric grayscale values")
    array = array.astype(np.float64, copy=False)
    if not np.all(np.isfinite(array)):
        raise ValueError("frames must contain only finite values")
    if float(np.min(array)) < 0.0 or float(np.max(array)) > 255.0:
        raise ValueError("field nuisance baseline expects grayscale values in [0, 255]")
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


def _positive_correlation(left: np.ndarray, right: np.ndarray) -> float:
    left_centered = left - np.mean(left)
    right_centered = right - np.mean(right)
    left_norm = float(np.linalg.norm(left_centered))
    right_norm = float(np.linalg.norm(right_centered))
    if left_norm <= 1e-15 or right_norm <= 1e-15:
        # Two flat traces are not evidence for a coherent dynamic process.
        return 0.0
    correlation = float(np.dot(left_centered, right_centered) / (left_norm * right_norm))
    return max(0.0, min(1.0, correlation))


def _amplitude_agreement(left_rms: float, right_rms: float) -> float:
    total = left_rms + right_rms
    if total <= 1e-15:
        return 0.0
    return max(0.0, min(1.0, 2.0 * min(left_rms, right_rms) / total))


def _stationarity_score(trace: np.ndarray) -> float:
    if float(np.max(trace)) <= 1e-15:
        return 0.0
    midpoint = max(1, trace.size // 2)
    first = trace[:midpoint]
    second = trace[midpoint:]
    if second.size == 0:
        return 0.0
    first_level = _rms(first)
    second_level = _rms(second)
    total = first_level + second_level
    if total <= 1e-15:
        return 0.0
    return max(0.0, min(1.0, 1.0 - abs(first_level - second_level) / total))


def _spectral_concentration(trace: np.ndarray) -> float:
    centered = trace - np.mean(trace)
    if float(np.linalg.norm(centered)) <= 1e-15:
        return 0.0
    power = np.square(np.abs(np.fft.rfft(centered)))
    if power.size <= 1:
        return 0.0
    non_dc = power[1:]
    total = float(np.sum(non_dc))
    if total <= 1e-15:
        return 0.0
    return max(0.0, min(1.0, float(np.max(non_dc)) / total))


def measure_field_nuisance_process(
    frames: np.ndarray,
    *,
    focal_zone: BBox,
    reference_layout: NuisanceReferenceLayout,
) -> FieldNuisanceProcessMeasurement:
    """Measure exogenous-process structure without using target evidence.

    The focal and reference motion traces are frame-to-frame mean absolute
    differences normalized by the fixed 8-bit grayscale range.  Spatial
    coherence combines positive temporal correlation with **amplitude agreement**,
    avoiding the amplitude-invariance problem of Pearson correlation alone that
    was exposed by the V14a post-result diagnosis.

    The final ``nuisance_process_index`` is the geometric mean of:

    1. scale-sensitive focal/reference coherence;
    2. quasi-stationary or spectrally concentrated temporal structure;
    3. absolute reference-motion fraction.

    It is deliberately uncalibrated.  No field nuisance threshold is defined here.
    """

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
    correlation = _positive_correlation(focal_trace, reference_trace)
    amplitude = _amplitude_agreement(focal_rms, reference_rms)
    spatial = correlation * amplitude

    stationarity = _stationarity_score(reference_trace)
    spectral = _spectral_concentration(reference_trace)
    temporal = max(stationarity, spectral)

    # Retain absolute process amplitude so weak but perfectly correlated numerical
    # fluctuations do not receive high nuisance-process support.
    process = float(np.cbrt(max(0.0, spatial * temporal * reference_rms)))

    return FieldNuisanceProcessMeasurement(
        focal_motion_fraction=max(0.0, min(1.0, focal_rms)),
        reference_motion_fraction=max(0.0, min(1.0, reference_rms)),
        scale_sensitive_spatial_coherence=max(0.0, min(1.0, spatial)),
        reference_stationarity=stationarity,
        reference_spectral_concentration=spectral,
        temporal_process_support=temporal,
        nuisance_process_index=max(0.0, min(1.0, process)),
        reference_zone_count=len(reference_layout.reference_zones),
        reference_layout_method=reference_layout.method,
    )
