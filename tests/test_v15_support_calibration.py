import pytest

from interaction_sensing.observation_triad import ObservationAvailability
from interaction_sensing.v15_support_calibration import (
    SupportCalibrationBudget,
    SupportCalibrationRow,
    calibrate_support_thresholds,
)


def rows() -> list[SupportCalibrationRow]:
    return [
        SupportCalibrationRow(0.05, ObservationAvailability.UNOBSERVABLE),
        SupportCalibrationRow(0.10, ObservationAvailability.UNOBSERVABLE),
        SupportCalibrationRow(0.20, ObservationAvailability.UNOBSERVABLE),
        SupportCalibrationRow(0.40, ObservationAvailability.COMPROMISED),
        SupportCalibrationRow(0.55, ObservationAvailability.COMPROMISED),
        SupportCalibrationRow(0.75, ObservationAvailability.OBSERVABLE),
        SupportCalibrationRow(0.85, ObservationAvailability.OBSERVABLE),
        SupportCalibrationRow(0.95, ObservationAvailability.OBSERVABLE),
    ]


def test_calibration_uses_explicit_error_budgets_and_preserves_middle_state() -> None:
    result = calibrate_support_thresholds(
        rows(),
        budget=SupportCalibrationBudget(
            max_false_censor_on_observable=0.0,
            max_false_observable_on_unobservable=0.0,
        ),
    )
    assert result.unobservable_threshold == pytest.approx(0.55)
    assert result.observable_threshold == pytest.approx(0.75)
    assert result.achieved_false_censor_on_observable == 0.0
    assert result.achieved_false_observable_on_unobservable == 0.0
    estimator = result.to_estimator()
    assert estimator.unobservable_threshold < estimator.observable_threshold


def test_calibration_requires_both_reference_extremes() -> None:
    with pytest.raises(ValueError, match="unobservable truth"):
        calibrate_support_thresholds(
            [SupportCalibrationRow(0.8, ObservationAvailability.OBSERVABLE)],
            budget=SupportCalibrationBudget(0.05, 0.05),
        )

    with pytest.raises(ValueError, match="observable truth"):
        calibrate_support_thresholds(
            [SupportCalibrationRow(0.1, ObservationAvailability.UNOBSERVABLE)],
            budget=SupportCalibrationBudget(0.05, 0.05),
        )


def test_calibration_fails_when_declared_budget_is_infeasible() -> None:
    reversed_extremes = [
        SupportCalibrationRow(1.0, ObservationAvailability.UNOBSERVABLE),
        SupportCalibrationRow(0.0, ObservationAvailability.OBSERVABLE),
    ]
    with pytest.raises(ValueError, match="false-censor budget"):
        calibrate_support_thresholds(
            reversed_extremes,
            budget=SupportCalibrationBudget(0.0, 0.0),
        )


def test_budget_has_no_implicit_default_and_must_be_valid() -> None:
    with pytest.raises(ValueError, match="\[0, 1\)"):
        SupportCalibrationBudget(1.0, 0.05)
