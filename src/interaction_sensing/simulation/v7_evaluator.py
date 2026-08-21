"""Trace-only evaluator for one-shot V7 validation.

The evaluator knows nothing about pixels or observer implementation. It consumes
already emitted PolliPi/InsePi traces from the same canonical artifact, samples
paired prevalence/budget worlds, evaluates the pre-registered baselines and frozen
V6 portfolio, then applies the locked pass/fail rules.

``hidden_error_recall`` is deliberately an observer-relative audit metric: it asks
whether allocated audit effort recovers latent-truth errors made by the PolliPi
biological-evidence observer. It must not be described as a world-intrinsic error
rate. To make that distinction auditable, V7 also reports two observer-independent
secondary coverage metrics: recall of all disturbed windows and recall of true
events occurring under disturbance. These secondary metrics do not alter the
pre-registered hard gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from math import isfinite
from pathlib import Path
from random import Random
from statistics import mean
from typing import Iterable, Mapping, Sequence

from interaction_sensing.simulation.budget_competition import allocation_score
from interaction_sensing.simulation.observer_portfolio_v6 import (
    PortfolioWeights,
    _score_selection,
    align_rows,
    sample_world,
    select_portfolio_indices,
)


POLLIPI_TRACE_SCHEMA = "pollipi-insepi-v7-pollipi-trace-v1"
INSEPI_TRACE_SCHEMA = "pollipi-insepi-v7-insepi-trace-v1"
BASELINE_SCHEMA = "pollipi-insepi-v7-baselines-v1"
REPORT_SCHEMA = "pollipi-insepi-v7-report-v1"


@dataclass(frozen=True, slots=True)
class PolicyMetric:
    prevalence: float
    budget: float
    policy: str
    true_event_recall: float
    hidden_error_recall: float
    disturbance_window_recall: float
    disturbed_true_event_recall: float
    captures_per_hidden_error: float
    disturbance_tv_distance: float

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if not isfinite(self.captures_per_hidden_error):
            payload["captures_per_hidden_error"] = None
        return payload


@dataclass(frozen=True, slots=True)
class PolicyRobustness:
    policy: str
    worst_joint_ratio: float
    mean_joint_ratio: float
    max_tv: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class V7GateResult:
    passed: bool
    failures: tuple[str, ...]
    v6: PolicyRobustness
    policy_robustness: tuple[PolicyRobustness, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "failures": list(self.failures),
            "v6": self.v6.to_dict(),
            "policy_robustness": [row.to_dict() for row in self.policy_robustness],
        }


def _canonical_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def load_baseline_registry(path: str | Path) -> dict[str, object]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema") != BASELINE_SCHEMA:
        raise ValueError("unexpected V7 baseline registry schema")
    expected = raw.get("registry_sha256")
    canonical = {"schema": raw["schema"], "entries": raw["entries"]}
    actual = _canonical_hash(canonical)
    if expected != actual:
        raise ValueError(f"V7 baseline registry hash mismatch: expected={expected} actual={actual}")
    return raw


def read_trace_jsonl(
    path: str | Path,
    *,
    expected_schema: str,
    expected_world_fingerprint: str,
    expected_pixel_sha256: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    records = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    provenance = [row for row in records if row.get("record_type") == "provenance"]
    results = [row for row in records if row.get("record_type") == "result"]
    if len(provenance) != 1:
        raise ValueError("V7 trace must contain exactly one provenance row")
    prov = provenance[0]
    if prov.get("schema") != expected_schema:
        raise ValueError("unexpected V7 trace schema")
    if prov.get("world_fingerprint") != expected_world_fingerprint:
        raise ValueError("V7 trace world fingerprint mismatch")
    if prov.get("pixel_artifact_sha256") != expected_pixel_sha256:
        raise ValueError("V7 trace pixel artifact mismatch")
    if not prov.get("source_commit"):
        raise ValueError("V7 trace is missing source_commit")
    if not results:
        raise ValueError("V7 trace has no results")
    ids = [str(row["condition_id"]) for row in results]
    if len(ids) != len(set(ids)):
        raise ValueError("V7 trace condition IDs are not unique")
    return prov, results


def _normalise_rows(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    normalised: list[dict[str, object]] = []
    for row in rows:
        payload = dict(row)
        if "disturbance_family" not in payload and "family" in payload:
            payload["disturbance_family"] = payload["family"]
        normalised.append(payload)
    return normalised


def _derived_eval_seed(master_seed_hex: str, prevalence: float, budget: float, replicate: int) -> int:
    payload = f"v7-eval-v1|{master_seed_hex}|{prevalence:.6f}|{budget:.6f}|{replicate}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def _select_legacy(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    *,
    policy: str,
    budget: float,
    seed: int,
) -> set[int]:
    selected_n = max(1, round(len(world) * budget))
    rng = Random(seed)
    scored = [
        (allocation_score(policy, pollipi, insepi) + rng.random() * 1e-9, index)
        for index, (pollipi, insepi) in enumerate(world)
    ]
    return {index for _, index in sorted(scored, reverse=True)[:selected_n]}


def _weights(entry: Mapping[str, object]) -> PortfolioWeights:
    raw = entry.get("weights")
    if not isinstance(raw, Mapping):
        raise ValueError("portfolio registry entry is missing weights")
    return PortfolioWeights(
        exploration=float(raw["exploration"]),
        pollipi=float(raw["pollipi"]),
        insepi=float(raw["insepi"]),
        disagreement=float(raw["disagreement"]),
    )


def _policy_selection(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    entry: Mapping[str, object],
    *,
    budget: float,
    seed: int,
) -> set[int]:
    kind = str(entry["kind"])
    if kind == "legacy":
        name = str(entry["name"])
        mapping = {
            "uniform": "uniform",
            "pollipi_candidate": "pollipi_candidate",
            "insepi_audit": "insepi_audit",
            "legacy_fixed_disagreement": "disagreement",
            "candidate_or_risky": "union",
            "candidate_and_risky": "intersection",
        }
        try:
            legacy_policy = mapping[name]
        except KeyError as exc:
            raise ValueError(f"unknown legacy V7 policy: {name}") from exc
        return _select_legacy(world, policy=legacy_policy, budget=budget, seed=seed)
    if kind in {"portfolio", "portfolio_ablation"}:
        selected, _ = select_portfolio_indices(
            world,
            budget_fraction=budget,
            weights=_weights(entry),
            seed=seed,
        )
        return selected
    raise ValueError(f"unknown V7 policy kind: {kind}")


def _family(pair: tuple[Mapping[str, object], Mapping[str, object]]) -> str:
    pollipi, insepi = pair
    for row in (pollipi, insepi):
        if row.get("disturbance_family") is not None:
            return str(row["disturbance_family"])
        if row.get("family") is not None:
            return str(row["family"])
    return "unknown"


def _recall(indices: set[int], selected: set[int]) -> float:
    return len(indices & selected) / len(indices) if indices else 1.0


def _observer_independent_coverage(
    world: Sequence[tuple[Mapping[str, object], Mapping[str, object]]],
    selected: set[int],
) -> tuple[float, float]:
    """Return coverage metrics defined only from latent world labels.

    These metrics do not inspect PolliPi state or InsePi risk predictions.
    """

    disturbed = {
        index for index, pair in enumerate(world)
        if _family(pair) != "clean"
    }
    disturbed_true_events = {
        index for index, pair in enumerate(world)
        if _family(pair) != "clean" and bool(pair[0].get("true_visit", False))
    }
    return (
        _recall(disturbed, selected),
        _recall(disturbed_true_events, selected),
    )


def evaluate_v7_traces(
    pollipi_rows: Iterable[Mapping[str, object]],
    insepi_rows: Iterable[Mapping[str, object]],
    baseline_registry: Mapping[str, object],
    *,
    master_seed_hex: str,
    prevalences: Sequence[float] = (0.1, 0.5, 0.9),
    budgets: Sequence[float] = (0.1, 0.25, 0.5),
    world_windows: int = 4800,
    replicates: int = 200,
) -> list[PolicyMetric]:
    pollipi = _normalise_rows(pollipi_rows)
    insepi = _normalise_rows(insepi_rows)
    aligned = align_rows(pollipi, insepi)
    entries = list(baseline_registry["entries"])
    accum: dict[
        tuple[float, float, str],
        list[tuple[float, float, float, float, float, float]],
    ] = {}

    for prevalence in prevalences:
        for budget in budgets:
            for replicate in range(replicates):
                world_seed = _derived_eval_seed(master_seed_hex, prevalence, budget, replicate)
                world = sample_world(
                    aligned,
                    prevalence=prevalence,
                    world_windows=world_windows,
                    seed=world_seed,
                )
                for policy_index, entry in enumerate(entries):
                    policy_name = str(entry["name"])
                    selection_seed = world_seed + 7919 + policy_index * 104729
                    selected = _policy_selection(
                        world,
                        entry,
                        budget=budget,
                        seed=selection_seed,
                    )
                    result = _score_selection(
                        world,
                        selected,
                        prevalence=prevalence,
                        budget_fraction=budget,
                        weights=(
                            _weights(entry)
                            if str(entry["kind"]) in {"portfolio", "portfolio_ablation"}
                            else PortfolioWeights(1.0, 0.0, 0.0, 0.0)
                        ),
                    )
                    disturbance_recall, disturbed_event_recall = _observer_independent_coverage(
                        world,
                        selected,
                    )
                    accum.setdefault((prevalence, budget, policy_name), []).append((
                        result.true_event_recall,
                        result.hidden_error_recall,
                        disturbance_recall,
                        disturbed_event_recall,
                        result.captures_per_hidden_error,
                        result.disturbance_tv_distance,
                    ))

    metrics: list[PolicyMetric] = []
    for (prevalence, budget, policy), values in sorted(accum.items()):
        finite_cpe = [row[4] for row in values if isfinite(row[4])]
        metrics.append(PolicyMetric(
            prevalence=prevalence,
            budget=budget,
            policy=policy,
            true_event_recall=mean(row[0] for row in values),
            hidden_error_recall=mean(row[1] for row in values),
            disturbance_window_recall=mean(row[2] for row in values),
            disturbed_true_event_recall=mean(row[3] for row in values),
            captures_per_hidden_error=(mean(finite_cpe) if finite_cpe else float("inf")),
            disturbance_tv_distance=mean(row[5] for row in values),
        ))
    return metrics


def _strictly_dominates(left: PolicyRobustness, right: PolicyRobustness) -> bool:
    left_tuple = (left.worst_joint_ratio, left.mean_joint_ratio, -left.max_tv)
    right_tuple = (right.worst_joint_ratio, right.mean_joint_ratio, -right.max_tv)
    return all(a >= b for a, b in zip(left_tuple, right_tuple, strict=True)) and any(
        a > b for a, b in zip(left_tuple, right_tuple, strict=True)
    )


def apply_locked_gate(
    metrics: Sequence[PolicyMetric],
    *,
    joint_ratio_floor: float = 0.98,
    mean_joint_ratio_strictly_above: float = 1.0,
    max_tv: float = 0.25,
    legacy_tolerance: float = 0.01,
) -> V7GateResult:
    by_key = {(row.prevalence, row.budget, row.policy): row for row in metrics}
    regimes = sorted({(row.prevalence, row.budget) for row in metrics})
    policies = sorted({row.policy for row in metrics})
    if "uniform" not in policies or "v6_frozen" not in policies:
        raise ValueError("V7 gate requires uniform and v6_frozen")

    robustness: list[PolicyRobustness] = []
    for policy in policies:
        joint_ratios: list[float] = []
        tvs: list[float] = []
        for prevalence, budget in regimes:
            candidate = by_key[(prevalence, budget, policy)]
            uniform = by_key[(prevalence, budget, "uniform")]
            event_ratio = candidate.true_event_recall / uniform.true_event_recall
            error_ratio = candidate.hidden_error_recall / uniform.hidden_error_recall
            joint_ratios.append(min(event_ratio, error_ratio))
            tvs.append(candidate.disturbance_tv_distance)
        robustness.append(PolicyRobustness(
            policy=policy,
            worst_joint_ratio=min(joint_ratios),
            mean_joint_ratio=mean(joint_ratios),
            max_tv=max(tvs),
        ))
    robust_by_name = {row.policy: row for row in robustness}
    v6 = robust_by_name["v6_frozen"]
    failures: list[str] = []

    # Rule 1: every regime joint ratio >= floor.
    for prevalence, budget in regimes:
        candidate = by_key[(prevalence, budget, "v6_frozen")]
        uniform = by_key[(prevalence, budget, "uniform")]
        joint = min(
            candidate.true_event_recall / uniform.true_event_recall,
            candidate.hidden_error_recall / uniform.hidden_error_recall,
        )
        if joint < joint_ratio_floor:
            failures.append(f"joint_ratio_below_floor:p={prevalence}:b={budget}:{joint:.6f}")

    if not v6.mean_joint_ratio > mean_joint_ratio_strictly_above:
        failures.append(f"mean_joint_ratio_not_above_{mean_joint_ratio_strictly_above}")
    if v6.max_tv > max_tv:
        failures.append(f"max_tv_above_{max_tv}:{v6.max_tv:.6f}")

    for legacy in (
        "pollipi_candidate",
        "insepi_audit",
        "legacy_fixed_disagreement",
        "candidate_or_risky",
        "candidate_and_risky",
    ):
        other = robust_by_name[legacy]
        if v6.worst_joint_ratio + legacy_tolerance < other.worst_joint_ratio:
            failures.append(f"legacy_worst_joint_superior:{legacy}")

    for ablation in ("v6_no_pollipi", "v6_no_insepi"):
        if _strictly_dominates(robust_by_name[ablation], v6):
            failures.append(f"arm_removal_strictly_dominates:{ablation}")

    return V7GateResult(
        passed=not failures,
        failures=tuple(failures),
        v6=v6,
        policy_robustness=tuple(sorted(robustness, key=lambda row: row.policy)),
    )


def build_report(
    *,
    metrics: Sequence[PolicyMetric],
    gate: V7GateResult,
    provenance: Mapping[str, object],
) -> dict[str, object]:
    report = {
        "schema": REPORT_SCHEMA,
        "provenance": dict(provenance),
        "metric_semantics": {
            "hidden_error_recall": (
                "observer-relative recovery of latent-truth PolliPi detection/attribution errors"
            ),
            "disturbance_window_recall": (
                "observer-independent coverage of latent non-clean disturbance windows"
            ),
            "disturbed_true_event_recall": (
                "observer-independent coverage of latent true events under non-clean disturbance"
            ),
        },
        "metrics": [row.to_dict() for row in metrics],
        "gate": gate.to_dict(),
    }
    report["report_sha256"] = _canonical_hash(report)
    return report
