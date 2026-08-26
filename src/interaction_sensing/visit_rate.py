"""Block-level visit-rate aggregation with explicit observation exposure.

Frames are never treated as independent visits.  Stable event identifiers are
counted once, and primary-stream exposure is separated into interpretable and
censored time.  The default estimand is deliberately narrow:

    visit events per hour of interpretable primary-stream exposure.

It is *not* automatically the ecological visit rate over total deployment time.
Extending to total time requires an explicit sampling/missingness model or a
probability-sample estimator; censored time is never silently relabelled as
zero-visit exposure.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlockObservationExposure:
    block_id: str
    total_seconds: float
    interpretable_seconds: float
    censored_seconds: float

    def __post_init__(self) -> None:
        if not self.block_id.strip():
            raise ValueError("block_id cannot be empty")
        for name, value in (
            ("total_seconds", self.total_seconds),
            ("interpretable_seconds", self.interpretable_seconds),
            ("censored_seconds", self.censored_seconds),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if abs((self.interpretable_seconds + self.censored_seconds) - self.total_seconds) > 1e-6:
            raise ValueError("interpretable + censored exposure must equal total exposure")


@dataclass(frozen=True, slots=True)
class VisitEventDetection:
    event_id: str
    block_id: str

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id cannot be empty")
        if not self.block_id.strip():
            raise ValueError("block_id cannot be empty")


@dataclass(frozen=True, slots=True)
class BlockVisitRate:
    block_id: str
    detected_event_count: int
    total_exposure_hours: float
    interpretable_exposure_hours: float
    censored_fraction: float
    rate_per_interpretable_hour: float | None
    estimand: str = "detected visit-event rate conditional on interpretable primary-stream exposure"


@dataclass(frozen=True, slots=True)
class VisitRateSummary:
    block_rates: tuple[BlockVisitRate, ...]
    unique_detected_events: int
    total_exposure_hours: float
    interpretable_exposure_hours: float
    censored_fraction: float
    pooled_rate_per_interpretable_hour: float | None
    estimand: str = "detected visit-event rate conditional on interpretable primary-stream exposure"


def estimate_block_visit_rates(
    exposures: list[BlockObservationExposure],
    detections: list[VisitEventDetection],
) -> VisitRateSummary:
    """Aggregate stable event IDs without treating censored time as absence."""

    exposure_by_block = {row.block_id: row for row in exposures}
    if len(exposure_by_block) != len(exposures):
        raise ValueError("block exposure IDs must be unique")

    event_to_block: dict[str, str] = {}
    for row in detections:
        previous = event_to_block.get(row.event_id)
        if previous is not None and previous != row.block_id:
            raise ValueError("one event_id cannot belong to multiple blocks")
        event_to_block[row.event_id] = row.block_id
        if row.block_id not in exposure_by_block:
            raise ValueError(f"event refers to unknown block: {row.block_id}")

    events_by_block: dict[str, set[str]] = {block_id: set() for block_id in exposure_by_block}
    for event_id, block_id in event_to_block.items():
        events_by_block[block_id].add(event_id)

    block_rates: list[BlockVisitRate] = []
    for block_id in sorted(exposure_by_block):
        exposure = exposure_by_block[block_id]
        n_events = len(events_by_block[block_id])
        total_hours = exposure.total_seconds / 3600.0
        interpretable_hours = exposure.interpretable_seconds / 3600.0
        censored_fraction = 0.0 if exposure.total_seconds == 0 else exposure.censored_seconds / exposure.total_seconds
        rate = None if interpretable_hours <= 0 else n_events / interpretable_hours
        block_rates.append(
            BlockVisitRate(
                block_id=block_id,
                detected_event_count=n_events,
                total_exposure_hours=total_hours,
                interpretable_exposure_hours=interpretable_hours,
                censored_fraction=censored_fraction,
                rate_per_interpretable_hour=rate,
            )
        )

    total_seconds = sum(row.total_seconds for row in exposures)
    interpretable_seconds = sum(row.interpretable_seconds for row in exposures)
    censored_seconds = sum(row.censored_seconds for row in exposures)
    interpretable_hours = interpretable_seconds / 3600.0

    return VisitRateSummary(
        block_rates=tuple(block_rates),
        unique_detected_events=len(event_to_block),
        total_exposure_hours=total_seconds / 3600.0,
        interpretable_exposure_hours=interpretable_hours,
        censored_fraction=0.0 if total_seconds == 0 else censored_seconds / total_seconds,
        pooled_rate_per_interpretable_hour=None if interpretable_hours <= 0 else len(event_to_block) / interpretable_hours,
    )
