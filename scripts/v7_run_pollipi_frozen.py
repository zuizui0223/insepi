#!/usr/bin/env python3
"""Run an exact frozen PolliPi checkout against a canonical V7 artifact.

This script lives outside the frozen PolliPi source tree. It imports only the
frozen observer implementation and passes only pixel arrays to ``analyze``.
Latent labels from the canonical artifact are attached after inference.
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
TRACE_SCHEMA = "pollipi-insepi-v7-pollipi-trace-v1"


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


def _import_analyze(source_root: Path):
    analysis_src = (source_root / "packages" / "analysis" / "src").resolve()
    if not analysis_src.exists():
        raise FileNotFoundError(f"PolliPi analysis source not found: {analysis_src}")
    _purge_module_prefix("pollipi_analysis")
    sys.path.insert(0, str(analysis_src))
    package = importlib.import_module("pollipi_analysis")
    pipeline = importlib.import_module("pollipi_analysis.pipeline")
    package_path = _require_module_under(package, analysis_src, "pollipi_analysis")
    pipeline_path = _require_module_under(pipeline, analysis_src, "pollipi_analysis.pipeline")
    analyze = getattr(pipeline, "analyze", None)
    if analyze is None:
        raise RuntimeError("exact frozen PolliPi pipeline has no analyze()")
    print("V7_POLLIPI_MODULE_ORIGIN PASS", package_path, pipeline_path)
    return analyze


def smoke_test(source_root: Path) -> None:
    analyze = _import_analyze(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(96 + 10 * np.sin(xx * 0.09) + 7 * np.cos(yy * 0.13), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame = np.clip(frame.astype(np.float32) + 55 * np.exp(-((xx - 64) ** 2 + (yy - 48) ** 2) / (2 * 5.0**2)), 0, 255).astype(np.uint8)
    decision = analyze(frame, background)
    if not hasattr(decision, "state") or not hasattr(decision, "features"):
        raise RuntimeError("frozen PolliPi analyze() does not expose expected decision contract")
    print("POLLIPI_FROZEN_ADAPTER_SMOKE PASS", str(decision.state))


def run(source_root: Path, source_commit: str, npz_path: Path, manifest_path: Path, output: Path) -> None:
    analyze = _import_analyze(source_root)
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
    }
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(provenance, sort_keys=True) + "\n")
        for index, meta in enumerate(metadata):
            # Only the two images enter the frozen observer.
            decision = analyze(frames[index], backgrounds[index])
            features = decision.features
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
                "pollipi_state": str(decision.state),
                "pollipi_reason": str(decision.reason),
                "global_synchrony": float(features.global_synchrony),
                "active_cell_proportion": float(features.active_cell_proportion),
                "estimated_global_shift": float(features.estimated_global_shift),
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
