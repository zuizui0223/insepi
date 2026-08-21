"""V6 observer-portfolio allocation after falsification of fixed disagreement ranking.

V5 falsified the claim that one fixed scalar disagreement ranking is robust to
prevalence shift.  V6 changes the *policy class*: finite audit budget is split
across four independent arms instead of collapsing all evidence into one score.

The four arms are:

- uniform exploration: prevalence-agnostic coverage with a hard positive floor;
- PolliPi evidence: biological-candidate priority;
- InsePi observability: error-risk priority;
- structured disagreement: conflict-specific audit priority.

Latent truth is never read by ``select_portfolio_indices``.  Truth is consulted
only by the development evaluator after selection.  Weight fitting is allowed on
explicit development/calibration worlds, but final locked validation must use a
new, unseen world generation after method freeze.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import floor
from random import Random
from statistics import mean
from typing import Iterable, Mapping, Sequence


POLLIPI_CANDIDATE = {"strong_visitation_candidate", "uncertain_local_activity"}
TARGETED_ARMS = ("pollipi", "insepi", "disagreement")


@dataclass(frozen=True, slots=True)
class PortfolioWeights:
    exploration: float
    pollipi: float
    insepi: float
    disagreement: float

    def __post_init__(self) -> None:
        values = (self.exploration, self.pollipi, self.insepi, self.disagreement)
        if any(value < 0.0 for value in values):
            raise ValueError("portfolio weights must be non-negative")
        if abs(sum(values) - 1.0) > 1e-9:
            raise ValueError("portfolio weights must sum to 1")
        if self.exploration <= 0.0:
            raise ValueError("V6 requires a strictly positive exploration floor")

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PortfolioResult:
    policy: str
    prevalence: float
    budget_fraction: float
    world_windows: int
    selected: int
    exploration_share: float
    pollipi_share: float
    insepi_share: float
    disagreement_share: float
    true_event_recall: float
    hidden_error_recall: float
    false_event_audit_yield: float
    missed_event_audit_yield: float
    attribution_audit_yield: float
    captures_per_hidden_error: float
    disturbance_tv_distance: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MinimaxFit:
    weights: PortfolioWeights
    worst_joint_recall: float
    worst_tv_distance: float
    mean_joint_recall: float
    regimes: int

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["weights"] = self.weights.to_dict()
        return payload


def _row_key(row: Mapping[str, object]) -> str:
    for key in ("condition_id", "scenario_id", "window_id"):
        if key in row:
            return str(row[key])
    raise ValueError("trace row has no stable condition/scenario/window id")


def align_rows(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
) -> list[tuple[Mapping[str, object], Mapping[str, object]]]:
    pollipi = {_row_key(row): row for row in pollipi_rows}
    insepi = {_row_key(row): row for row in insepi_rows}
    if set(pollipi) != set(insepi):
        raise ValueError("observer traces do not contain identical IDs")
    return [(pollipi[key], insepi[key]) for key in sorted(pollipi)]


def _risk(row: Mapping[str, object], key: str) -> float:
    return float(row.get(key, 0.0) or 0.0)


def _candidate_state(row: Mapping[str, object]) -> bool:
    return str(row.get("pollipi_state", "")) in POLLIPI_CANDIDATE


def _strong_candidate(row: Mapping[str, object]) -> bool:
    return str(row.get("pollipi_state", "")) == "strong_visitation_candidate"


def _environmental(row: Mapping[str, object]) -> bool:
    return str(row.get("pollipi_state", "")) == "environmental_noise"


def arm_score(
    arm: str,
    pollipi: Mapping[str, object],
    insepi: Mapping[str, object],
) -> float:
    """Observable priority within one arm.

    This is intentionally *not* a global scalar.  Each arm produces its own
    ranking and receives a separately guaranteed quota.
    """

    candidate = _candidate_state(pollipi)
    false_risk = _risk(insepi, "false_event_risk")
    missed_risk = _risk(insepi, "missed_event_risk")
    attribution_risk = _risk(insepi, "attribution_risk")
    max_risk = max(false_risk, missed_risk, attribution_risk)

    if arm == "pollipi":
        if _strong_candidate(pollipi):
            return 1.0
        if candidate:
            return 0.70
        return 0.0
    if arm == "insepi":
        return max_risk
    if arm == "disagreement":
        # Conflict-specific evidence only.  These branches preserve the V5
        # disagreement semantics but no longer decide the whole allocation.
        if candidate and max_risk >= 0.60:
            return 1.00
        if not candidate and missed_risk >= 0.60:
            return 0.98
        if _environmental(pollipi) and max(false_risk, attribution_risk) >= 0.60:
            return 0.92
        if candidate and 0.25 <= max_risk < 0.60:
            return 0.70
        return 0.0
    raise ValueError(f"unknown portfolio arm: {arm}")


def _quota_counts(total: int, weights: PortfolioWeights) -> dict[str, int]:
    names = ("exploration", "pollipi", "insepi", "disagreement")
    values = (
        weights.exploration,
        weights.pollipi,
        weights.insepi,
        weights.disagreement,
    )
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


def select_portfolio_indices(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    *,
    budget_fraction: float,
    weights: PortfolioWeights,
    seed: int,
) -> tuple[set[int], dict[str, int]]:
    """Select exact-budget windows without consulting latent truth.

    Uniform exploration is drawn first.  The three targeted arms then receive
    independent quotas and are interleaved round-robin so no arm can overwrite
    another through one global ranking.  Empty targeted quotas spill back to
    uniform exploration rather than to another observer.
    """

    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0, 1]")
    if not world:
        raise ValueError("world cannot be empty")

    selected_n = max(1, round(len(world) * budget_fraction))
    quotas = _quota_counts(selected_n, weights)
    rng = Random(seed)
    selected: set[int] = set()
    selected_by_arm = {name: 0 for name in (*TARGETED_ARMS, "exploration", "spillover_uniform")}

    uniform_order = list(range(len(world)))
    rng.shuffle(uniform_order)
    for index in uniform_order[: quotas["exploration"]]:
        selected.add(index)
        selected_by_arm["exploration"] += 1

    rankings: dict[str, list[tuple[float, float, int]]] = {}
    pointers: dict[str, int] = {}
    remaining = {arm: quotas[arm] for arm in TARGETED_ARMS}
    for arm in TARGETED_ARMS:
        ranked = []
        for index, (pollipi, insepi) in enumerate(world):
            score = arm_score(arm, pollipi, insepi)
            ranked.append((score, rng.random(), index))
        ranked.sort(reverse=True)
        rankings[arm] = ranked
        pointers[arm] = 0

    while any(value > 0 for value in remaining.values()):
        progress = False
        for arm in TARGETED_ARMS:
            if remaining[arm] <= 0:
                continue
            ranked = rankings[arm]
            pointer = pointers[arm]
            chosen: int | None = None
            while pointer < len(ranked):
                score, _, index = ranked[pointer]
                pointer += 1
                if score <= 0.0:
                    break
                if index not in selected:
                    chosen = index
                    break
            pointers[arm] = pointer
            if chosen is not None:
                selected.add(chosen)
                selected_by_arm[arm] += 1
                remaining[arm] -= 1
                progress = True
            else:
                # No positive unique candidate remains for this arm.  Its quota
                # becomes unbiased exploration, not extra budget for another arm.
                remaining[arm] = 0
        if not progress:
            break

    if len(selected) < selected_n:
        spill = [index for index in uniform_order if index not in selected]
        for index in spill[: selected_n - len(selected)]:
            selected.add(index)
            selected_by_arm["spillover_uniform"] += 1

    if len(selected) != selected_n:
        raise AssertionError("portfolio allocator failed to satisfy exact budget")
    return selected, selected_by_arm


def _truth_family(pollipi: Mapping[str, object], insepi: Mapping[str, object]) -> str:
    for row in (pollipi, insepi):
        if row.get("disturbance_family") is not None:
            return str(row["disturbance_family"])
    return str(pollipi.get("noise_source", insepi.get("noise_source", "unknown")))


def _latent_error_types(
    pollipi: Mapping[str, object],
    insepi: Mapping[str, object],
) -> set[str]:
    true_visit = bool(pollipi.get("true_visit", insepi.get("true_visit", False)))
    candidate = _candidate_state(pollipi)
    family = _truth_family(pollipi, insepi)
    errors: set[str] = set()
    if true_visit and not candidate:
        errors.add("missed_event")
    if not true_visit and candidate:
        errors.add("false_event")
    if candidate and "clutter" in family:
        errors.add("attribution")
    return errors


def _tv_distance(full: Sequence[str], selected: Sequence[str]) -> float:
    if not full or not selected:
        return 0.0
    labels = sorted(set(full) | set(selected))
    return 0.5 * sum(
        abs(full.count(label) / len(full) - selected.count(label) / len(selected))
        for label in labels
    )


def sample_world(
    aligned: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    *,
    prevalence: float,
    world_windows: int,
    seed: int,
) -> list[tuple[Mapping[str, object], Mapping[str, object]]]:
    """Construct a development world at an explicit event prevalence."""

    if not 0.0 < prevalence < 1.0:
        raise ValueError("prevalence must lie in (0, 1)")
    positives = [pair for pair in aligned if bool(pair[0].get("true_visit", False))]
    negatives = [pair for pair in aligned if not bool(pair[0].get("true_visit", False))]
    if not positives or not negatives:
        raise ValueError("both positive and negative condition rows are required")
    rng = Random(seed)
    positive_n = round(world_windows * prevalence)
    negative_n = world_windows - positive_n
    world = [positives[rng.randrange(len(positives))] for _ in range(positive_n)]
    world.extend(negatives[rng.randrange(len(negatives))] for _ in range(negative_n))
    rng.shuffle(world)
    return world


def _score_selection(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    selected: set[int],
    *,
    prevalence: float,
    budget_fraction: float,
    weights: PortfolioWeights,
) -> PortfolioResult:
    true_events = {index for index, (p, _) in enumerate(world) if bool(p.get("true_visit", False))}
    hidden_errors = {
        index: _latent_error_types(p, i)
        for index, (p, i) in enumerate(world)
        if _latent_error_types(p, i)
    }
    selected_errors = {index: hidden_errors[index] for index in selected if index in hidden_errors}

    def recall(indices: set[int]) -> float:
        return len(indices & selected) / len(indices) if indices else 1.0

    def audit_yield(kind: str) -> float:
        return sum(kind in kinds for kinds in selected_errors.values()) / len(selected)

    full_families = [_truth_family(p, i) for p, i in world]
    selected_families = [_truth_family(*world[index]) for index in selected]
    recovered_errors = len(selected_errors)
    return PortfolioResult(
        policy="observer_portfolio_v6",
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        world_windows=len(world),
        selected=len(selected),
        exploration_share=weights.exploration,
        pollipi_share=weights.pollipi,
        insepi_share=weights.insepi,
        disagreement_share=weights.disagreement,
        true_event_recall=recall(true_events),
        hidden_error_recall=recall(set(hidden_errors)),
        false_event_audit_yield=audit_yield("false_event"),
        missed_event_audit_yield=audit_yield("missed_event"),
        attribution_audit_yield=audit_yield("attribution"),
        captures_per_hidden_error=(len(selected) / recovered_errors if recovered_errors else float("inf")),
        disturbance_tv_distance=_tv_distance(full_families, selected_families),
    )


def evaluate_portfolio_once(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    weights: PortfolioWeights,
    prevalence: float,
    budget_fraction: float,
    world_windows: int,
    seed: int,
) -> PortfolioResult:
    aligned = align_rows(pollipi_rows, insepi_rows)
    world = sample_world(aligned, prevalence=prevalence, world_windows=world_windows, seed=seed)
    selected, _ = select_portfolio_indices(
        world,
        budget_fraction=budget_fraction,
        weights=weights,
        seed=seed + 7919,
    )
    return _score_selection(
        world,
        selected,
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        weights=weights,
    )


def run_portfolio_replicates(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    weights: PortfolioWeights,
    prevalence: float,
    budget_fraction: float,
    world_windows: int = 2400,
    replicates: int = 100,
    seed: int = 20260821,
) -> PortfolioResult:
    pollipi = list(pollipi_rows)
    insepi = list(insepi_rows)
    rows = [
        evaluate_portfolio_once(
            pollipi,
            insepi,
            weights=weights,
            prevalence=prevalence,
            budget_fraction=budget_fraction,
            world_windows=world_windows,
            seed=seed + replicate * 1009,
        )
        for replicate in range(replicates)
    ]
    first = rows[0]
    return PortfolioResult(
        policy=first.policy,
        prevalence=prevalence,
        budget_fraction=budget_fraction,
        world_windows=world_windows,
        selected=first.selected,
        exploration_share=weights.exploration,
        pollipi_share=weights.pollipi,
        insepi_share=weights.insepi,
        disagreement_share=weights.disagreement,
        true_event_recall=mean(row.true_event_recall for row in rows),
        hidden_error_recall=mean(row.hidden_error_recall for row in rows),
        false_event_audit_yield=mean(row.false_event_audit_yield for row in rows),
        missed_event_audit_yield=mean(row.missed_event_audit_yield for row in rows),
        attribution_audit_yield=mean(row.attribution_audit_yield for row in rows),
        captures_per_hidden_error=mean(row.captures_per_hidden_error for row in rows),
        disturbance_tv_distance=mean(row.disturbance_tv_distance for row in rows),
    )


def generate_weight_grid(
    *,
    step: float = 0.10,
    min_exploration: float = 0.30,
    min_targeted: float = 0.10,
    max_targeted: float = 0.50,
) -> list[PortfolioWeights]:
    """Generate a constrained simplex grid for development-only minimax fitting."""

    units = round(1.0 / step)
    if abs(units * step - 1.0) > 1e-9:
        raise ValueError("step must divide 1 exactly")
    min_e = round(min_exploration / step)
    min_t = round(min_targeted / step)
    max_t = round(max_targeted / step)
    grid: list[PortfolioWeights] = []
    for e in range(min_e, units + 1):
        for p in range(min_t, max_t + 1):
            for i in range(min_t, max_t + 1):
                d = units - e - p - i
                if min_t <= d <= max_t:
                    grid.append(PortfolioWeights(e * step, p * step, i * step, d * step))
    return grid


def fit_minimax_portfolio(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    prevalences: Sequence[float] = (0.10, 0.50, 0.90),
    budgets: Sequence[float] = (0.10, 0.25, 0.50),
    world_windows: int = 600,
    replicates: int = 8,
    seed: int = 20260821,
    grid: Sequence[PortfolioWeights] | None = None,
) -> MinimaxFit:
    """Fit portfolio shares on development/calibration rows only.

    Objective is lexicographic rather than a hand-tuned weighted sum:
    1) maximise the worst regime's minimum(event recall, hidden-error recall),
    2) minimise worst disturbance TV distance,
    3) maximise mean joint recall.
    """

    pollipi = [row for row in pollipi_rows if str(row.get("split", "calibration")) == "calibration"]
    insepi = [row for row in insepi_rows if str(row.get("split", "calibration")) == "calibration"]
    candidates = list(grid) if grid is not None else generate_weight_grid()
    if not candidates:
        raise ValueError("portfolio weight grid is empty")

    best: MinimaxFit | None = None
    best_key: tuple[float, float, float] | None = None
    for candidate_index, weights in enumerate(candidates):
        regime_results: list[PortfolioResult] = []
        for prevalence in prevalences:
            for budget in budgets:
                regime_results.append(
                    run_portfolio_replicates(
                        pollipi,
                        insepi,
                        weights=weights,
                        prevalence=prevalence,
                        budget_fraction=budget,
                        world_windows=world_windows,
                        replicates=replicates,
                        seed=seed + candidate_index * 100_003,
                    )
                )
        worst_joint = min(min(row.true_event_recall, row.hidden_error_recall) for row in regime_results)
        worst_tv = max(row.disturbance_tv_distance for row in regime_results)
        mean_joint = mean(0.5 * (row.true_event_recall + row.hidden_error_recall) for row in regime_results)
        key = (worst_joint, -worst_tv, mean_joint)
        if best_key is None or key > best_key:
            best_key = key
            best = MinimaxFit(
                weights=weights,
                worst_joint_recall=worst_joint,
                worst_tv_distance=worst_tv,
                mean_joint_recall=mean_joint,
                regimes=len(regime_results),
            )
    assert best is not None
    return best
