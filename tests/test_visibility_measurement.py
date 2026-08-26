import numpy as np
import pytest

from interaction_sensing.visibility_measurement import visibility_from_masks


def test_visibility_fraction_is_visible_over_expected_zone() -> None:
    expected = np.zeros((4, 4), dtype=bool)
    expected[1:3, 1:3] = True
    visible = np.zeros((4, 4), dtype=bool)
    visible[1, 1:3] = True
    result = visibility_from_masks(expected, visible)
    assert result.expected_pixels == 4
    assert result.visible_pixels == 2
    assert result.visible_fraction == 0.5
    assert result.measurement.visible_fraction == 0.5


def test_fully_visible_target_zone_scores_one() -> None:
    expected = np.ones((3, 3), dtype=np.uint8)
    result = visibility_from_masks(expected, expected)
    assert result.visible_fraction == 1.0


def test_visible_mask_cannot_include_pixels_outside_expected_zone() -> None:
    expected = np.zeros((3, 3), dtype=bool)
    expected[1, 1] = True
    visible = expected.copy()
    visible[0, 0] = True
    with pytest.raises(ValueError, match="subset"):
        visibility_from_masks(expected, visible)


def test_nonbinary_masks_fail_closed() -> None:
    expected = np.ones((3, 3), dtype=np.uint8)
    visible = np.full((3, 3), 2, dtype=np.uint8)
    with pytest.raises(ValueError, match="0/1"):
        visibility_from_masks(expected, visible)


def test_empty_expected_target_zone_fails_closed() -> None:
    expected = np.zeros((3, 3), dtype=bool)
    with pytest.raises(ValueError, match="at least one"):
        visibility_from_masks(expected, expected)
