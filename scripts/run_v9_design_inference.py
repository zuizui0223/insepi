#!/usr/bin/env python3
"""Run the pre-registered V9 design-based inference validation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from math import sqrt
from pathlib import Path
from typing import Iterable, Mapping

from interaction_sensing.simulation.design_inference_v9 import (
    binary_srs_variance,
    exact_hypergeometric_interval,
    finite_population_prevalence,
    sample_prevalence,
    select_frozen_v6_with_reference,
    wilson_interval,
)
from interaction_sensing.simulation.generality_v8 import Regime, generate_world


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks" / "v9_design_inference_protocol.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regimes(protocol: Mapping[str, object]) -> tuple[Regime, ...]:
    world = protocol["world"]
    if not isinstance(world, Mapping):
        raise ValueError("protocol world must be a mapping")
    rows: list[Regime] = []
    for prevalence in world["event_prevalence"]:
        for budget in world["budget_fraction"]:
            for e_quality in world["evidence_quality"]:
                for o_quality in world["observability_quality"]:
                    for correlation in world["residual_correlation"]:
                        for disturbance in world["disturbance_prevalence"]:
                            rows.append(
                                Regime(
                                    event_prevalence=float(prevalence),
                                    budget_fraction=float(budget),
                                    evidence_quality=float(e_quality),
                                    observability_quality=float(o_quality),
                                    residual_correlation=float(correlation),
                                    disturbance_prevalence=float(disturbance),
                                )
                            )
    return tuple(rows)


def _mean(values: Iterable[float]) -> float:
    values = tuple(values)
    return sum(values) / len(values)


def _summarize(rows: list[dict[str, object]]) -> dict[str, float | int]:
    if not rows:
        raise ValueError("cannot summarize no rows")
    return {
        "replicates": len(rows),
        "naive_signed_bias": _mean(float(row["naive_error"]) for row in rows),
        "protected_signed_bias": _mean(float(row["protected_error"]) for row in rows),
        "naive_rmse": sqrt(_mean(float(row["naive_error"]) ** 2 for row in rows)),
        "protected_rmse": sqrt(_mean(float(row["protected_error"]) ** 2 for row in rows)),
        "protected_mean_theory_sd": sqrt(
            _mean(float(row["protected_theory_variance"]) for row in rows)
        ),
        "naive_95_coverage": _mean(float(bool(row["naive_covered"])) for row in rows),
        "protected_95_coverage": _mean(
            float(bool(row["protected_covered"])) for row in rows
        ),
        "naive_mean_interval_width": _mean(float(row["naive_interval_width"]) for row in rows),
        "protected_mean_interval_width": _mean(
            float(row["protected_interval_width"]) for row in rows
        ),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty CSV")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(protocol: Mapping[str, object]) -> tuple[list[dict[str, object]], dict[str, object]]:
    world_spec = protocol["world"]
    if not isinstance(world_spec, Mapping):
        raise ValueError("protocol world must be a mapping")
    population_size = int(world_spec["finite_population_size"])
    paired_replicates = int(world_spec["paired_replicates"])
    base_seed = int(protocol["seed"])

    replicate_rows: list[dict[str, object]] = []
    regime_rows = regimes(protocol)
    for regime_index, regime in enumerate(regime_rows):
        for replicate in range(paired_replicates):
            world_seed = base_seed + regime_index * 100_003 + replicate * 101
            selection_seed = base_seed + regime_index * 1_000_003 + replicate * 1_009
            world = generate_world(n=population_size, regime=regime, seed=world_seed)
            selection = select_frozen_v6_with_reference(
                world, budget_fraction=regime.budget_fraction, seed=selection_seed
            )

            target = finite_population_prevalence(world)
            selected_n = len(selection.selected)
            reference_n = len(selection.protected_exploration)
            selected_successes = sum(int(world[index].true_event) for index in selection.selected)
            reference_successes = sum(
                int(world[index].true_event) for index in selection.protected_exploration
            )

            naive_estimate = sample_prevalence(world, selection.selected)
            protected_estimate = sample_prevalence(world, selection.protected_exploration)
            naive_interval = wilson_interval(selected_successes, selected_n, confidence=0.95)
            protected_interval = exact_hypergeometric_interval(
                population_size, reference_n, reference_successes, confidence=0.95
            )
            theory_variance = binary_srs_variance(
                population_size=population_size,
                sample_size=reference_n,
                prevalence=target,
            )

            replicate_rows.append(
                {
                    "event_prevalence_nominal": regime.event_prevalence,
                    "budget_fraction": regime.budget_fraction,
                    "evidence_quality": regime.evidence_quality,
                    "observability_quality": regime.observability_quality,
                    "residual_correlation": regime.residual_correlation,
                    "disturbance_prevalence": regime.disturbance_prevalence,
                    "replicate": replicate,
                    "realized_prevalence": target,
                    "selected_n": selected_n,
                    "protected_exploration_n": reference_n,
                    "naive_estimate": naive_estimate,
                    "protected_estimate": protected_estimate,
                    "naive_error": naive_estimate - target,
                    "protected_error": protected_estimate - target,
                    "protected_theory_variance": theory_variance,
                    "naive_interval_lower": naive_interval.lower,
                    "naive_interval_upper": naive_interval.upper,
                    "naive_interval_width": naive_interval.width,
                    "naive_covered": naive_interval.covers(target),
                    "protected_interval_lower": protected_interval.lower,
                    "protected_interval_upper": protected_interval.upper,
                    "protected_interval_width": protected_interval.width,
                    "protected_covered": protected_interval.covers(target),
                }
            )

    grouped: dict[tuple[float, float], list[dict[str, object]]] = defaultdict(list)
    by_prevalence: dict[float, list[dict[str, object]]] = defaultdict(list)
    by_budget: dict[float, list[dict[str, object]]] = defaultdict(list)
    for row in replicate_rows:
        prevalence = float(row["event_prevalence_nominal"])
        budget = float(row["budget_fraction"])
        grouped[(prevalence, budget)].append(row)
        by_prevalence[prevalence].append(row)
        by_budget[budget].append(row)

    result = {
        "schema": "interaction-sensing-v9-design-inference-result-v1",
        "protocol_schema": protocol["schema"],
        "headline": {
            "regime_count": len(regime_rows),
            "world_count": len(replicate_rows),
            **_summarize(replicate_rows),
        },
        "by_nominal_prevalence": {
            f"{key:.2f}": _summarize(by_prevalence[key]) for key in sorted(by_prevalence)
        },
        "by_budget": {
            f"{key:.2f}": _summarize(by_budget[key]) for key in sorted(by_budget)
        },
        "by_prevalence_budget": [
            {
                "event_prevalence_nominal": key[0],
                "budget_fraction": key[1],
                **_summarize(grouped[key]),
            }
            for key in sorted(grouped)
        ],
    }
    return replicate_rows, result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--output-dir", type=Path, default=Path(".v9/design-inference"))
    args = parser.parse_args()

    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    replicate_rows, result = run(protocol)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    replicate_path = output_dir / "v9_replicate_metrics.csv"
    result_path = output_dir / "v9_design_inference_result.json"
    group_path = output_dir / "v9_prevalence_budget_summary.csv"
    manifest_path = output_dir / "v9_design_inference_manifest.json"

    _write_csv(replicate_path, replicate_rows)
    _write_csv(group_path, list(result["by_prevalence_budget"]))
    result_path.write_text(
        json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": "interaction-sensing-v9-design-inference-manifest-v1",
        "protocol_sha256": sha256_file(args.protocol),
        "result_sha256": sha256_file(result_path),
        "replicate_csv_sha256": sha256_file(replicate_path),
        "group_csv_sha256": sha256_file(group_path),
        "frozen_candidate": protocol["frozen_candidate"],
        "v7_materialised": False,
    }
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    headline = result["headline"]
    print("V9_REGIMES", headline["regime_count"])
    print("V9_WORLDS", headline["world_count"])
    print("V9_NAIVE_BIAS", headline["naive_signed_bias"])
    print("V9_PROTECTED_BIAS", headline["protected_signed_bias"])
    print("V9_NAIVE_RMSE", headline["naive_rmse"])
    print("V9_PROTECTED_RMSE", headline["protected_rmse"])
    print("V9_PROTECTED_THEORY_SD", headline["protected_mean_theory_sd"])
    print("V9_NAIVE_COVERAGE", headline["naive_95_coverage"])
    print("V9_PROTECTED_COVERAGE", headline["protected_95_coverage"])
    print("V9_PROTOCOL_SHA256", manifest["protocol_sha256"])
    print("V9_RESULT_SHA256", manifest["result_sha256"])


if __name__ == "__main__":
    main()
