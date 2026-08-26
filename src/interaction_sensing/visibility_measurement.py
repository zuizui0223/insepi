"""Independent target-zone visibility measurement for V15.

This adapter does not detect insects and does not classify nuisance.  It measures
what fraction of a pre-defined focal interaction zone is visibly available in the
primary stream, given an expected target-zone mask and an independently produced
visible-zone mask.

The visible mask may come from blinded manual annotation or from a separately
validated visibility model trained only on visibility labels.  It must not be
constructed from visit truth, target evidence, or nuisance risk.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .support_measurement import VisibilityMeasurement


@dataclass(frozen=True, slots=True)
class VisibilityMaskResult:
    expected_pixels: int
    visible_pixels: int
    visible_fraction: float
    measurement: VisibilityMeasurement


def _binary_mask(mask: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(mask)
    if array.ndim != 2:
        raise ValueError(f"{name} must be a 2D mask")
    if array.size == 0:
        raise ValueError(f"{name} cannot be empty")
    if array.dtype == np.bool_:
        return array
    unique = np.unique(array)
    if not set(unique.tolist()) <= {0, 1}:
        raise ValueError(f"{name} must contain only boolean/0/1 values")
    return array.astype(bool)


def visibility_from_masks(
    expected_target_zone_mask: np.ndarray,
    visible_target_zone_mask: np.ndarray,
    *,
    method: str = "independent_target_zone_visibility_mask",
) -> VisibilityMaskResult:
    """Measure visible target-zone fraction from independent binary masks."""

    expected = _binary_mask(expected_target_zone_mask, "expected_target_zone_mask")
    visible = _binary_mask(visible_target_zone_mask, "visible_target_zone_mask")
    if expected.shape != visible.shape:
        raise ValueError("visibility masks must have identical shape")
    expected_pixels = int(expected.sum())
    if expected_pixels == 0:
        raise ValueError("expected target-zone mask must contain at least one pixel")
    if np.any(visible & ~expected):
        raise ValueError("visible target-zone mask must be a subset of the expected target-zone mask")

    visible_pixels = int(visible.sum())
    fraction = visible_pixels / expected_pixels
    return VisibilityMaskResult(
        expected_pixels=expected_pixels,
        visible_pixels=visible_pixels,
        visible_fraction=fraction,
        measurement=VisibilityMeasurement(fraction, method),
    )
