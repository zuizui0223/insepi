"""V14b target-side observer with nuisance observer frozen.

This generation makes the smallest correction supported by the observation-safe
plateau audit: preserve directly observed actor evidence as an independent
positive route, while retaining local target/scene response as unattributed
unless an independent target-link channel exists.

The frozen V14a2 direct channel has an exact zero under no actor. Therefore the
`> 0` direct-support rule is a closed-world structural rule, not a proposed field
threshold or calibrated probability.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .simulation.dimensionless_observability_v14a2 import SpatiotemporalSignature


class TargetRouteState(str, Enum):
    NONE = "none"
    DIRECT_SUPPORTED = "direct_supported"
    INDIRECT_UNATTRIBUTED = "indirect_unattributed"
    DIRECT_WITH_LOCAL_RESPONSE = "direct_with_local_response"


@dataclass(frozen=True, slots=True)
class TargetObservationV14b:
    direct_signal_fraction: float
    local_response_fraction: float
    route_state: TargetRouteState
    target_supported: bool
    unresolved_indirect_only: bool

    def __post_init__(self) -> None:
        if not 0.0 <= self.direct_signal_fraction <= 1.0:
            raise ValueError("direct_signal_fraction must lie in [0,1]")
        if not 0.0 <= self.local_response_fraction <= 1.0:
            raise ValueError("local_response_fraction must lie in [0,1]")
        if self.unresolved_indirect_only and self.target_supported:
            raise ValueError("indirect-only unresolved evidence cannot be target-supported")


def observe_target_v14b(signature: SpatiotemporalSignature) -> TargetObservationV14b:
    """Read target-side evidence only; never consume nuisance observer output.

    Direct actor signal is the only positive target attribution channel in this
    generation. Local response is retained for audit/context but cannot assert
    target presence without a separate actor-to-response link signal.
    """

    direct = float(signature.direct_target_signal_fraction)
    local = float(signature.local_excess_motion_fraction)
    direct_supported = direct > 0.0
    local_present = local > 0.0

    if direct_supported and local_present:
        state = TargetRouteState.DIRECT_WITH_LOCAL_RESPONSE
    elif direct_supported:
        state = TargetRouteState.DIRECT_SUPPORTED
    elif local_present:
        state = TargetRouteState.INDIRECT_UNATTRIBUTED
    else:
        state = TargetRouteState.NONE

    return TargetObservationV14b(
        direct_signal_fraction=direct,
        local_response_fraction=local,
        route_state=state,
        target_supported=direct_supported,
        unresolved_indirect_only=(not direct_supported and local_present),
    )
