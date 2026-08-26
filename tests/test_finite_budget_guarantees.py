from __future__ import annotations

import math

import pytest

from interaction_sensing.finite_budget_guarantees import (
    family_miss_probability,
    max_uniform_target_weight_ratio,
    uniform_inclusion_floor,
)


def test_uniform_inclusion_floor() -> None:
    assert uniform_inclusion_floor(1000, 50) == 0.05
    assert uniform_inclusion_floor(1000, 0) == 0.0


def test_family_miss_probability_matches_hypergeometric_formula() -> None:
    expected = math.comb(90, 20) / math.comb(100, 20)
    assert family_miss_probability(100, 10, 20) == pytest.approx(expected)
    assert family_miss_probability(100, 90, 20) == 0.0
    assert family_miss_probability(100, 0, 20) == 1.0


def test_frozen_half_exploration_bounds_target_weight_by_two() -> None:
    assert max_uniform_target_weight_ratio(100, 50) == 2.0
    assert max_uniform_target_weight_ratio(37, 19) == pytest.approx(37 / 19)


def test_invalid_arguments_are_rejected() -> None:
    with pytest.raises(ValueError):
        uniform_inclusion_floor(0, 0)
    with pytest.raises(ValueError):
        family_miss_probability(10, 11, 1)
    with pytest.raises(ValueError):
        max_uniform_target_weight_ratio(10, 0)
