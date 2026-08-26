"""Independent primary-stream observation-support truth for V15.

Observation support is not the complement of nuisance burden. It asks whether the
system-under-test stream contained enough information to support a biological
presence/absence interpretation *if a visit opportunity occurred*.

The five components mirror the V14 operational support dimensions but are truth
annotations or physical measurements, never PolliPi/InsePi outputs. This allows
high nuisance to remain observable and quiet scenes to be unobservable.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observation_triad import ObservationAvailability


class SupportComponentState(str, Enum):
    """Ordinal support state for one necessary observation component."""

    ADEQUATE = "adequate"
    COMPROMISED = "compromised"
    FAILED = "failed"
    UNRESOLVED = "unresolved"


class SupportTruthResolution(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class PrimaryStreamSupportTruth:
    """Component-level truth for whether a visit opportunity was observable.

    Components are positively defined measurement requirements:

    - ``target_zone_coverage``: the focal interaction zone is inside the usable
      field of view for the required opportunity;
    - ``target_zone_visibility``: the relevant zone is not physically hidden;
    - ``spatial_resolution``: the stream resolves the actor/contact scale needed
      by the stated visit definition;
    - ``photometric_sufficiency``: exposure/contrast are sufficient rather than
      saturated, dark, or otherwise photometrically lost;
    - ``temporal_continuity``: enough of the relevant interval is recorded to
      observe entry/contact/exit rather than being lost to dropout or gaps.

    The overall state is derived without nuisance or target-model scores.
    A known failed necessary component is sufficient for UNOBSERVABLE. If none is
    known to have failed but at least one component is unresolved, overall support
    remains unresolved. Otherwise any compromised component yields COMPROMISED;
    only five adequate components yield OBSERVABLE.
    """

    target_zone_coverage: SupportComponentState
    target_zone_visibility: SupportComponentState
    spatial_resolution: SupportComponentState
    photometric_sufficiency: SupportComponentState
    temporal_continuity: SupportComponentState
    annotation_method: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.annotation_method.strip():
            raise ValueError("annotation_method cannot be empty")

    @property
    def components(self) -> tuple[SupportComponentState, ...]:
        return (
            self.target_zone_coverage,
            self.target_zone_visibility,
            self.spatial_resolution,
            self.photometric_sufficiency,
            self.temporal_continuity,
        )

    @property
    def component_map(self) -> dict[str, SupportComponentState]:
        return {
            "target_zone_coverage": self.target_zone_coverage,
            "target_zone_visibility": self.target_zone_visibility,
            "spatial_resolution": self.spatial_resolution,
            "photometric_sufficiency": self.photometric_sufficiency,
            "temporal_continuity": self.temporal_continuity,
        }

    @property
    def resolution(self) -> SupportTruthResolution:
        if SupportComponentState.FAILED in self.components:
            # One independently established failed necessary component already
            # proves that the opportunity is not observable in the primary stream.
            return SupportTruthResolution.RESOLVED
        if SupportComponentState.UNRESOLVED in self.components:
            return SupportTruthResolution.UNRESOLVED
        return SupportTruthResolution.RESOLVED

    @property
    def availability(self) -> ObservationAvailability | None:
        if SupportComponentState.FAILED in self.components:
            return ObservationAvailability.UNOBSERVABLE
        if SupportComponentState.UNRESOLVED in self.components:
            return None
        if SupportComponentState.COMPROMISED in self.components:
            return ObservationAvailability.COMPROMISED
        return ObservationAvailability.OBSERVABLE

    @property
    def limiting_components(self) -> tuple[str, ...]:
        """Return all non-adequate component names without imposing a cause."""

        return tuple(
            name
            for name, value in self.component_map.items()
            if value is not SupportComponentState.ADEQUATE
        )

    @classmethod
    def fully_observable(cls, *, annotation_method: str = "blinded_primary_stream_review") -> "PrimaryStreamSupportTruth":
        return cls(
            SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE,
            SupportComponentState.ADEQUATE,
            annotation_method,
        )
