#!/usr/bin/env python3
"""Run an exact frozen InsePi checkout against a canonical V7 artifact.

The script imports the frozen noise/observability implementation from an external
checkout. Latent labels are never passed into the observer; they are attached to
trace rows only after inference. The frozen API requires a bookkeeping
``frame_index``; before V7 materialisation the smoke test proves that
decision-relevant outputs are invariant to that index on fixed pixels.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

import numpy as np

ARTIFACT_SCHEMA = "pollipi-insepi-v7-pixel-artifact-v1"
TRACE_SCHEMA = "pollipi-insepi-v7-insepi-trace-v1"
FRAME_INDEX_INVARIANCE_PROBES = (0, 1, 179)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_artifact(npz_path: Path, manifest_path: Path):
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if raw.get("schema") != ARTIFACT_SCHEMA:
        raise ValueError("unexpected V7 artifact schema")
    actual = _sha256_file(npz_path)
    if actual != raw.get("npz_sha256"):
        raise ValueError("V7 artifact SHA-256 mismatch")
    with np.load(npz_path, allow_pickle=False) as payload:
        backgrounds = payload["backgrounds"].astype(np.uint8)
        frames = payload["frames"].astype(np.uint8)
        metadata = json.loads(str(payload["metadata_json"].item()))
    if backgrounds.shape != frames.shape or backgrounds.ndim != 3:
        raise ValueError("invalid V7 image tensor")
    if len(metadata) != backgrounds.shape[0] or len(metadata) != int(raw["condition_count"]):
        raise ValueError("V7 artifact condition count mismatch")
    return raw, backgrounds, frames, metadata


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
    if not src.exists():
        raise FileNotFoundError(f"InsePi source not found: {src}")
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
    print("V7_INSEPI_MODULE_ORIGIN PASS", *(str(path) for path in verified))
    return (
        noise_module.NoiseFirstPolicy,
        visual_module.infer_noise_observation,
        factorial_module.calibrate_occlusion_threshold,
        factorial_module.local_structure_loss,
        factorial_module._apply_calibrated_local_audit,
    )


def _decision_components(source_root: Path):
    (
        NoiseFirstPolicy,
        infer_noise_observation,
        calibrate_occlusion_threshold,
        local_structure_loss,
        apply_local_audit,
    ) = _import_frozen(source_root)
    threshold = float(calibrate_occlusion_threshold())
    policy = NoiseFirstPolicy()
    return policy, threshold, infer_noise_observation, local_structure_loss, apply_local_audit


def _decide(source_root: Path, background: np.ndarray, frame: np.ndarray, frame_index: int):
    policy, threshold, infer_noise_observation, local_structure_loss, apply_local_audit = _decision_components(source_root)
    observation = infer_noise_observation(background, frame, frame_index)
    structure_loss = float(local_structure_loss(background, frame, observation))
    observation = apply_local_audit(observation, structure_loss, threshold)
    decision = policy.decide(observation)
    return observation, decision, structure_loss, threshold


def _optional_float(value):
    return None if value is None else float(value)


def _decision_signature(observation, decision, structure_loss: float):
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
        float(structure_loss),
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
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(95 + 12 * np.sin(xx * 0.08) + 9 * np.cos(yy * 0.12), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[:, 48:80] = np.clip(frame[:, 48:80].astype(np.float32) - 28, 0, 255).astype(np.uint8)
    results = [_decide(source_root, background, frame, index) for index in FRAME_INDEX_INVARIANCE_PROBES]
    signatures = [_decision_signature(observation, decision, structure_loss) for observation, decision, structure_loss, _ in results]
    if any(signature != signatures[0] for signature in signatures[1:]):
        raise RuntimeError(
            "exact frozen InsePi decision-relevant outputs depend on frame_index; "
            "V7 image-only observer boundary is not satisfied"
        )
    observation, decision, _structure_loss, threshold = results[0]
    if not hasattr(observation, "source") or not hasattr(decision, "state"):
        raise RuntimeError("frozen InsePi observer does not expose expected decision contract")
    print("INSEPI_FROZEN_ADAPTER_SMOKE PASS", observation.source.value, decision.state.value, threshold)
    print("V7_INSEPI_FRAME_INDEX_INVARIANCE PASS", *FRAME_INDEX_INVARIANCE_PROBES)


def run(source_root: Path, source_commit: str, npz_path: Path, manifest_path: Path, output: Path) -> None:
    (
        NoiseFirstPolicy,
        infer_noise_observation,
        calibrate_occlusion_threshold,
        local_structure_loss,
        apply_local_audit,
    ) = _import_frozen(source_root)
    threshold = float(calibrate_occlusion_threshold())
    policy = NoiseFirstPolicy()
    manifest, backgrounds, frames, metadata = _load_artifact(npz_path, manifest_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    provenance = {
        "record_type": "provenance",
        "schema": TRACE_SCHEMA,
        "source_commit": source_commit,
        "world_fingerprint": manifest["world_fingerprint"],
        "world_spec_sha256": manifest["world_spec_sha256"],
        "pixel_artifact_sha256": manifest["npz_sha256"],
        "condition_count": int(manifest["condition_count"]),
        "occlusion_threshold": threshold,
    }
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(provenance, sort_keys=True) + "\n")
        for index, meta in enumerate(metadata):
            # Only images and the pre-registered deterministic bookkeeping index
            # enter the frozen observer. The pre-materialisation smoke gate above
            # requires decision-relevant outputs to be invariant to this index.
            observation = infer_noise_observation(backgrounds[index], frames[index], index)
            structure_loss = float(local_structure_loss(backgrounds[index], frames[index], observation))
            observation = apply_local_audit(observation, structure_loss, threshold)
            decision = policy.decide(observation)
            row = {
                "record_type": "result",
                "schema": TRACE_SCHEMA,
                "condition_id": str(meta["condition_id"]),
                "family": str(meta["family"]),
                "tier": int(meta["tier"]),
                "replicate": int(meta["replicate"]),
                "true_visit": bool(meta["true_visit"]),
                "event_visibility": float(meta["event_visibility"]),
                "intensity": float(meta["intensity"]),
                "inferred_noise_source": str(observation.source.value),
                "observability_state": str(decision.state.value),
                "false_event_risk": float(decision.false_event_risk),
                "missed_event_risk": float(decision.missed_event_risk),
                "attribution_risk": float(decision.attribution_risk),
                "local_structure_loss": structure_loss,
                "occlusion_threshold": threshold,
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-commit", default="")
    parser.add_argument("--npz", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        smoke_test(args.source_root)
        return
    if not args.source_commit or args.npz is None or args.manifest is None or args.output is None:
        parser.error("normal mode requires --source-commit --npz --manifest --output")
    run(args.source_root, args.source_commit, args.npz, args.manifest, args.output)


if __name__ == "__main__":
    main()
