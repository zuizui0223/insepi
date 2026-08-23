from __future__ import annotations

from collections import Counter
from math import floor
from random import Random

import pytest

from interaction_sensing.guarded_portfolio import select_guarded_indices
from interaction_sensing.simulation import v10_evaluator as v10


REFERENCE_POLICIES: dict[str, tuple[float, tuple[tuple[str, float], ...]]] = {
    "uniform": (1.0, ()),
    "guarded_v6": (0.50, (("evidence", 0.10), ("observability", 0.40))),
    "guarded_e_only": (0.50, (("evidence", 0.50),)),
    "guarded_o_only": (0.50, (("observability", 0.50),)),
    "guarded_fused_20_80": (0.50, (("fused", 0.50),)),
    "guarded_max": (0.50, (("maximum", 0.50),)),
}


def _reference_quota_counts(
    total: int,
    exploration: float,
    arms: tuple[tuple[str, float], ...],
) -> dict[str, int]:
    names = ("exploration", *(name for name, _ in arms))
    weights = (exploration, *(weight for _, weight in arms))
    raw = [total * weight for weight in weights]
    counts = [floor(value) for value in raw]
    remainder = total - sum(counts)
    order = sorted(
        range(len(names)),
        key=lambda index: (raw[index] - counts[index], weights[index], -index),
        reverse=True,
    )
    for index in order[:remainder]:
        counts[index] += 1
    return dict(zip(names, counts, strict=True))


def _reference_select(
    score_rows: list[dict[str, float]],
    *,
    budget_fraction: float,
    policy_name: str,
    seed: int,
) -> set[int]:
    """Independent transcription of the frozen quota algorithm.

    This function intentionally does not import GuardedPortfolio or call the
    production selector. It is an oracle used only to detect implementation drift.
    """
    exploration, arms = REFERENCE_POLICIES[policy_name]
    selected_n = max(1, round(len(score_rows) * budget_fraction))
    quotas = _reference_quota_counts(selected_n, exploration, arms)
    rng = Random(seed)

    uniform_order = list(range(len(score_rows)))
    rng.shuffle(uniform_order)
    selected = set(uniform_order[: quotas["exploration"]])

    rankings: dict[str, list[tuple[float, float, int]]] = {}
    pointers: dict[str, int] = {}
    remaining: dict[str, int] = {}
    for name, _weight in arms:
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
        for name, _weight in arms:
            if remaining[name] <= 0:
                continue
            ranked = rankings[name]
            pointer = pointers[name]
            chosen: int | None = None
            while pointer < len(ranked):
                score, _tie, index = ranked[pointer]
                pointer += 1
                if score <= 0.0:
                    break
                if index not in selected:
                    chosen = index
                    break
            pointers[name] = pointer
            if chosen is None:
                remaining[name] = 0
                continue
            selected.add(chosen)
            remaining[name] -= 1
            progress = True
        if not progress:
            break

    if len(selected) < selected_n:
        for index in uniform_order:
            if index in selected:
                continue
            selected.add(index)
            if len(selected) == selected_n:
                break
    assert len(selected) == selected_n
    return selected


def _score_rows() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    evidence_cycle = (0.0, 0.70, 1.0, 0.0, 1.0, 0.70, 0.0)
    for index in range(364):
        evidence = evidence_cycle[index % len(evidence_cycle)]
        # Deliberately include many ties and exact zeros.
        observability = ((index * 37) % 21) / 20.0
        rows.append(
            {
                "evidence": evidence,
                "observability": observability,
                "fused": 0.20 * evidence + 0.80 * observability,
                "maximum": max(evidence, observability),
            }
        )
    return rows


@pytest.mark.parametrize("policy_name", tuple(REFERENCE_POLICIES))
@pytest.mark.parametrize("budget", (0.10, 0.25, 0.50))
@pytest.mark.parametrize("seed", (0, 1, 137, 2**63 + 19))
def test_v10_production_selector_matches_independent_oracle(
    policy_name: str,
    budget: float,
    seed: int,
) -> None:
    rows = _score_rows()
    expected = _reference_select(
        rows,
        budget_fraction=budget,
        policy_name=policy_name,
        seed=seed,
    )
    actual, _counts = select_guarded_indices(
        rows,
        budget_fraction=budget,
        portfolio=v10._policy(policy_name),
        seed=seed,
    )
    assert actual == expected


def test_v10_targeted_quota_exhaustion_spills_only_to_uniform_oracle() -> None:
    rows = [
        {"evidence": 0.0, "observability": 0.0, "fused": 0.0, "maximum": 0.0}
        for _ in range(364)
    ]
    seed = 20260823
    expected = _reference_select(
        rows,
        budget_fraction=0.25,
        policy_name="guarded_v6",
        seed=seed,
    )
    actual, counts = select_guarded_indices(
        rows,
        budget_fraction=0.25,
        portfolio=v10._policy("guarded_v6"),
        seed=seed,
    )
    assert actual == expected
    assert counts["evidence"] == 0
    assert counts["observability"] == 0
    assert counts["spillover_uniform"] > 0


def _reference_tv(
    selected: set[int],
    rows: list[dict[str, int]],
    keys: tuple[str, ...],
) -> float:
    full_counts = Counter(tuple(row[key] for key in keys) for row in rows)
    selected_counts = Counter(tuple(rows[index][key] for key in keys) for index in selected)
    return 0.5 * sum(
        abs(selected_counts.get(category, 0) / len(selected) - count / len(rows))
        for category, count in full_counts.items()
    )


def test_v10_representation_tv_matches_independent_counting_oracle() -> None:
    rows = [
        {
            "video_index": index % 7,
            "temporal_quartile": (index // 7) % 4,
        }
        for index in range(364)
    ]
    selected = _reference_select(
        _score_rows(),
        budget_fraction=0.25,
        policy_name="guarded_v6",
        seed=991827,
    )
    assert v10._categorical_tv(selected, rows, ("video_index",)) == pytest.approx(
        _reference_tv(selected, rows, ("video_index",)), abs=1e-15
    )
    assert v10._categorical_tv(
        selected, rows, ("video_index", "temporal_quartile")
    ) == pytest.approx(
        _reference_tv(selected, rows, ("video_index", "temporal_quartile")), abs=1e-15
    )


def _reference_claim(
    positive: int,
    monotone: int,
    global_high: float,
    allocation_pass: bool,
) -> str:
    if positive <= 2 or global_high <= 0.0:
        return "D"
    if positive >= 5 and monotone >= 4:
        return "A" if allocation_pass else "B"
    return "C"


def test_v10_claim_precedence_matches_exhaustive_independent_oracle() -> None:
    for positive in range(7):
        for monotone in range(7):
            for global_high in (-0.1, 0.0, 0.1):
                for allocation_pass in (False, True):
                    expected = _reference_claim(
                        positive,
                        monotone,
                        global_high,
                        allocation_pass,
                    )
                    actual, _label = v10._claim(
                        {
                            "positive_high_tier_family_count": positive,
                            "dose_monotone_family_count": monotone,
                            "global_high_tier_median_risk_delta": global_high,
                        },
                        {"v6_allocation_pass": allocation_pass},
                    )
                    assert actual == expected
