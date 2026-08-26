"""Simple analytical guarantees for the V6 exploration floor.

Let a finite-budget portfolio reserve an ``alpha`` fraction of selected slots for
uniform exploration and use all remaining slots for any adaptive/targeted rule.
In expectation over the uniform draw, the empirical selected-window distribution
can be written as

    Q = alpha * U + (1 - alpha) * R,

where ``U`` is the full-window uniform distribution and ``R`` is an arbitrary
probability distribution induced by targeted arms (including dependence on the
uniform draw). Therefore

    TV(Q, U) = (1 - alpha) * TV(R, U) <= 1 - alpha.

Any coarsening such as disturbance-family labels also obeys the same or a tighter
bound by the data-processing property of total variation. This is why V6 treats
uniform exploration as a structural guarantee rather than another arm competing
for a scalar score.
"""
from __future__ import annotations

from math import floor

from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights


def expected_tv_upper_bound(exploration_share: float) -> float:
    """Worst-case expected TV distortion under an exploration mixture."""

    if not 0.0 <= exploration_share <= 1.0:
        raise ValueError("exploration_share must lie in [0, 1]")
    return 1.0 - exploration_share


def exploration_quota(selected_slots: int, weights: PortfolioWeights) -> int:
    """Return the minimum number of selected slots assigned to uniform sampling.

    This mirrors the floor-plus-largest-remainder apportionment used by the live
    V6 allocator sufficiently to provide a conservative lower bound: the true
    exploration count can only be higher when targeted-arm quota spills back to
    uniform exploration.
    """

    if selected_slots < 1:
        raise ValueError("selected_slots must be positive")
    raw = selected_slots * weights.exploration
    base = floor(raw)
    # Largest-remainder allocation can add at most one exploration slot. The
    # conservative guarantee is therefore the floor.
    return int(base)


def uniform_inclusion_probability_lower_bound(
    world_size: int,
    budget_fraction: float,
    weights: PortfolioWeights,
) -> float:
    """Lower-bound each window's inclusion probability from exploration alone."""

    if world_size < 1:
        raise ValueError("world_size must be positive")
    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0, 1]")
    selected_slots = max(1, round(world_size * budget_fraction))
    quota = exploration_quota(selected_slots, weights)
    return quota / world_size
