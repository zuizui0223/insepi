#!/usr/bin/env python3
"""Run the pre-registered V8 generality benchmark and emit auditable artifacts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping

from interaction_sensing.simulation.generality_v8 import run_protocol


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_csv(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    rows = list(rows)
    if not rows:
        raise ValueError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default="benchmarks/v8_generality_protocol.json", type=Path)
    parser.add_argument("--output-dir", default=".v8/generality", type=Path)
    args = parser.parse_args()

    protocol_bytes = args.protocol.read_bytes()
    protocol = json.loads(protocol_bytes)
    result = run_protocol(protocol)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "v8_generality_result.json"
    metrics_path = args.output_dir / "v8_regime_policy_metrics.csv"
    applicability_path = args.output_dir / "v8_applicability.csv"
    slices_path = args.output_dir / "v8_quality_correlation_slices.csv"

    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_csv(metrics_path, result["regime_policy_metrics"])
    _write_csv(applicability_path, result["applicability"])
    _write_csv(slices_path, result["quality_correlation_slices"])

    manifest = {
        "schema": "interaction-sensing-v8-generality-manifest-v1",
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "result_sha256": _sha256(result_path),
        "metrics_csv_sha256": _sha256(metrics_path),
        "applicability_csv_sha256": _sha256(applicability_path),
        "slices_csv_sha256": _sha256(slices_path),
        "frozen_candidate": protocol["frozen_candidate"],
        "no_tuning_rule": protocol["no_tuning_rule"],
    }
    manifest_path = args.output_dir / "v8_generality_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    headline = result["headline"]
    print("V8_REGIMES", headline["regime_count"])
    print("V8_V6_GE_UNIFORM", headline["v6_ge_uniform_count"])
    print("V8_V6_BEST_SAME_ALPHA", headline["v6_best_same_alpha_count"])
    print("V8_MEAN_V6_JOINT", headline["mean_v6_joint_ratio"])
    print("V8_MEAN_DELTA_BEST_SAME_ALPHA", headline["mean_v6_minus_best_same_alpha_joint"])
    print("V8_NAIVE_PREVALENCE_RMSE", headline["mean_v6_naive_prevalence_rmse"])
    print("V8_EXPLORATION_PREVALENCE_RMSE", headline["mean_v6_exploration_prevalence_rmse"])
    print("V8_PROTOCOL_SHA256", manifest["protocol_sha256"])
    print("V8_RESULT_SHA256", manifest["result_sha256"])


if __name__ == "__main__":
    main()
