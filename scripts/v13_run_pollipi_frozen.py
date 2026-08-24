#!/usr/bin/env python3
"""Run exact frozen PolliPi on the truth-free V13 canonical pixel artifact."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from interaction_sensing.physical_artifact_v13 import load_pixel_artifact, sha256_file

POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
TRACE_SCHEMA = "pollipi-insepi-v13-pollipi-phase-trace-v1"


def verify_exact_checkout(root: Path) -> None:
    actual = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != POLLIPI_COMMIT:
        raise RuntimeError(f"PolliPi frozen checkout mismatch: {actual} != {POLLIPI_COMMIT}")


def _state_text(value: object) -> str:
    return str(getattr(value, "value", value))


def _purge(prefix: str) -> None:
    for name in tuple(sys.modules):
        if name == prefix or name.startswith(prefix + "."):
            del sys.modules[name]


def import_analyze(source_root: Path):
    analysis_src = (source_root / "packages" / "analysis" / "src").resolve()
    if not analysis_src.is_dir():
        raise FileNotFoundError(analysis_src)
    _purge("pollipi_analysis")
    sys.path.insert(0, str(analysis_src))
    package = importlib.import_module("pollipi_analysis")
    pipeline = importlib.import_module("pollipi_analysis.pipeline")
    for module, label in ((package, "pollipi_analysis"), (pipeline, "pollipi_analysis.pipeline")):
        path = Path(str(module.__file__)).resolve()
        try:
            path.relative_to(analysis_src)
        except ValueError as exc:
            raise RuntimeError(f"{label} imported outside exact frozen checkout: {path}") from exc
    analyze = getattr(pipeline, "analyze", None)
    if analyze is None:
        raise RuntimeError("exact frozen PolliPi has no analyze()")
    return analyze


def smoke_test(source_root: Path) -> None:
    verify_exact_checkout(source_root)
    analyze = import_analyze(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(96 + 8 * np.sin(xx * 0.08) + 6 * np.cos(yy * 0.11), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[43:53, 58:70] = np.clip(frame[43:53, 58:70].astype(np.int16) + 60, 0, 255).astype(np.uint8)
    decision = analyze(frame, background)
    if not hasattr(decision, "state") or not hasattr(decision, "features"):
        raise RuntimeError("frozen PolliPi decision contract changed")
    print("V13_POLLIPI_FROZEN_SMOKE PASS", _state_text(decision.state))


def run(source_root: Path, artifact_dir: Path, output: Path) -> None:
    verify_exact_checkout(source_root)
    artifact = load_pixel_artifact(artifact_dir)
    analyze = import_analyze(source_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    pixel_receipt_path = artifact_dir / "v13_pixel_receipt.json"
    provenance = {
        "record_type": "provenance",
        "schema": TRACE_SCHEMA,
        "source_commit": POLLIPI_COMMIT,
        "pixel_receipt_sha256": sha256_file(pixel_receipt_path),
        "frames_raw_sha256": artifact.receipt["array_contract"]["frames_raw_sha256"],
        "backgrounds_raw_sha256": artifact.receipt["array_contract"]["backgrounds_raw_sha256"],
        "result_row_count": 180 * 4 * 8,
        "truth_metadata_received": False,
    }
    rows_written = 0
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(provenance, sort_keys=True) + "\n")
        for phase in artifact.registry:
            block_index = int(phase["block_index"])
            phase_index = int(phase["phase_index"])
            background = artifact.backgrounds[block_index]
            for sample_index in range(8):
                frame = artifact.frames[block_index, phase_index, sample_index]
                decision = analyze(frame, background)
                features = decision.features
                row = {
                    "record_type": "result",
                    "schema": TRACE_SCHEMA,
                    "block_index": block_index,
                    "opaque_block_id": str(phase["opaque_block_id"]),
                    "split": str(phase["split"]),
                    "phase_index": phase_index,
                    "phase_order": int(phase["phase_order"]),
                    "phase_name": str(phase["phase_name"]),
                    "sample_index": sample_index,
                    "pollipi_state": _state_text(decision.state),
                    "pollipi_reason": str(decision.reason),
                    "global_synchrony": float(features.global_synchrony),
                    "active_cell_proportion": float(features.active_cell_proportion),
                    "estimated_global_shift": float(features.estimated_global_shift),
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                rows_written += 1
    if rows_written != 5760:
        raise RuntimeError(f"V13 PolliPi trace row count changed: {rows_written}")
    print("V13_POLLIPI_TRACE PASS", rows_written, hashlib.sha256(output.read_bytes()).hexdigest())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        smoke_test(args.source_root)
        return
    if args.artifact_dir is None or args.output is None:
        parser.error("normal mode requires --artifact-dir and --output")
    run(args.source_root, args.artifact_dir, args.output)


if __name__ == "__main__":
    main()
