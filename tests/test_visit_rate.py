import pytest

from interaction_sensing.visit_rate import (
    BlockObservationExposure,
    VisitEventDetection,
    estimate_block_visit_rates,
)


def test_stable_event_id_is_counted_once_across_multiple_window_detections() -> None:
    summary = estimate_block_visit_rates(
        [BlockObservationExposure("b1", 3600.0, 3000.0, 600.0)],
        [
            VisitEventDetection("event-1", "b1"),
            VisitEventDetection("event-1", "b1"),
            VisitEventDetection("event-2", "b1"),
        ],
    )
    assert summary.unique_detected_events == 2
    assert summary.block_rates[0].detected_event_count == 2
    assert summary.censored_fraction == pytest.approx(1 / 6)
    assert summary.pooled_rate_per_interpretable_hour == pytest.approx(2 / (3000 / 3600))


def test_censored_time_is_not_silently_added_to_interpretable_denominator() -> None:
    summary = estimate_block_visit_rates(
        [BlockObservationExposure("b1", 3600.0, 1800.0, 1800.0)],
        [VisitEventDetection("event-1", "b1")],
    )
    rate = summary.block_rates[0]
    assert rate.total_exposure_hours == 1.0
    assert rate.interpretable_exposure_hours == 0.5
    assert rate.rate_per_interpretable_hour == 2.0
    assert "conditional on interpretable" in rate.estimand


def test_zero_interpretable_exposure_returns_undefined_rate_not_zero() -> None:
    summary = estimate_block_visit_rates(
        [BlockObservationExposure("b1", 600.0, 0.0, 600.0)],
        [],
    )
    assert summary.block_rates[0].rate_per_interpretable_hour is None
    assert summary.pooled_rate_per_interpretable_hour is None
    assert summary.censored_fraction == 1.0


def test_exposure_must_partition_total_time() -> None:
    with pytest.raises(ValueError, match="must equal total"):
        BlockObservationExposure("b1", 100.0, 50.0, 40.0)


def test_one_event_id_cannot_cross_blocks() -> None:
    with pytest.raises(ValueError, match="multiple blocks"):
        estimate_block_visit_rates(
            [
                BlockObservationExposure("b1", 100.0, 100.0, 0.0),
                BlockObservationExposure("b2", 100.0, 100.0, 0.0),
            ],
            [VisitEventDetection("event-1", "b1"), VisitEventDetection("event-1", "b2")],
        )


def test_unknown_event_block_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown block"):
        estimate_block_visit_rates(
            [BlockObservationExposure("b1", 100.0, 100.0, 0.0)],
            [VisitEventDetection("event-x", "b2")],
        )
