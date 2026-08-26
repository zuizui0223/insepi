#!/usr/bin/env python3
"""Run the preregistered V14 visit-inference development benchmark."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np

from interaction_sensing.simulation.visit_inference_v14 import (
    POLICIES,
    diagnostic_slice,
    evaluate_policy,
    generate_world,
)


DIAGNOSTIC_SLICES = (
    "low_nuisance_unobservable",
    "high_nuisance_observable",
    "masking_observable",
    "support_loss_low_target",
)


def _mean_dict(rows: list[dict[str, float]]) -> dict[str, float]:
    keys = rows[0].keys()
    return {key: float(np.mean([row[key] for row in rows])) for key in keys}


def build_report(contract: dict[str, object]) -> dict[str, object]:
    design = contract["design"]
    if not isinstance(design, dict):
        raise TypeError("design must be an object")
    windows_per_cell = int(design["windows_per_cell"])
    replicates = int(design["replicates"])
    base_seed = int(design["base_seed"])

    policy_metrics: dict[str, list[dict[str, float]]] = {policy: [] for policy in POLICIES}
    slice_metrics: dict[str, dict[str, list[dict[str, float]]]] = {
        policy: {name: [] for name in DIAGNOSTIC_SLICES} for policy in POLICIES
    }

    for replicate in range(replicates):
        world = generate_world(base_seed + replicate, windows_per_cell)
        for policy in POLICIES:
            metric = asdict(evaluate_policy(policy, world))
            metric.pop("policy")
            policy_metrics[policy].append(metric)
            for name in DIAGNOSTIC_SLICES:
                slice_metrics[policy][name].append(diagnostic_slice(world, policy, name))

    aggregate = {policy: _mean_dict(rows) for policy, rows in policy_metrics.items()}
    slices = {
        policy: {name: _mean_dict(rows) for name, rows in policy_slices.items()}
        for policy, policy_slices in slice_metrics.items()
    }

    key_contrasts = {
        "false_absence_triad_minus_target_plus_nuisance": (
            aggregate["triad"]["false_absence_rate_among_true_visits"]
            - aggregate["target_plus_nuisance"]["false_absence_rate_among_true_visits"]
        ),
        "unobservable_contamination_triad_minus_target_plus_nuisance": (
            aggregate["triad"]["unobservable_denominator_contamination"]
            - aggregate["target_plus_nuisance"]["unobservable_denominator_contamination"]
        ),
        "observable_retention_triad": aggregate["triad"]["observable_opportunity_retention"],
        "high_nuisance_observable_triad_denominator_retention": slices["triad"]["high_nuisance_observable"][
            "denominator_eligible_rate"
        ],
        "low_nuisance_unobservable_triad_censor_rate": slices["triad"]["low_nuisance_unobservable"]["censor_rate"],
    }

    report: dict[str, object] = {
        "schema": "pollipi-insepi-v14-visit-inference-result-v1",
        "generation": "V14",
        "role": "development_result_not_field_validation",
        "contract_schema": contract["schema"],
        "design": design,
        "policy_metrics": aggregate,
        "diagnostic_slices": slices,
        "key_contrasts": key_contrasts,
        "claim_boundary": [
            "No field visit accuracy claim.",
            "No calibrated detection probability claim.",
            "No universal superiority claim.",
            "Metrics remain separate; no scalar winner is computed.",
        ],
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["canonical_content_sha256"] = hashlib.sha256(canonical).hexdigest()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="benchmarks/v14_visit_inference_benchmark.json")
    parser.add_argument("--output", default="benchmarks/generated/v14_visit_inference_result.json")
    args = parser.parse_args()

    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    if contract.get("schema") != "pollipi-insepi-v14-visit-inference-benchmark-v1":
        raise SystemExit("unexpected V14 benchmark contract schema")
    report = build_report(contract)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("V14_VISIT_INFERENCE_RESULT", output)
    print("V14_RESULT_SHA256", report["canonical_content_sha256"])
    for policy, metrics in report["policy_metrics"].items():
        print(
            "V14_POLICY",
            policy,
            "false_absence",
            f"{metrics['false_absence_rate_among_true_visits']:.6f}",
            "unobs_contamination",
            f"{metrics['unobservable_denominator_contamination']:.6f}",
            "observable_retention",
            f"{metrics['observable_opportunity_retention']:.6f}",
        )


if __name__ == "__main__":
    main()
