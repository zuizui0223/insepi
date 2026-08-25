from __future__ import annotations

import numpy as np
import pytest

from interaction_sensing import physical_measurement_v13 as v13m


def _rgb(value: int) -> np.ndarray:
    return np.full((1080, 1920, 3), value, dtype=np.uint8)


def test_v13_sample_indices_are_fixed_eight_points_after_stabilisation() -> None:
    assert v13m.SAMPLE_NATIVE_FRAME_INDICES == (75, 105, 135, 165, 195, 225, 255, 285)
    assert all(60 <= index < 300 for index in v13m.SAMPLE_NATIVE_FRAME_INDICES)


def test_v13_canonicalise_requires_exactly_eight_native_frames() -> None:
    output = v13m.canonicalize_sampled_rgb24([_rgb(10 + i) for i in range(8)])
    assert len(output) == 8
    assert all(frame.shape == (96, 128) and frame.dtype == np.uint8 for frame in output)
    with pytest.raises(ValueError):
        v13m.canonicalize_sampled_rgb24([_rgb(10)] * 7)


def test_v13_placebo_background_uses_integer_half_up_even_median() -> None:
    # Sorted central pair is 30 and 31, so half-up median must be 31 rather than
    # NumPy's banker's rounding of 30.5.
    frames = [np.full((96, 128), value, dtype=np.uint8) for value in (1, 2, 3, 30, 31, 40, 50, 60)]
    background = v13m.placebo_background(frames)
    assert np.all(background == 31)
    assert v13m.background_sha256(background) == v13m.background_sha256(background.copy())


def test_v13_placebo_background_rejects_active_or_wrong_shape_contracts() -> None:
    with pytest.raises(ValueError):
        v13m.placebo_background([np.zeros((96, 128), dtype=np.uint8)] * 7)
    wrong = [np.zeros((95, 128), dtype=np.uint8)] * 8
    with pytest.raises(ValueError):
        v13m.placebo_background(wrong)


def test_v13_evidence_mapping_matches_frozen_diagnostic_contract() -> None:
    assert v13m.evidence_score("strong_visitation_candidate") == 1.0
    assert v13m.evidence_score("uncertain_local_activity") == 0.7
    assert v13m.evidence_score("environmental_noise") == 0.0
    assert v13m.evidence_score("no_activity") == 0.0
    with pytest.raises(ValueError):
        v13m.evidence_score("invented")


def test_v13_observability_risk_is_max_of_three_frozen_risks() -> None:
    assert v13m.observability_risk(0.2, 0.8, 0.4) == 0.8
    with pytest.raises(ValueError):
        v13m.observability_risk(-0.1, 0.2, 0.3)
    with pytest.raises(ValueError):
        v13m.observability_risk(float("nan"), 0.2, 0.3)


def _pollipi(states: list[str]):
    return [{"pollipi_state": state} for state in states]


def _insepi(values: list[float]):
    return [
        {"false_event_risk": value, "missed_event_risk": value / 2, "attribution_risk": value / 4}
        for value in values
    ]


def test_v13_phase_summary_uses_medians_not_frame_counts_as_replication() -> None:
    pollipi = _pollipi([
        "no_activity", "no_activity", "uncertain_local_activity", "uncertain_local_activity",
        "strong_visitation_candidate", "strong_visitation_candidate", "strong_visitation_candidate", "strong_visitation_candidate",
    ])
    insepi = _insepi([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    summary = v13m.phase_summary(pollipi, insepi)
    assert summary.sample_count == 8
    assert summary.evidence == pytest.approx(0.85)
    assert summary.observability == pytest.approx(0.45)
    with pytest.raises(ValueError):
        v13m.phase_summary(pollipi[:7], insepi)


def test_v13_all_active_deltas_share_same_placebo_summary() -> None:
    placebo = v13m.PhaseSummary(0.2, 0.7, 8)
    summaries = {
        "placebo": placebo,
        "event_restore": v13m.PhaseSummary(0.8, 0.7, 8),
        "observability_restore": v13m.PhaseSummary(0.2, 0.2, 8),
        "shared_restore": v13m.PhaseSummary(0.7, 0.3, 8),
    }
    response = v13m.build_block_responses(summaries)
    assert response == {
        "event_restore": pytest.approx((0.6, 0.0)),
        "observability_restore": pytest.approx((0.0, -0.5)),
        "shared_restore": pytest.approx((0.5, -0.4)),
    }


def test_v13_block_response_rejects_missing_or_extra_phase() -> None:
    phase = v13m.PhaseSummary(0.0, 0.0, 8)
    with pytest.raises(ValueError):
        v13m.build_block_responses({"placebo": phase})
