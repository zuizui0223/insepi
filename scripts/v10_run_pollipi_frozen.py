#!/usr/bin/env python3
"""Run exact frozen PolliPi against the byte-frozen V10 real-pixel artifact.

Only current/background pixels enter ``analyze``. Result rows deliberately omit
family, tier, disturbance truth, source-video identity and panel assignment.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys

import numpy as np

from v10_trace_common import (
    POLLIPI_COMMIT,
    load_trace_pixels,
    pixels_for_condition,
    provenance,
    verify_exact_checkout,
)

TRACE_SCHEMA = "pollipi-insepi-v10-pollipi-trace-v1"


def _state_text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


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
    if not analysis_src.is_dir():
        raise FileNotFoundError(analysis_src)
    _purge_module_prefix("pollipi_analysis")
    sys.path.insert(0, str(analysis_src))
    package = importlib.import_module("pollipi_analysis")
    pipeline = importlib.import_module("pollipi_analysis.pipeline")
    package_path = _require_module_under(package, analysis_src, "pollipi_analysis")
    pipeline_path = _require_module_under(pipeline, analysis_src, "pollipi_analysis.pipeline")
    analyze = getattr(pipeline, "analyze", None)
    if analyze is None:
        raise RuntimeError("exact frozen PolliPi pipeline has no analyze()")
    print("V10_POLLIPI_MODULE_ORIGIN PASS", package_path, pipeline_path)
    return analyze


def smoke_test(source_root: Path) -> None:
    verify_exact_checkout(source_root, POLLIPI_COMMIT)
    analyze = _import_analyze(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(96 + 8 * np.sin(xx * 0.08) + 6 * np.cos(yy * 0.11), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[43:53, 58:70] = np.clip(frame[43:53, 58:70].astype(np.int16) + 60, 0, 255).astype(np.uint8)
    decision = analyze(frame, background)
    if not hasattr(decision, "state") or not hasattr(decision, "features"):
        raise RuntimeError("frozen PolliPi analyze() contract differs from V10 freeze")
    print("V10_POLLIPI_FROZEN_SMOKE PASS", _state_text(decision.state))


def run(source_root: Path, artifact_dir: Path, freeze_path: Path, output: Path) -> None:
    verify_exact_checkout(source_root, POLLIPI_COMMIT)
    analyze = _import_analyze(source_root)
    backgrounds, frames, condition_keys = load_trace_pixels(artifact_dir, freeze_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(provenance(TRACE_SCHEMA, POLLIPI_COMMIT), sort_keys=True) + "\n")
        for condition_index, condition_id in condition_keys:
            frame, background = pixels_for_condition(backgrounds, frames, condition_index)
            decision = analyze(frame, background)
            features = decision.features
            row = {
                "record_type": "result",
                "schema": TRACE_SCHEMA,
                "condition_index": condition_index,
                "condition_id": condition_id,
                "pollipi_state": _state_text(decision.state),
                "pollipi_reason": str(decision.reason),
                "global_synchrony": float(features.global_synchrony),
                "active_cell_proportion": float(features.active_cell_proportion),
                "estimated_global_shift": float(features.estimated_global_shift),
            }
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print("V10_POLLIPI_TRACE_ROWS", len(condition_keys))
    print("V10_POLLIPI_SOURCE_COMMIT", POLLIPI_COMMIT)


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
