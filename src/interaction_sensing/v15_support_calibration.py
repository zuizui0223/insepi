"""Development-only calibration of V15-v2 observation-support thresholds.

The historical 0.30/0.70 O thresholds are development defaults. This module
provides a predeclared replacement rule that uses only resolved *development*
support truth and two explicit error budgets. It never consumes biological target
truth or nuisance truth.

The rule is asymmetric and fail-closed:

- choose the largest unobservable threshold whose false-censor rate on truly
  observable development windows does not exceed its declared budget;
- then choose the smallest observable threshold *strictly above that boundary*
  whose false-observable rate on truly unobservable development windows does not
  exceed its declared budget;
- if no such ordered pair exists, calibration fails rather than collapsing the
  compromised middle state.

No default budgets are provided. They must be frozen before held-out scoring.
"""
from __future__ import annotations

from dataclasses import dataclass

from .observation_triad import ObservationAvailability
from .support_estimation import PrimaryStreamSupportEstimator


@dataclass(frozen=True, slots=True)
class SupportCalibrationRow:
    support_ceiling: float
    truth_availability: ObservationAvailability

    def __post_init__(self) -> None:
        if not 0.0 <= self.support_ceiling <= 1.0:
            raise ValueError("support_ceiling must lie in [0, 1]")
        if not isinstance(self.truth_availability, ObservationAvailability):
            raise TypeError("truth_availability must be ObservationAvailability")


@dataclass(frozen=True, slots=True)
class SupportCalibrationBudget:
    max_false_censor_on_observable: float
    max_false_observable_on_unobservable: float

    def __post_init__(self) -> None:
        for name, value in (
            ("max_false_censor_on_observable", self.max_false_censor_on_observable),
            ("max_false_observable_on_unobservable", self.max_false_observable_on_unobservable),
        ):
            if not 0.0 <= value < 1.0:
                raise ValueError(f"{name} must lie in [0, 1)")


@dataclass(frozen=True, slots=True)
class SupportCalibrationResult:
    unobservable_threshold: float
    observable_threshold: float
    achieved_false_censor_on_observable: float
    achieved_false_observable_on_unobservable: float
    n_observable_truth: int
    n_unobservable_truth: int
    n_compromised_truth: int

    def to_estimator(self) -> PrimaryStreamSupportEstimator:
        return PrimaryStreamSupportEstimator(
            observable_threshold=self.observable_threshold,
            unobservable_threshold=self.unobservable_threshold,
        )


def _rate(flags: list[bool]) -> float:
    if not flags:
        raise ValueError("calibration requires non-empty reference class")
    return sum(flags) / len(flags)


def calibrate_support_thresholds(
    rows: list[SupportCalibrationRow],
    *,
    budget: SupportCalibrationBudget,
) -> SupportCalibrationResult:
    """Calibrate O thresholds from resolved development support truth only."""

    if not rows:
        raise ValueError("support calibration rows cannot be empty")

    observable_scores = [
        row.support_ceiling
        for row in rows
        if row.truth_availability is ObservationAvailability.OBSERVABLE
    ]
    unobservable_scores = [
        row.support_ceiling
        for row in rows
        if row.truth_availability is ObservationAvailability.UNOBSERVABLE
    ]
    compromised_count = sum(
        row.truth_availability is ObservationAvailability.COMPROMISED for row in rows
    )
    if not observable_scores:
        raise ValueError("support calibration requires observable truth rows")
    if not unobservable_scores:
        raise ValueError("support calibration requires unobservable truth rows")

    candidates = sorted({0.0, 1.0, *(row.support_ceiling for row in rows)})

    feasible_unobservable: list[tuple[float, float]] = []
    for threshold in candidates:
        false_censor = _rate([score <= threshold for score in observable_scores])
        if false_censor <= budget.max_false_censor_on_observable + 1e-15:
            feasible_unobservable.append((threshold, false_censor))
    if not feasible_unobservable:
        raise ValueError("no unobservable threshold satisfies the false-censor budget")
    unobservable_threshold, false_censor = max(feasible_unobservable, key=lambda item: item[0])

    feasible_observable: list[tuple[float, float]] = []
    for threshold in candidates:
        if threshold <= unobservable_threshold:
            continue
        false_observable = _rate([score >= threshold for score in unobservable_scores])
        if false_observable <= budget.max_false_observable_on_unobservable + 1e-15:
            feasible_observable.append((threshold, false_observable))
    if not feasible_observable:
        raise ValueError(
            "no observable threshold above the calibrated unobservable boundary "
            "satisfies the false-observable budget"
        )
    observable_threshold, false_observable = min(feasible_observable, key=lambda item: item[0])

    return SupportCalibrationResult(
        unobservable_threshold=unobservable_threshold,
        observable_threshold=observable_threshold,
        achieved_false_censor_on_observable=false_censor,
        achieved_false_observable_on_unobservable=false_observable,
        n_observable_truth=len(observable_scores),
        n_unobservable_truth=len(unobservable_scores),
        n_compromised_truth=compromised_count,
    )
