"""Equal-budget competition for independent and disagreement-driven sensing.

Allocation scores use only observable program outputs. Latent truth is consulted
only after selection to score what each policy recovered. This separation is a
hard methodological constraint for the simulation-only paper.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from random import Random
from statistics import mean

POLLIPI_CANDIDATE = {"strong_visitation_candidate", "uncertain_local_activity"}
CORE_POLICIES = (
    "uniform",
    "pollipi_candidate",
    "insepi_audit",
    "union",
    "intersection",
    "disagreement",
)
SINGLE_VIEW_ABLATIONS = (
    "disagreement_pollipi_only",
    "disagreement_insepi_only",
)


@dataclass(frozen=True, slots=True)
class BudgetResult:
    policy: str
    budget_fraction: float
    windows: int
    selected: int
    true_event_recall: float
    hidden_error_recall: float
    missed_event_audit_yield: float
    false_event_audit_yield: float
    attribution_audit_yield: float
    captures_per_hidden_error: float
    disturbance_tv_distance: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _risk(row: Mapping[str, object], key: str) -> float:
    return float(row.get(key, 0.0) or 0.0)


def _row_id(row: Mapping[str, object]) -> str:
    if "scenario_id" in row:
        return str(row["scenario_id"])
    if "condition_id" in row:
        return str(row["condition_id"])
    raise KeyError("row needs scenario_id or condition_id")


def _noise_source(pollipi: Mapping[str, object], insepi: Mapping[str, object]) -> str:
    for row in (pollipi, insepi):
        for key in ("noise_source", "disturbance_family", "inferred_noise_source"):
            if key in row:
                return str(row[key])
    return "unknown"


def allocation_score(
    policy: str,
    pollipi: Mapping[str, object],
    insepi: Mapping[str, object],
) -> float:
    """Return a deployment-available priority score; never reads latent truth."""

    p_state = str(pollipi["pollipi_state"])
    candidate = p_state in POLLIPI_CANDIDATE
    strong = p_state == "strong_visitation_candidate"
    environmental = p_state == "environmental_noise"
    false_risk = _risk(insepi, "false_event_risk")
    missed_risk = _risk(insepi, "missed_event_risk")
    attribution_risk = _risk(insepi, "attribution_risk")
    max_risk = max(false_risk, missed_risk, attribution_risk)

    if policy == "disagreement_pollipi_only":
        false_risk = missed_risk = attribution_risk = max_risk = 0.0
        policy = "disagreement"
    elif policy == "disagreement_insepi_only":
        candidate = strong = environmental = False
        policy = "disagreement"

    if policy == "uniform":
        return 0.0
    if policy == "pollipi_candidate":
        return 1.0 if strong else (0.65 if candidate else 0.0)
    if policy == "insepi_audit":
        return max_risk
    if policy == "union":
        return max(1.0 if candidate else 0.0, max_risk)
    if policy == "intersection":
        return min(1.0 if candidate else 0.0, max_risk)
    if policy == "disagreement":
        if candidate and max_risk >= 0.60:
            return 1.00
        if not candidate and missed_risk >= 0.60:
            return 0.98
        if environmental and max(false_risk, attribution_risk) >= 0.60:
            return 0.92
        if candidate and 0.25 <= max_risk < 0.60:
            return 0.72
        if strong and max_risk < 0.25:
            return 0.45
        return 0.20 * max_risk
    raise ValueError(f"unknown policy: {policy}")


def _align_rows(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
) -> list[tuple[Mapping[str, object], Mapping[str, object]]]:
    p = {_row_id(row): row for row in pollipi_rows}
    i = {_row_id(row): row for row in insepi_rows}
    if set(p) != set(i):
        raise ValueError("scenario/condition IDs differ between traces")
    return [(p[key], i[key]) for key in sorted(p)]


def _latent_error_types(pollipi: Mapping[str, object], insepi: Mapping[str, object]) -> set[str]:
    """Simulation-only truth labels used after allocation, never by the policy."""

    true_visit = bool(pollipi["true_visit"])
    candidate = str(pollipi["pollipi_state"]) in POLLIPI_CANDIDATE
    noise_source = _noise_source(pollipi, insepi).lower()
    tokens = set(noise_source.replace("+", " ").replace("_", " ").split())
    errors: set[str] = set()
    if true_visit and not candidate:
        errors.add("missed_event")
    if not true_visit and candidate:
        errors.add("false_event")
    if true_visit and ({"occlusion", "blur", "smear"} & tokens or "blur_or_focus_loss" in noise_source):
        errors.add("missed_event")
    if candidate and ("clutter" in tokens or "multi_object_clutter" in noise_source):
        errors.add("attribution")
    return errors


def _tv_distance(full_sources: Sequence[str], selected_sources: Sequence[str]) -> float:
    if not full_sources or not selected_sources:
        return 0.0
    labels = sorted(set(full_sources) | set(selected_sources))
    full_n, sel_n = len(full_sources), len(selected_sources)
    return 0.5 * sum(
        abs(full_sources.count(label) / full_n - selected_sources.count(label) / sel_n)
        for label in labels
    )


def evaluate_budget_once(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    policy: str,
    budget_fraction: float = 0.25,
    world_windows: int = 1200,
    seed: int = 1,
) -> BudgetResult:
    if not 0.0 < budget_fraction <= 1.0:
        raise ValueError("budget_fraction must lie in (0, 1]")
    aligned = _align_rows(pollipi_rows, insepi_rows)
    if not aligned:
        raise ValueError("empty traces")
    rng = Random(seed)
    world = [aligned[rng.randrange(len(aligned))] for _ in range(world_windows)]
    scored = [
        (allocation_score(policy, p, i) + rng.random() * 1e-9, index, p, i)
        for index, (p, i) in enumerate(world)
    ]
    selected_n = max(1, round(world_windows * budget_fraction))
    selected = sorted(scored, reverse=True)[:selected_n]
    selected_indices = {index for _, index, _, _ in selected}

    true_events = {idx for idx, (p, _) in enumerate(world) if bool(p["true_visit"])}
    hidden_errors = {
        idx: _latent_error_types(p, i)
        for idx, (p, i) in enumerate(world)
        if _latent_error_types(p, i)
    }
    selected_errors = {idx: hidden_errors[idx] for idx in selected_indices if idx in hidden_errors}

    def recall(indices: set[int]) -> float:
        return len(indices & selected_indices) / len(indices) if indices else 1.0

    def audit_yield(kind: str) -> float:
        count = sum(kind in kinds for kinds in selected_errors.values())
        return count / selected_n

    full_sources = [_noise_source(p, i) for p, i in world]
    selected_sources = [_noise_source(*world[idx]) for idx in selected_indices]
    recovered_errors = len(selected_errors)
    return BudgetResult(
        policy=policy,
        budget_fraction=budget_fraction,
        windows=world_windows,
        selected=selected_n,
        true_event_recall=recall(true_events),
        hidden_error_recall=recall(set(hidden_errors)),
        missed_event_audit_yield=audit_yield("missed_event"),
        false_event_audit_yield=audit_yield("false_event"),
        attribution_audit_yield=audit_yield("attribution"),
        captures_per_hidden_error=(selected_n / recovered_errors if recovered_errors else float("inf")),
        disturbance_tv_distance=_tv_distance(full_sources, selected_sources),
    )


def run_budget_competition(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    *,
    policies: Sequence[str] = CORE_POLICIES,
    budget_fraction: float = 0.25,
    world_windows: int = 1200,
    replicates: int = 100,
    seed: int = 20260821,
) -> list[BudgetResult]:
    p_rows, i_rows = list(pollipi_rows), list(insepi_rows)
    results: list[BudgetResult] = []
    for policy in policies:
        reps = [
            evaluate_budget_once(
                p_rows,
                i_rows,
                policy=policy,
                budget_fraction=budget_fraction,
                world_windows=world_windows,
                seed=seed + replicate * 1009,
            )
            for replicate in range(replicates)
        ]
        results.append(BudgetResult(
            policy=policy,
            budget_fraction=budget_fraction,
            windows=world_windows,
            selected=reps[0].selected,
            true_event_recall=mean(r.true_event_recall for r in reps),
            hidden_error_recall=mean(r.hidden_error_recall for r in reps),
            missed_event_audit_yield=mean(r.missed_event_audit_yield for r in reps),
            false_event_audit_yield=mean(r.false_event_audit_yield for r in reps),
            attribution_audit_yield=mean(r.attribution_audit_yield for r in reps),
            captures_per_hidden_error=mean(r.captures_per_hidden_error for r in reps),
            disturbance_tv_distance=mean(r.disturbance_tv_distance for r in reps),
        ))
    return results
