#!/usr/bin/env python3
"""Post-result descriptive audit for the frozen V11 negative result.

This script must not change V11 protocol, features, classifier, repair logic,
claim ceiling, or canonical result. It only explains where the preregistered
contradiction-guided operationalisation failed to transfer.
"""
from __future__ import annotations

from collections import Counter
import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path
from typing import Iterable

import numpy as np

from interaction_sensing.simulation import contradiction_development_v11 as v11

CANONICAL_RESULT_SHA256 = "654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1"
CANONICAL_PROTOCOL_SHA256 = "af358226f4afccff3bb148e90a30c5fe9a25c2170d3f223497a22fb3dd685080"


def _episodes(split: str) -> list[v11.Episode]:
    return [
        v11.generate_episode(split, label, intensity, replicate)
        for label in v11.CLASSES
        for intensity in v11.INTENSITIES
        for replicate in range(300)
    ]


def _confusion(true: Iterable[str], predicted: Iterable[str]) -> dict[str, dict[str, int]]:
    matrix = {label: {p: 0 for p in v11.CLASSES} for label in v11.CLASSES}
    for y, yhat in zip(true, predicted, strict=True):
        matrix[y][yhat] += 1
    return matrix


def _diag_name(row: v11.ProbeObservation) -> str:
    state = v11.diagnostic_state(row.evidence, row.observability)
    return (
        "evidence_high_observability_low",
        "evidence_low_observability_high",
        "both_high",
        "both_low",
    )[state.index(1.0)]


def _heldout_shift(model: v11.CentroidModel, heldout: list[v11.Episode]) -> dict[str, object]:
    output: dict[str, object] = {}
    for label in v11.CLASSES:
        subset = [ep for ep in heldout if ep.failure_class == label]
        z = np.vstack([
            (v11.features(ep, model.strategy, model.prefix) - model.mean) / model.scale
            for ep in subset
        ])
        center = z.mean(axis=0)
        distances = {
            candidate: float(np.linalg.norm(center - centroid))
            for candidate, centroid in model.centroids.items()
        }
        ranked = sorted(distances.items(), key=lambda item: (item[1], item[0]))
        correct_distance = distances[label]
        nearest_wrong = min(value for candidate, value in distances.items() if candidate != label)
        output[label] = {
            "development_to_heldout_centroid_distance": correct_distance,
            "nearest_development_centroid": ranked[0][0],
            "nearest_development_centroid_distance": ranked[0][1],
            "correct_minus_nearest_wrong_distance": correct_distance - nearest_wrong,
            "all_development_centroid_distances": distances,
        }
    return output


def audit() -> dict[str, object]:
    summary = json.loads(Path("benchmarks/v11_contradiction_development_result_summary.json").read_text())
    if summary["result_sha256"] != CANONICAL_RESULT_SHA256:
        raise RuntimeError("V11 canonical result identity changed")
    protocol_bytes = Path(v11.PROTOCOL_PATH).read_bytes()
    if hashlib.sha256(protocol_bytes).hexdigest() != CANONICAL_PROTOCOL_SHA256:
        raise RuntimeError("V11 protocol identity changed")

    development = _episodes("development")
    heldout = _episodes("heldout")
    strategies: dict[str, object] = {}
    for strategy in v11.STRATEGIES:
        models = {prefix: v11.fit_centroid_model(development, strategy, prefix) for prefix in range(1, 7)}
        final = models[6]
        predictions = [final.predict(ep) for ep in heldout]
        true = [ep.failure_class for ep in heldout]
        by_intensity: dict[str, object] = {}
        for intensity in v11.INTENSITIES:
            indices = [i for i, ep in enumerate(heldout) if ep.intensity == intensity]
            by_intensity[f"{intensity:.2f}"] = {
                "accuracy": sum(predictions[i] == true[i] for i in indices) / len(indices),
                "confusion": _confusion((true[i] for i in indices), (predictions[i] for i in indices)),
            }
        prefix_accuracy = {}
        for prefix, model in models.items():
            pred = [model.predict(ep) for ep in heldout]
            prefix_accuracy[str(prefix)] = sum(a == b for a, b in zip(pred, true, strict=True)) / len(true)
        strategies[strategy] = {
            "confusion": _confusion(true, predictions),
            "by_intensity": by_intensity,
            "prefix_accuracy": prefix_accuracy,
            "development_to_heldout_geometry": _heldout_shift(final, heldout),
        }

    # Diagnostic-state prevalence is descriptive and uses the fixed CG quadrant map.
    state_by_split_class: dict[str, object] = {}
    for split, episodes in (("development", development), ("heldout", heldout)):
        state_by_split_class[split] = {}
        for label in v11.CLASSES:
            rows = [row for ep in episodes if ep.failure_class == label for row in ep.probes]
            counts = Counter(_diag_name(row) for row in rows)
            state_by_split_class[split][label] = {
                key: counts[key] / len(rows)
                for key in (
                    "evidence_high_observability_low",
                    "evidence_low_observability_high",
                    "both_high",
                    "both_low",
                )
            }

    low_low_audit: dict[str, object] = {}
    for split, episodes in (("development", development), ("heldout", heldout)):
        low_low_audit[split] = {}
        for label in v11.CLASSES:
            audited = [
                row
                for ep in episodes
                if ep.failure_class == label
                for row in ep.probes[4:]
                if row.protected_audit
            ]
            low_low = [row for row in audited if _diag_name(row) == "both_low"]
            true_joint = [row for row in low_low if row.event == 1 and row.disturbance == 1]
            low_low_audit[split][label] = {
                "audited_blind_probe_count": len(audited),
                "audited_both_low_count": len(low_low),
                "audited_both_low_fraction": len(low_low) / len(audited) if audited else 0.0,
                "joint_event_disturbance_given_both_low": len(true_joint) / len(low_low) if low_low else None,
            }

    return {
        "schema": "interaction-sensing-v11-post-result-failure-audit-v1",
        "status": "descriptive-post-result-not-a-new-gate",
        "canonical_result_sha256": CANONICAL_RESULT_SHA256,
        "canonical_protocol_sha256": CANONICAL_PROTOCOL_SHA256,
        "strategies": strategies,
        "diagnostic_state_prevalence": state_by_split_class,
        "protected_audit_low_low_specificity": low_low_audit,
        "interpretation_limits": [
            "This audit cannot change V11 claim level D.",
            "Centroid geometry describes the frozen nearest-centroid operationalisation only.",
            "Quadrant prevalence does not establish causal identification.",
            "Any redesigned diagnostic representation requires a new generation."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V11_FAILURE_AUDIT_SHA256", hashlib.sha256(args.output.read_bytes()).hexdigest())
    for strategy, row in result["strategies"].items():
        print("V11_AUDIT", strategy, "confusion", json.dumps(row["confusion"], sort_keys=True))
        print("V11_AUDIT", strategy, "prefix_accuracy", json.dumps(row["prefix_accuracy"], sort_keys=True))
    for split, classes in result["protected_audit_low_low_specificity"].items():
        for label, row in classes.items():
            print("V11_LOW_LOW", split, label, json.dumps(row, sort_keys=True))


if __name__ == "__main__":
    main()
