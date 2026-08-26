"""Frozen V6 allocation candidate selected from V4 development evidence.

This module is the method-freeze boundary for the allocation policy that may be
carried into a future locked V7 validation.  V4 has already been inspected and
is development evidence only.

High-resolution paired V4 development screening (4,800 windows x 200 replicates,
three prevalence regimes x three budgets) selected the fixed quota vector:

    50% uniform exploration
    10% PolliPi biological-evidence priority
    40% InsePi observability-risk priority
     0% direct disagreement priority

Disagreement remains part of the development/falsification framework, but it is
not a direct allocation arm in the frozen V6 candidate.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from interaction_sensing.simulation.observer_portfolio_v6 import (
    PortfolioWeights,
    select_portfolio_indices,
)


V6_METHOD_NAME = "exploration_guarded_dual_observer_portfolio_v6"
V6_FROZEN_WEIGHTS = PortfolioWeights(
    exploration=0.50,
    pollipi=0.10,
    insepi=0.40,
    disagreement=0.00,
)

# Development provenance. These are not V7 validation identifiers.
V6_DEV_WORLD_FINGERPRINT = "10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193"
V6_DEV_POLLIPI_SOURCE_COMMIT = "5541201b376689c32aaabeafbc8e7e9592150d23"
V6_DEV_WINDOWS = 4800
V6_DEV_REPLICATES = 200
V6_DEV_PREVALENCES = (0.10, 0.50, 0.90)
V6_DEV_BUDGETS = (0.10, 0.25, 0.50)
V6_DEV_RATIO_FLOOR = 1.00
V6_DEV_TV_CEILING = 0.25

# High-resolution paired development result for the frozen candidate.
V6_DEV_WORST_JOINT_RATIO = 1.00846
V6_DEV_MEAN_JOINT_RATIO = 1.11642
V6_DEV_MAX_TV_DISTANCE = 0.21919


def select_frozen_v6_indices(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    *,
    budget_fraction: float,
    seed: int,
) -> tuple[set[int], dict[str, int]]:
    """Apply the frozen V6 quota policy without any fitting or prevalence input."""

    return select_portfolio_indices(
        world,
        budget_fraction=budget_fraction,
        weights=V6_FROZEN_WEIGHTS,
        seed=seed,
    )
