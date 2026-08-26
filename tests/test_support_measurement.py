import numpy as np
import pytest

from interaction_sensing.domain import BBox
from interaction_sensing.support_measurement import (
    PrimaryStreamMeasurementConfig,
    VisibilityMeasurement,
    measure_primary_stream_support,
)


def checkerboard(n_frames: int = 4, height: int = 20, width: int = 20) -> np.ndarray:
    y, x = np.indices((height, width))
    image = np.where((x + y) % 2 == 0, 40, 200).astype(np.uint8)
    return np.stack([image] * n_frames)


def timestamps(n: int, dt: float = 1.0 / 30.0) -> tuple[float, ...]:
    return tuple(i * dt for i in range(n))


def test_clear_primary_stream_produces_high_independent_support_measurements() -> None:
    frames = checkerboard()
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(2, 2, 18, 18),
        visibility=VisibilityMeasurement(0.95, "blinded_visibility_fixture"),
        timestamps_seconds=timestamps(len(frames)),
        config=PrimaryStreamMeasurementConfig(reference_gradient_magnitude=10.0, expected_frame_count=4),
    )
    assert result.target_zone_coverage.score == 1.0
    assert result.target_zone_visibility.score == 0.95
    assert result.spatial_resolution.score > 0.9
    assert result.photometric_sufficiency.score > 0.9
    assert result.temporal_continuity.score > 0.99


def test_partial_frame_loss_reduces_coverage_without_target_or_nuisance_scores() -> None:
    frames = checkerboard()
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(-10, 0, 10, 20),
        visibility=VisibilityMeasurement(1.0, "geometry_only_fixture"),
        timestamps_seconds=timestamps(len(frames)),
    )
    assert result.target_zone_coverage.score == 0.5


def test_visibility_is_explicit_and_not_inferred_from_low_motion_or_nuisance() -> None:
    frames = checkerboard()
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(0, 0, 20, 20),
        visibility=VisibilityMeasurement(0.15, "independent_occlusion_audit"),
        timestamps_seconds=timestamps(len(frames)),
    )
    assert result.target_zone_visibility.score == 0.15
    assert result.target_zone_coverage.score == 1.0


def test_saturation_reduces_photometric_sufficiency() -> None:
    frames = np.full((4, 20, 20), 255, dtype=np.uint8)
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(0, 0, 20, 20),
        visibility=VisibilityMeasurement(1.0, "fixture"),
        timestamps_seconds=timestamps(len(frames)),
    )
    assert result.photometric_sufficiency.score == 0.0


def test_low_spatial_structure_reduces_resolution_score() -> None:
    frames = np.full((4, 20, 20), 100, dtype=np.uint8)
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(0, 0, 20, 20),
        visibility=VisibilityMeasurement(1.0, "fixture"),
        timestamps_seconds=timestamps(len(frames)),
    )
    assert result.spatial_resolution.score == 0.0


def test_large_frame_gap_reduces_temporal_continuity() -> None:
    frames = checkerboard()
    result = measure_primary_stream_support(
        frames,
        target_zone=BBox(0, 0, 20, 20),
        visibility=VisibilityMeasurement(1.0, "fixture"),
        timestamps_seconds=(0.0, 1.0 / 30.0, 2.0 / 30.0, 1.0),
        config=PrimaryStreamMeasurementConfig(expected_frame_count=4),
    )
    assert result.temporal_continuity.score < 0.1


def test_timestamp_count_mismatch_fails_closed() -> None:
    frames = checkerboard()
    with pytest.raises(ValueError, match="timestamp count"):
        measure_primary_stream_support(
            frames,
            target_zone=BBox(0, 0, 20, 20),
            visibility=VisibilityMeasurement(1.0, "fixture"),
            timestamps_seconds=(0.0,),
        )
