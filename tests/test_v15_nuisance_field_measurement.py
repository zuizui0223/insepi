import inspect

import numpy as np
import pytest

from interaction_sensing.domain import BBox
from interaction_sensing.nuisance_field_measurement_v15 import (
    NuisanceReferenceLayout,
    measure_field_nuisance_process,
)


FOCAL = BBox(0, 0, 4, 8)
REFERENCE = BBox(4, 0, 8, 8)
LAYOUT = NuisanceReferenceLayout((REFERENCE,), "fixed_geometry_reference")


def global_frames(offsets: list[float]) -> np.ndarray:
    frames = np.full((len(offsets), 8, 8), 100.0)
    for index, offset in enumerate(offsets):
        frames[index] += offset
    return frames


def localized_focal_frames(offsets: list[float]) -> np.ndarray:
    frames = np.full((len(offsets), 8, 8), 100.0)
    for index, offset in enumerate(offsets):
        frames[index, :, :4] += offset
    return frames


def test_field_nuisance_api_cannot_consume_target_scores_or_truth() -> None:
    parameters = tuple(inspect.signature(measure_field_nuisance_process).parameters)
    assert parameters == ("frames", "focal_zone", "reference_layout")


def test_spatially_coherent_global_motion_has_positive_process_index() -> None:
    result = measure_field_nuisance_process(
        global_frames([0, 5, 0, 15, 0, 10]),
        focal_zone=FOCAL,
        reference_layout=LAYOUT,
    )
    assert result.reference_motion_fraction > 0.0
    assert result.scale_sensitive_spatial_coherence > 0.99
    assert result.temporal_process_support > 0.0
    assert result.nuisance_process_index > 0.0


def test_local_target_zone_motion_does_not_become_spatially_coherent_nuisance() -> None:
    result = measure_field_nuisance_process(
        localized_focal_frames([0, 5, 0, 15, 0, 10]),
        focal_zone=FOCAL,
        reference_layout=LAYOUT,
    )
    assert result.focal_motion_fraction > 0.0
    assert result.reference_motion_fraction == 0.0
    assert result.scale_sensitive_spatial_coherence == 0.0
    assert result.nuisance_process_index == 0.0


def test_static_scene_emits_zero_dynamic_nuisance_support() -> None:
    result = measure_field_nuisance_process(
        np.full((6, 8, 8), 100.0),
        focal_zone=FOCAL,
        reference_layout=LAYOUT,
    )
    assert result.focal_motion_fraction == 0.0
    assert result.reference_motion_fraction == 0.0
    assert result.temporal_process_support == 0.0
    assert result.nuisance_process_index == 0.0


def test_process_index_is_scale_sensitive_even_when_coherence_is_same() -> None:
    weak = measure_field_nuisance_process(
        global_frames([0, 2, 0, 6, 0, 4]),
        focal_zone=FOCAL,
        reference_layout=LAYOUT,
    )
    strong = measure_field_nuisance_process(
        global_frames([0, 10, 0, 30, 0, 20]),
        focal_zone=FOCAL,
        reference_layout=LAYOUT,
    )
    assert weak.scale_sensitive_spatial_coherence == pytest.approx(
        strong.scale_sensitive_spatial_coherence
    )
    assert strong.reference_motion_fraction > weak.reference_motion_fraction
    assert strong.nuisance_process_index > weak.nuisance_process_index


def test_reference_layout_provenance_is_retained() -> None:
    layout = NuisanceReferenceLayout((REFERENCE,), "blinded_fixed_annulus_v1")
    result = measure_field_nuisance_process(
        global_frames([0, 5, 0, 15, 0, 10]),
        focal_zone=FOCAL,
        reference_layout=layout,
    )
    assert result.reference_zone_count == 1
    assert result.reference_layout_method == "blinded_fixed_annulus_v1"


def test_reference_zone_outside_frame_fails_closed() -> None:
    outside = NuisanceReferenceLayout((BBox(20, 20, 30, 30),), "invalid_test")
    with pytest.raises(ValueError, match="does not intersect the frame"):
        measure_field_nuisance_process(
            global_frames([0, 5, 0, 15, 0, 10]),
            focal_zone=FOCAL,
            reference_layout=outside,
        )
