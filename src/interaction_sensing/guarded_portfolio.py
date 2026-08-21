"""Generic reference API for exploration-guarded sensing portfolios.

This module is an uptake/reference interface, not the frozen V7 runtime allocator.
It expresses the V6 architecture without PolliPi/InsePi-specific state names:
reserve an explicit exploration quota, then give independent quotas to arbitrary
positive-valued acquisition signals. Unused targeted quota returns to uniform
exploration.

The frozen V6 evidence is still defined by the implementation pinned in
``benchmarks/v6_method_freeze.json``. Parity tests show that the generic
``evidence`` + ``observability`` adaptation reproduces frozen V6 selections for the
frozen E=.50/P=.10/I=.40/D=0 policy on representative worlds.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import floor
from random import Random
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class GuardedPortfolio:
    exploration: float
    arms: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        if not 0.0 < self.exploration <= 1.0:
            raise ValueError("exploration must lie in (0, 1]")
        names = [name for name, _ in self.arms]
        if len(names) != len(set(names)):
            raise ValueError("arm names must be unique")
        if any(not name for name in names):
            raise ValueError("arm names cannot be empty")
        if any(weight < 0.0 for _, weight in self.arms):
            raise ValueError("arm weights must be non-negative")
        total = self.exploration + sum(weight for _, weight in self.arms)
        if abs(total - 1.0) > 1e-9:
            raise ValueError("exploration + arm weights must sum to one")

    @classmethod
    def frozen_v6_reference(cls) -> "GuardedPortfolio":
        return cls(
            exploration=0.50,
            arms=(("evidence", 0.10), ("observability", 0.40)),
        )


def _quota_counts(total: int, portfolio: GuardedPortfolio) -> dict[str, int]:
    names = ("exploration", *(name for name, _ in portfolio.arms))
    values = (portfolio.exploration, *(weight for _, weight in portfolio.arms))
    raw = [total * value for value in values]
    counts = [floor(value) for value in raw]
    remainder = total - sum(counts)
    order = sorted(
        range(len(names)),
        key=lambda index: (raw[index] - counts[index], values[index], -index),
        reverse=True,
    )
    for index in order[:remainder]:
        counts[index] += 1
    return dict(zip(names, counts, strict=True))


def select_guarded_indices(
    score_rows: Sequence[Mapping[str, float]],
    *,
    budget_fraction: float,
    portfolio: GuardedPortfolio,
    seed: int,
) -> tuple[set[int], dict[str, int]]:
    """Select exact-budget indices using generic acquisition-score columns.

    ``score_rows[index][arm_name]`` must be a deployment-available non-negative
    acquisition score. Zero means the arm has no positive reason to target the
    item. The function never sees latent truth.
    """

    if not score_rows:
        raise ValueError("score_rows cannot be empty")
    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0, 1]")
    for row in score_rows:
        for name, _ in portfolio.arms:
            value = float(row.get(name, 0.0))
            if value < 0.0:
                raise ValueError(f"negative acquisition score for arm {name}")

    selected_n = max(1, round(len(score_rows) * budget_fraction))
    quotas = _quota_counts(selected_n, portfolio)
    rng = Random(seed)
    selected: set[int] = set()
    selected_by_arm = {
        "exploration": 0,
        "spillover_uniform": 0,
        **{name: 0 for name, _ in portfolio.arms},
    }

    uniform_order = list(range(len(score_rows)))
    rng.shuffle(uniform_order)
    for index in uniform_order[: quotas["exploration"]]:
        selected.add(index)
        selected_by_arm["exploration"] += 1

    rankings: dict[str, list[tuple[float, float, int]]] = {}
    pointers: dict[str, int] = {}
    remaining: dict[str, int] = {}
    for name, weight in portfolio.arms:
        ranked = [
            (float(row.get(name, 0.0)), rng.random(), index)
            for index, row in enumerate(score_rows)
        ]
        ranked.sort(reverse=True)
        rankings[name] = ranked
        pointers[name] = 0
        remaining[name] = quotas[name]

    while any(value > 0 for value in remaining.values()):
        progress = False
        for name, _ in portfolio.arms:
            if remaining[name] <= 0:
                continue
            ranked = rankings[name]
            pointer = pointers[name]
            chosen: int | None = None
            while pointer < len(ranked):
                score, _, index = ranked[pointer]
                pointer += 1
                if score <= 0.0:
                    break
                if index not in selected:
                    chosen = index
                    break
            pointers[name] = pointer
            if chosen is None:
                # Targeted quota is not transferred to another targeted signal.
                remaining[name] = 0
                continue
            selected.add(chosen)
            selected_by_arm[name] += 1
            remaining[name] -= 1
            progress = True
        if not progress:
            break

    if len(selected) < selected_n:
        spill = [index for index in uniform_order if index not in selected]
        for index in spill[: selected_n - len(selected)]:
            selected.add(index)
            selected_by_arm["spillover_uniform"] += 1

    if len(selected) != selected_n:
        raise AssertionError("generic guarded portfolio failed to satisfy exact budget")
    return selected, selected_by_arm
