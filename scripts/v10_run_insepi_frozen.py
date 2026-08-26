#!/usr/bin/env python3
"""Run exact frozen InsePi against the byte-frozen V10 real-pixel artifact.

The current repository's ``interaction_sensing`` package is intentionally never
used as the observer. The exact frozen checkout is placed first on ``sys.path``
after any cached package modules are purged, and every imported observer module
must resolve under that checkout before a decision is allowed. The frozen pixel
estimator requires a ``frame_index`` bookkeeping argument, but V10 fixes it to
zero for every condition so condition ordering cannot leak family/tier truth.
Before any V10 pixel is read, the smoke test also requires that decision-relevant
frozen outputs are invariant to the bookkeeping index.
"""
from __future__ import annotations

import argparse
import importlib
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
OBSERVER_FRAME_INDEX = 0
FRAME_INDEX_INVARIANCE_PROBES = (0, 1, 6915)


def _purge_module_prefix(prefix: str) -> None:
    for name in tuple(sys.modules):
        if name == prefix or name.startswith(prefix + "."):
            del sys.modules[name]


def _require_module_under(module, root: Path, label: str) -> Path:
    raw = getattr(module, "__file__", None)
    if not raw:
        raise RuntimeError(f"{label} has no concrete __file__; frozen module origin cannot be verified")
    resolved = Path(raw).resolve()
    expected_root = root.resolve()
    try:
        resolved.relative_to(expected_root)
    except ValueError as exc:
        raise RuntimeError(
            f"{label} imported from wrong origin: {resolved} is not under {expected_root}"
        ) from exc
    return resolved


def _import_frozen(source_root: Path):
    src = (source_root / "src").resolve()
    if not src.is_dir():
        raise FileNotFoundError(src)
    _purge_module_prefix("interaction_sensing")
    sys.path.insert(0, str(src))
    package = importlib.import_module("interaction_sensing")
    noise_module = importlib.import_module("interaction_sensing.noise")
    factorial_module = importlib.import_module("interaction_sensing.simulation.factorial_benchmark_v4")
    visual_module = importlib.import_module("interaction_sensing.simulation.visual_contradiction_v2")
    verified = (
        _require_module_under(package, src, "interaction_sensing"),
        _require_module_under(noise_module, src, "interaction_sensing.noise"),
        _require_module_under(factorial_module, src, "interaction_sensing.simulation.factorial_benchmark_v4"),
        _require_module_under(visual_module, src, "interaction_sensing.simulation.visual_contradiction_v2"),
    )
    print("V10_INSEPI_MODULE_ORIGIN PASS", *(str(path) for path in verified))
    return (
        noise_module.NoiseFirstPolicy,
        visual_module.infer_noise_observation,
        factorial_module.calibrate_occlusion_threshold,
        factorial_module.local_structure_loss,
        factorial_module._apply_calibrated_local_audit,
    )


def _components(source_root: Path):
    NoiseFirstPolicy, infer_noise_observation, calibrate, local_structure_loss, apply_audit = _import_frozen(source_root)
    return NoiseFirstPolicy(), float(calibrate()), infer_noise_observation, local_structure_loss, apply_audit


def _optional_float(value):
    return None if value is None else float(value)


def _decision_signature(
    policy,
    threshold: float,
    infer_noise_observation,
    local_structure_loss,
    apply_audit,
    background: np.ndarray,
    frame: np.ndarray,
    frame_index: int,
):
    observation = infer_noise_observation(background, frame, frame_index)
    structure_loss = float(local_structure_loss(background, frame, observation))
    observation = apply_audit(observation, structure_loss, threshold)
    decision = policy.decide(observation)
    if not hasattr(decision, "false_event_risk") or not hasattr(decision, "state"):
        raise RuntimeError("frozen InsePi decision contract differs from V10 freeze")
    observation_signature = (
        str(observation.source.value),
        float(observation.confidence),
        _optional_float(getattr(observation, "global_motion_score", None)),
        _optional_float(getattr(observation, "coherent_foreground_motion_score", None)),
        _optional_float(getattr(observation, "local_relative_motion_score", None)),
        _optional_float(getattr(observation, "illumination_change", None)),
        _optional_float(getattr(observation, "blur_score", None)),
        _optional_float(getattr(observation, "occlusion_score", None)),
        _optional_float(getattr(observation, "clutter_score", None)),
        json.dumps(getattr(observation, "sensor_scores", {}), sort_keys=True),
        json.dumps(getattr(observation, "metadata", {}), sort_keys=True),
        structure_loss,
    )
    decision_signature = (
        str(decision.state.value),
        float(decision.false_event_risk),
        float(decision.missed_event_risk),
        float(decision.attribution_risk),
        bool(decision.capture_audit),
        bool(decision.record_high_resolution_context),
        tuple(decision.reasons),
    )
    return observation_signature, decision_signature


def smoke_test(source_root: Path) -> None:
    verify_exact_checkout(source_root, INSEPI_COMMIT)
    policy, threshold, infer_noise_observation, local_structure_loss, apply_audit = _components(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(95 + 9 * np.sin(xx * 0.08) + 7 * np.cos(yy * 0.12), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[:, 45:82] = np.clip(frame[:, 45:82].astype(np.int16) - 30, 0, 255).astype(np.uint8)

    signatures = [
        _decision_signature(
            policy,
            threshold,
            infer_noise_observation,
            local_structure_loss,
            apply_audit,
            background,
            frame,
            frame_index,
        )
        for frame_index in FRAME_INDEX_INVARIANCE_PROBES
    ]
    if any(signature != signatures[0] for signature in signatures[1:]):
        raise RuntimeError(
            "exact frozen InsePi decision-relevant outputs depend on frame_index; "
            "V10 pixel-only observer contract is not satisfied"
        )
    print(
        "V10_INSEPI_FROZEN_SMOKE PASS",
        signatures[0][0][0],
        signatures[0][1][0],
        threshold,
    )
    print("V10_INSEPI_FRAME_INDEX_INVARIANCE PASS", *FRAME_INDEX_INVARIANCE_PROBES)


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
            # Keep the observer bookkeeping index constant so only pixels vary.
            observation = infer_noise_observation(background, frame, OBSERVER_FRAME_INDEX)
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
    print("V10_INSEPI_FRAME_INDEX_CONSTANT", OBSERVER_FRAME_INDEX)


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
