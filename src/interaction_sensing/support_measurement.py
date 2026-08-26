"""Transparent primary-stream measurement adapter for V15 observation support.

This module measures properties of the camera channel without target evidence,
nuisance scores, biological truth, or nuisance truth.  Four components are
computed from frame bytes / timing / geometry.  Target-zone visibility remains an
explicit independent measurement because silently defining visibility from low
insect evidence would make the support estimator circular.

The adapter is a development baseline, not a field-calibrated observability model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .domain import BBox
from .support_estimation import (
    PrimaryStreamSupportMeasurements,
    SupportComponentMeasurement,
    SupportMeasurementProvenance,
)


@dataclass(frozen=True, slots=True)
class PrimaryStreamMeasurementConfig:
    low_clip_value: float = 5.0
    high_clip_value: float = 250.0
    minimum_useful_dynamic_range: float = 30.0
    reference_gradient_magnitude: float = 12.0
    expected_frame_interval_seconds: float = 1.0 / 30.0
    expected_frame_count: int | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.low_clip_value < self.high_clip_value <= 255.0:
            raise ValueError("clip values must satisfy 0 <= low < high <= 255")
        if self.minimum_useful_dynamic_range <= 0:
            raise ValueError("minimum_useful_dynamic_range must be positive")
        if self.reference_gradient_magnitude <= 0:
            raise ValueError("reference_gradient_magnitude must be positive")
        if self.expected_frame_interval_seconds <= 0:
            raise ValueError("expected_frame_interval_seconds must be positive")
        if self.expected_frame_count is not None and self.expected_frame_count <= 0:
            raise ValueError("expected_frame_count must be positive when provided")


@dataclass(frozen=True, slots=True)
class VisibilityMeasurement:
    """Independent estimate/audit of visible focal-zone fraction."""

    visible_fraction: float
    method: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.visible_fraction <= 1.0:
            raise ValueError("visible_fraction must lie in [0, 1]")
        if not self.method.strip():
            raise ValueError("visibility method cannot be empty")


def _validate_frames(frames: np.ndarray) -> np.ndarray:
    array = np.asarray(frames)
    if array.ndim == 2:
        array = array[None, ...]
    if array.ndim != 3:
        raise ValueError("frames must have shape (time, height, width) or (height, width)")
    if array.shape[0] == 0 or array.shape[1] == 0 or array.shape[2] == 0:
        raise ValueError("frames cannot contain an empty dimension")
    if not np.issubdtype(array.dtype, np.number):
        raise TypeError("frames must contain numeric grayscale values")
    return array.astype(np.float64, copy=False)


def _target_intersection(target_zone: BBox, height: int, width: int) -> tuple[int, int, int, int, float]:
    left = max(0.0, target_zone.left)
    top = max(0.0, target_zone.top)
    right = min(float(width), target_zone.right)
    bottom = min(float(height), target_zone.bottom)
    if right <= left or bottom <= top:
        return 0, 0, 0, 0, 0.0
    intersection_area = (right - left) * (bottom - top)
    coverage = max(0.0, min(1.0, intersection_area / target_zone.area))
    x0 = max(0, min(width - 1, int(np.floor(left))))
    y0 = max(0, min(height - 1, int(np.floor(top))))
    x1 = max(x0 + 1, min(width, int(np.ceil(right))))
    y1 = max(y0 + 1, min(height, int(np.ceil(bottom))))
    return x0, y0, x1, y1, coverage


def _photometric_score(region: np.ndarray, config: PrimaryStreamMeasurementConfig) -> float:
    flat = region.reshape(-1)
    usable_fraction = float(np.mean((flat > config.low_clip_value) & (flat < config.high_clip_value)))
    p05, p95 = np.percentile(flat, [5.0, 95.0])
    dynamic_factor = max(0.0, min(1.0, float(p95 - p05) / config.minimum_useful_dynamic_range))
    return min(usable_fraction, dynamic_factor)


def _gradient_magnitude_score(region: np.ndarray, config: PrimaryStreamMeasurementConfig) -> float:
    # Median frame prevents one transient frame from defining spatial support.
    image = np.median(region, axis=0)
    if image.shape[0] < 2 or image.shape[1] < 2:
        return 0.0
    gx = np.diff(image, axis=1)
    gy = np.diff(image, axis=0)
    gx_mean = float(np.mean(np.abs(gx)))
    gy_mean = float(np.mean(np.abs(gy)))
    magnitude = 0.5 * (gx_mean + gy_mean)
    return max(0.0, min(1.0, magnitude / config.reference_gradient_magnitude))


def _temporal_score(
    timestamps_seconds: tuple[float, ...],
    n_frames: int,
    config: PrimaryStreamMeasurementConfig,
) -> float:
    if len(timestamps_seconds) != n_frames:
        raise ValueError("timestamp count must equal frame count")
    if n_frames == 1:
        return 1.0 if config.expected_frame_count in (None, 1) else min(1.0, 1.0 / config.expected_frame_count)
    timestamps = np.asarray(timestamps_seconds, dtype=np.float64)
    if not np.all(np.diff(timestamps) > 0):
        raise ValueError("timestamps must be strictly increasing")
    gaps = np.diff(timestamps)
    largest_gap = float(np.max(gaps))
    gap_score = min(1.0, config.expected_frame_interval_seconds / largest_gap)
    if config.expected_frame_count is None:
        count_score = 1.0
    else:
        count_score = min(1.0, n_frames / config.expected_frame_count)
    return max(0.0, min(count_score, gap_score))


def measure_primary_stream_support(
    frames: np.ndarray,
    *,
    target_zone: BBox,
    visibility: VisibilityMeasurement,
    timestamps_seconds: tuple[float, ...],
    config: PrimaryStreamMeasurementConfig | None = None,
) -> PrimaryStreamSupportMeasurements:
    """Measure five O components from primary-stream information only.

    ``visibility`` is intentionally a separate input with provenance.  It may be
    supplied by a blinded visibility/occlusion audit or an independently validated
    visibility model, but must not be derived from PolliPi target score or InsePi
    nuisance risk inside this function.
    """

    cfg = config or PrimaryStreamMeasurementConfig()
    array = _validate_frames(frames)
    n_frames, height, width = array.shape
    x0, y0, x1, y1, coverage = _target_intersection(target_zone, height, width)

    if coverage <= 0.0:
        photometry = 0.0
        resolution = 0.0
    else:
        region = array[:, y0:y1, x0:x1]
        photometry = _photometric_score(region, cfg)
        resolution = _gradient_magnitude_score(region, cfg)

    temporal = _temporal_score(timestamps_seconds, n_frames, cfg)

    return PrimaryStreamSupportMeasurements(
        target_zone_coverage=SupportComponentMeasurement(
            coverage,
            SupportMeasurementProvenance.CAMERA_GEOMETRY,
            "bbox_intersection_over_expected_target_zone",
        ),
        target_zone_visibility=SupportComponentMeasurement(
            visibility.visible_fraction,
            SupportMeasurementProvenance.TARGET_ZONE_VISIBILITY_AUDIT,
            visibility.method,
        ),
        spatial_resolution=SupportComponentMeasurement(
            resolution,
            SupportMeasurementProvenance.IMAGE_RESOLUTION_AUDIT,
            "median_roi_gradient_relative_to_calibration_reference",
        ),
        photometric_sufficiency=SupportComponentMeasurement(
            photometry,
            SupportMeasurementProvenance.PHOTOMETRIC_AUDIT,
            "roi_nonclipped_fraction_and_robust_dynamic_range",
        ),
        temporal_continuity=SupportComponentMeasurement(
            temporal,
            SupportMeasurementProvenance.FRAME_TIMING_AUDIT,
            "frame_count_and_largest_gap_relative_to_expected_timing",
        ),
    )
