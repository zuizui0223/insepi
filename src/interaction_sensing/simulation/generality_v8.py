"""V8 observer-general applicability benchmark.

V8 is deliberately separate from locked V7. It does not render V7 pixels, use
V7 seeds, change frozen V6 weights, or fit a new allocator. It asks where the
already-frozen guarded architecture helps, where a simpler same-exploration
policy suffices, and how retaining an explicit uniform subset affects downstream
prevalence estimation.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import exp, floor, sqrt
from random import Random
from typing import Callable, Mapping, Sequence

from interaction_sensing.guarded_portfolio import GuardedPortfolio


POLICIES = (
    "uniform",
    "guarded_v6",
    "guarded_e_only",
    "guarded_o_only",
    "guarded_fused_20_80",
    "guarded_max",
)


@dataclass(frozen=True, slots=True)
class Regime:
    event_prevalence: float
    budget_fraction: float
    evidence_quality: float
    observability_quality: float
    residual_correlation: float
    disturbance_prevalence: float

    @property
    def key(self) -> tuple[float, float, float, float, float, float]:
        return (
            self.event_prevalence,
            self.budget_fraction,
            self.evidence_quality,
            self.observability_quality,
            self.residual_correlation,
            self.disturbance_prevalence,
        )


@dataclass(frozen=True, slots=True)
class Window:
    true_event: bool
    disturbed: bool
    hard_scene: bool
    evidence: float
    observability: float
    evidence_hidden_error: bool

    @property
    def family(self) -> str:
        return f"d{int(self.disturbed)}_h{int(self.hard_scene)}"


@dataclass(frozen=True, slots=True)
class Selection:
    selected: frozenset[int]
    exploration: frozenset[int]
    selected_by_arm: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class ReplicateMetrics:
    event_recall: float
    hidden_error_recall: float
    disturbance_tv: float
    naive_prevalence_error: float
    exploration_prevalence_error: float


def _sigmoid(value: float) -> float:
    if value >= 35.0:
        return 1.0
    if value <= -35.0:
        return 0.0
    return 1.0 / (1.0 + exp(-value))


def _quality_strength(quality: float) -> float:
    if not 0.5 <= quality <= 1.0:
        raise ValueError("observer quality must lie in [0.5, 1.0]")
    # Quality is a monotone simulation control, not a claimed AUC/calibration.
    return 0.8 + 4.0 * (quality - 0.5)


def generate_world(*, n: int, regime: Regime, seed: int) -> tuple[Window, ...]:
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 <= regime.residual_correlation <= 0.999999:
        raise ValueError("residual_correlation must lie in [0, 1)")
    rng = Random(seed)
    e_strength = _quality_strength(regime.evidence_quality)
    o_strength = _quality_strength(regime.observability_quality)
    rho = regime.residual_correlation
    independent_scale = sqrt(max(0.0, 1.0 - rho * rho))
    rows: list[Window] = []

    for _ in range(n):
        true_event = rng.random() < regime.event_prevalence
        disturbed = rng.random() < regime.disturbance_prevalence
        hard_scene = rng.gauss(0.0, 1.0) > 0.65

        # Risk is a scene property, not the evidence observer's error label.
        risk = min(1.0, 0.70 * float(disturbed) + 0.55 * float(hard_scene))
        visibility = 1.0 - 0.75 * risk

        common = rng.gauss(0.0, 1.0)
        e_noise = rho * common + independent_scale * rng.gauss(0.0, 1.0)
        o_noise = rho * common + independent_scale * rng.gauss(0.0, 1.0)

        event_sign = 1.0 if true_event else -1.0
        evidence_margin = event_sign * e_strength * visibility + e_noise
        evidence = _sigmoid(evidence_margin)

        # Observer-O estimates scene risk. The centring makes clean/easy scenes
        # low-risk and either disturbance or scene difficulty high-risk.
        observability_margin = o_strength * 3.0 * (risk - 0.35) + o_noise
        observability = _sigmoid(observability_margin)

        evidence_hidden_error = (evidence >= 0.5) != true_event
        rows.append(
            Window(
                true_event=true_event,
                disturbed=disturbed,
                hard_scene=hard_scene,
                evidence=evidence,
                observability=observability,
                evidence_hidden_error=evidence_hidden_error,
            )
        )
    return tuple(rows)


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


def _policy_spec(
    policy: str,
) -> tuple[GuardedPortfolio, Mapping[str, Callable[[Window], float]]]:
    if policy == "uniform":
        return GuardedPortfolio(exploration=1.0, arms=()), {}
    if policy == "guarded_v6":
        return GuardedPortfolio.frozen_v6_reference(), {
            "evidence": lambda row: row.evidence,
            "observability": lambda row: row.observability,
        }
    if policy == "guarded_e_only":
        return GuardedPortfolio(exploration=0.50, arms=(("evidence", 0.50),)), {
            "evidence": lambda row: row.evidence,
        }
    if policy == "guarded_o_only":
        return GuardedPortfolio(exploration=0.50, arms=(("observability", 0.50),)), {
            "observability": lambda row: row.observability,
        }
    if policy == "guarded_fused_20_80":
        return GuardedPortfolio(exploration=0.50, arms=(("fused", 0.50),)), {
            "fused": lambda row: 0.20 * row.evidence + 0.80 * row.observability,
        }
    if policy == "guarded_max":
        return GuardedPortfolio(exploration=0.50, arms=(("maximum", 0.50),)), {
            "maximum": lambda row: max(row.evidence, row.observability),
        }
    raise ValueError(f"unknown V8 policy: {policy}")


def select_with_provenance(
    world: Sequence[Window],
    *,
    budget_fraction: float,
    policy: str,
    seed: int,
) -> Selection:
    """Exact-budget selector retaining the uniform-subset membership.

    The guarded_v6 branch mirrors ``select_guarded_indices`` tie-breaking and
    spillover so parity can be tested against the generic public API.
    """
    if not world:
        raise ValueError("world cannot be empty")
    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0,1]")

    portfolio, score_functions = _policy_spec(policy)
    selected_n = max(1, round(len(world) * budget_fraction))
    quotas = _quota_counts(selected_n, portfolio)
    rng = Random(seed)
    selected: set[int] = set()
    exploration: set[int] = set()
    selected_by_arm = {
        "exploration": 0,
        "spillover_uniform": 0,
        **{name: 0 for name, _ in portfolio.arms},
    }

    uniform_order = list(range(len(world)))
    rng.shuffle(uniform_order)
    for index in uniform_order[: quotas["exploration"]]:
        selected.add(index)
        exploration.add(index)
        selected_by_arm["exploration"] += 1

    rankings: dict[str, list[tuple[float, float, int]]] = {}
    pointers: dict[str, int] = {}
    remaining: dict[str, int] = {}
    for name, _weight in portfolio.arms:
        scorer = score_functions[name]
        ranked = [(float(scorer(row)), rng.random(), index) for index, row in enumerate(world)]
        ranked.sort(reverse=True)
        rankings[name] = ranked
        pointers[name] = 0
        remaining[name] = quotas[name]

    while any(value > 0 for value in remaining.values()):
        progress = False
        for name, _weight in portfolio.arms:
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
            selected_by_arm[name] += 1
            remaining[name] -= 1
            progress = True
        if not progress:
            break

    if len(selected) < selected_n:
        spill = [index for index in uniform_order if index not in selected]
        for index in spill[: selected_n - len(selected)]:
            selected.add(index)
            exploration.add(index)
            selected_by_arm["spillover_uniform"] += 1

    if len(selected) != selected_n:
        raise AssertionError("V8 selector failed exact budget")
    return Selection(
        selected=frozenset(selected),
        exploration=frozenset(exploration),
        selected_by_arm=selected_by_arm,
    )


def _recall(indices: frozenset[int], positives: Sequence[bool]) -> float:
    denominator = sum(bool(value) for value in positives)
    if denominator == 0:
        return 1.0
    return sum(bool(positives[index]) for index in indices) / denominator


def _family_tv(world: Sequence[Window], selected: frozenset[int]) -> float:
    world_counts: dict[str, int] = defaultdict(int)
    selected_counts: dict[str, int] = defaultdict(int)
    for row in world:
        world_counts[row.family] += 1
    for index in selected:
        selected_counts[world[index].family] += 1
    # Fixed ordering prevents Python hash randomization from changing the final
    # floating-point addition order and therefore the byte-level result hash.
    families = sorted(set(world_counts) | set(selected_counts))
    return 0.5 * sum(
        abs(selected_counts[family] / len(selected) - world_counts[family] / len(world))
        for family in families
    )


def _mean_event(world: Sequence[Window], indices: frozenset[int]) -> float:
    if not indices:
        raise ValueError("cannot estimate prevalence from an empty sample")
    return sum(float(world[index].true_event) for index in indices) / len(indices)


def evaluate_selection(world: Sequence[Window], selection: Selection) -> ReplicateMetrics:
    true_events = tuple(row.true_event for row in world)
    hidden_errors = tuple(row.evidence_hidden_error for row in world)
    world_prevalence = sum(float(row.true_event) for row in world) / len(world)
    return ReplicateMetrics(
        event_recall=_recall(selection.selected, true_events),
        hidden_error_recall=_recall(selection.selected, hidden_errors),
        disturbance_tv=_family_tv(world, selection.selected),
        naive_prevalence_error=_mean_event(world, selection.selected) - world_prevalence,
        exploration_prevalence_error=_mean_event(world, selection.exploration) - world_prevalence,
    )


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


def _rmse(values: Sequence[float]) -> float:
    return sqrt(sum(value * value for value in values) / len(values))


def summarize_replicates(metrics: Sequence[ReplicateMetrics]) -> dict[str, float]:
    if not metrics:
        raise ValueError("metrics cannot be empty")
    naive_errors = [row.naive_prevalence_error for row in metrics]
    exploration_errors = [row.exploration_prevalence_error for row in metrics]
    return {
        "true_event_recall": _mean([row.event_recall for row in metrics]),
        "evidence_hidden_error_recall": _mean([row.hidden_error_recall for row in metrics]),
        "disturbance_family_tv": _mean([row.disturbance_tv for row in metrics]),
        "naive_selected_prevalence_bias": _mean(naive_errors),
        "naive_selected_prevalence_rmse": _rmse(naive_errors),
        "exploration_only_prevalence_bias": _mean(exploration_errors),
        "exploration_only_prevalence_rmse": _rmse(exploration_errors),
    }


def protocol_regimes(protocol: Mapping[str, object]) -> tuple[Regime, ...]:
    world = protocol["world"]
    if not isinstance(world, Mapping):
        raise ValueError("protocol world must be a mapping")
    regimes: list[Regime] = []
    for prevalence in world["event_prevalence"]:
        for budget in world["budget_fraction"]:
            for evidence_quality in world["evidence_quality"]:
                for observability_quality in world["observability_quality"]:
                    for correlation in world["residual_correlation"]:
                        for disturbance in world["disturbance_prevalence"]:
                            regimes.append(
                                Regime(
                                    event_prevalence=float(prevalence),
                                    budget_fraction=float(budget),
                                    evidence_quality=float(evidence_quality),
                                    observability_quality=float(observability_quality),
                                    residual_correlation=float(correlation),
                                    disturbance_prevalence=float(disturbance),
                                )
                            )
    return tuple(regimes)


def run_protocol(protocol: Mapping[str, object]) -> dict[str, object]:
    world_spec = protocol["world"]
    if not isinstance(world_spec, Mapping):
        raise ValueError("protocol world must be a mapping")
    n = int(world_spec["windows_per_regime"])
    replicates = int(world_spec["paired_replicates"])
    base_seed = int(protocol["seed"])
    policies = tuple(str(item) for item in protocol["policies"])
    if policies != POLICIES:
        raise ValueError("V8 policy registry differs from preregistered order")

    regime_rows: list[dict[str, object]] = []
    applicability_rows: list[dict[str, object]] = []
    slices: dict[tuple[float, float, float], dict[str, int]] = defaultdict(
        lambda: {"regimes": 0, "v6_ge_uniform": 0, "v6_best_same_alpha": 0}
    )

    for regime_index, regime in enumerate(protocol_regimes(protocol)):
        per_policy: dict[str, list[ReplicateMetrics]] = {policy: [] for policy in policies}
        for replicate in range(replicates):
            world_seed = base_seed + regime_index * 100_003 + replicate * 101
            selection_seed = base_seed + regime_index * 1_000_003 + replicate * 1_009
            world = generate_world(n=n, regime=regime, seed=world_seed)
            for policy in policies:
                selection = select_with_provenance(
                    world,
                    budget_fraction=regime.budget_fraction,
                    policy=policy,
                    seed=selection_seed,
                )
                per_policy[policy].append(evaluate_selection(world, selection))

        summaries = {policy: summarize_replicates(rows) for policy, rows in per_policy.items()}
        uniform = summaries["uniform"]
        joint_by_policy: dict[str, float] = {}
        for policy in policies:
            summary = summaries[policy]
            event_ratio = summary["true_event_recall"] / uniform["true_event_recall"]
            error_ratio = summary["evidence_hidden_error_recall"] / uniform[
                "evidence_hidden_error_recall"
            ]
            joint = min(event_ratio, error_ratio)
            joint_by_policy[policy] = joint
            regime_rows.append(
                {
                    "event_prevalence": regime.event_prevalence,
                    "budget_fraction": regime.budget_fraction,
                    "evidence_quality": regime.evidence_quality,
                    "observability_quality": regime.observability_quality,
                    "residual_correlation": regime.residual_correlation,
                    "disturbance_prevalence": regime.disturbance_prevalence,
                    "policy": policy,
                    **summary,
                    "event_recall_ratio_to_uniform": event_ratio,
                    "hidden_error_recall_ratio_to_uniform": error_ratio,
                    "joint_recovery_ratio_to_uniform": joint,
                }
            )

        same_alpha = (
            "guarded_e_only",
            "guarded_o_only",
            "guarded_fused_20_80",
            "guarded_max",
        )
        best_same_alpha = max(same_alpha, key=lambda name: (joint_by_policy[name], name))
        v6_joint = joint_by_policy["guarded_v6"]
        best_joint = joint_by_policy[best_same_alpha]
        applicability_rows.append(
            {
                "event_prevalence": regime.event_prevalence,
                "budget_fraction": regime.budget_fraction,
                "evidence_quality": regime.evidence_quality,
                "observability_quality": regime.observability_quality,
                "residual_correlation": regime.residual_correlation,
                "disturbance_prevalence": regime.disturbance_prevalence,
                "v6_joint_recovery_ratio_to_uniform": v6_joint,
                "v6_ge_uniform": v6_joint >= 1.0,
                "best_same_alpha_policy": best_same_alpha,
                "best_same_alpha_joint_ratio": best_joint,
                "v6_minus_best_same_alpha_joint": v6_joint - best_joint,
                "v6_best_same_alpha": v6_joint >= best_joint - 1e-12,
                "v6_tv": summaries["guarded_v6"]["disturbance_family_tv"],
                "v6_naive_prevalence_rmse": summaries["guarded_v6"][
                    "naive_selected_prevalence_rmse"
                ],
                "v6_exploration_prevalence_rmse": summaries["guarded_v6"][
                    "exploration_only_prevalence_rmse"
                ],
            }
        )
        slice_key = (
            regime.evidence_quality,
            regime.observability_quality,
            regime.residual_correlation,
        )
        slices[slice_key]["regimes"] += 1
        slices[slice_key]["v6_ge_uniform"] += int(v6_joint >= 1.0)
        slices[slice_key]["v6_best_same_alpha"] += int(v6_joint >= best_joint - 1e-12)

    slice_rows = [
        {
            "evidence_quality": key[0],
            "observability_quality": key[1],
            "residual_correlation": key[2],
            **counts,
            "fraction_v6_ge_uniform": counts["v6_ge_uniform"] / counts["regimes"],
            "fraction_v6_best_same_alpha": counts["v6_best_same_alpha"] / counts["regimes"],
        }
        for key, counts in sorted(slices.items())
    ]
    total = len(applicability_rows)
    headline = {
        "regime_count": total,
        "v6_ge_uniform_count": sum(int(row["v6_ge_uniform"]) for row in applicability_rows),
        "v6_best_same_alpha_count": sum(
            int(row["v6_best_same_alpha"]) for row in applicability_rows
        ),
        "mean_v6_joint_ratio": _mean(
            [float(row["v6_joint_recovery_ratio_to_uniform"]) for row in applicability_rows]
        ),
        "mean_v6_minus_best_same_alpha_joint": _mean(
            [float(row["v6_minus_best_same_alpha_joint"]) for row in applicability_rows]
        ),
        "mean_v6_naive_prevalence_rmse": _mean(
            [float(row["v6_naive_prevalence_rmse"]) for row in applicability_rows]
        ),
        "mean_v6_exploration_prevalence_rmse": _mean(
            [float(row["v6_exploration_prevalence_rmse"]) for row in applicability_rows]
        ),
    }
    return {
        "schema": "interaction-sensing-v8-generality-result-v1",
        "protocol_schema": protocol["schema"],
        "headline": headline,
        "regime_policy_metrics": regime_rows,
        "applicability": applicability_rows,
        "quality_correlation_slices": slice_rows,
    }