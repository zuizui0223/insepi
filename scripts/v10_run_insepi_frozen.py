#!/usr/bin/env python3
"""Run exact frozen InsePi against the byte-frozen V10 real-pixel artifact.

The current repository's ``interaction_sensing`` package is intentionally never
imported before the frozen checkout is placed first on ``sys.path``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

from v10_trace_common import (
    INSEPI_COMMIT,
    load_trace_pixels,
    pixels_for_condition,
    provenance,
    verify_exact_checkout,
)

TRACE_SCHEMA = "pollipi-insepi-v10-insepi-trace-v1"


def _import_frozen(source_root: Path):
    src = source_root / "src"
    if not src.is_dir():
        raise FileNotFoundError(src)
    sys.path.insert(0, str(src))
    from interaction_sensing.noise import NoiseFirstPolicy  # type: ignore
    from interaction_sensing.simulation.factorial_benchmark_v4 import (  # type: ignore
        _apply_calibrated_local_audit,
        calibrate_occlusion_threshold,
        local_structure_loss,
    )
    from interaction_sensing.simulation.visual_contradiction_v2 import infer_noise_observation  # type: ignore
    return (
        NoiseFirstPolicy,
        infer_noise_observation,
        calibrate_occlusion_threshold,
        local_structure_loss,
        _apply_calibrated_local_audit,
    )


def _components(source_root: Path):
    NoiseFirstPolicy, infer_noise_observation, calibrate, local_structure_loss, apply_audit = _import_frozen(source_root)
    return NoiseFirstPolicy(), float(calibrate()), infer_noise_observation, local_structure_loss, apply_audit


def smoke_test(source_root: Path) -> None:
    verify_exact_checkout(source_root, INSEPI_COMMIT)
    policy, threshold, infer_noise_observation, local_structure_loss, apply_audit = _components(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(95 + 9 * np.sin(xx * 0.08) + 7 * np.cos(yy * 0.12), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[:, 45:82] = np.clip(frame[:, 45:82].astype(np.int16) - 30, 0, 255).astype(np.uint8)
    observation = infer_noise_observation(background, frame, 0)
    structure_loss = float(local_structure_loss(background, frame, observation))
    observation = apply_audit(observation, structure_loss, threshold)
    decision = policy.decide(observation)
    if not hasattr(decision, "false_event_risk") or not hasattr(decision, "state"):
        raise RuntimeError("frozen InsePi decision contract differs from V10 freeze")
    print("V10_INSEPI_FROZEN_SMOKE PASS", observation.source.value, decision.state.value, threshold)


def run(source_root: Path, artifact_dir: Path, freeze_path: Path, output: Path) -> None:
    verify_exact_checkout(source_root, INSEPI_COMMIT)
    policy, threshold, infer_noise_observation, local_structure_loss, apply_audit = _components(source_root)
    backgrounds, frames, condition_keys = load_trace_pixels(artifact_dir, freeze_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prov = provenance(TRACE_SCHEMA, INSEPI_COMMIT)
    prov["occlusion_threshold"] = threshold
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(prov, sort_keys=True) + "\n")
        for condition_index, condition_id in condition_keys:
            frame, background = pixels_for_condition(backgrounds, frames, condition_index)
            observation = infer_noise_observation(background, frame, condition_index)
            structure_loss = float(local_structure_loss(background, frame, observation))
            observation = apply_audit(observation, structure_loss, threshold)
            decision = policy.decide(observation)
            row = {
                "record_type": "result",
                "schema": TRACE_SCHEMA,
                "condition_index": condition_index,
                "condition_id": condition_id,
                "inferred_noise_source": str(observation.source.value),
                "observability_state": str(decision.state.value),
                "false_event_risk": float(decision.false_event_risk),
                "missed_event_risk": float(decision.missed_event_risk),
                "attribution_risk": float(decision.attribution_risk),
                "local_structure_loss": structure_loss,
                "occlusion_threshold": threshold,
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print("V10_INSEPI_TRACE_ROWS", len(condition_keys))
    print("V10_INSEPI_SOURCE_COMMIT", INSEPI_COMMIT)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--freeze", type=Path, default=Path("benchmarks/v10_real_pixel_artifact_freeze.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        smoke_test(args.source_root)
        return
    if args.artifact_dir is None or args.output is None:
        parser.error("normal mode requires --artifact-dir and --output")
    run(args.source_root, args.artifact_dir, args.freeze, args.output)


if __name__ == "__main__":
    main()
