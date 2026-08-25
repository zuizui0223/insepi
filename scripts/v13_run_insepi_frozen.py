#!/usr/bin/env python3
"""Run exact frozen InsePi on the truth-free V13 canonical pixel artifact."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

from interaction_sensing.physical_artifact_v13 import load_pixel_artifact, sha256_file

INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"
TRACE_SCHEMA = "pollipi-insepi-v13-insepi-phase-trace-v1"
BOOKKEEPING_FRAME_INDEX = 0


def verify_exact_checkout(root: Path) -> None:
    actual = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != INSEPI_COMMIT:
        raise RuntimeError(f"InsePi frozen checkout mismatch: {actual} != {INSEPI_COMMIT}")


def _purge(prefix: str) -> None:
    for name in tuple(sys.modules):
        if name == prefix or name.startswith(prefix + "."):
            del sys.modules[name]


def _require_under(module, root: Path, label: str) -> None:
    path = Path(str(module.__file__)).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} imported outside exact frozen checkout: {path}") from exc


def components(source_root: Path):
    src = (source_root / "src").resolve()
    if not src.is_dir():
        raise FileNotFoundError(src)
    _purge("interaction_sensing")
    sys.path.insert(0, str(src))
    package = importlib.import_module("interaction_sensing")
    noise = importlib.import_module("interaction_sensing.noise")
    factorial = importlib.import_module("interaction_sensing.simulation.factorial_benchmark_v4")
    visual = importlib.import_module("interaction_sensing.simulation.visual_contradiction_v2")
    for module, label in (
        (package, "interaction_sensing"),
        (noise, "interaction_sensing.noise"),
        (factorial, "factorial_benchmark_v4"),
        (visual, "visual_contradiction_v2"),
    ):
        _require_under(module, src, label)
    policy = noise.NoiseFirstPolicy()
    threshold = float(factorial.calibrate_occlusion_threshold())
    return (
        policy,
        threshold,
        visual.infer_noise_observation,
        factorial.local_structure_loss,
        factorial._apply_calibrated_local_audit,
    )


def _decision_tuple(source_root: Path, background: np.ndarray, frame: np.ndarray, frame_index: int):
    policy, threshold, infer, local_loss, apply_audit = components(source_root)
    observation = infer(background, frame, frame_index)
    structure_loss = float(local_loss(background, frame, observation))
    observation = apply_audit(observation, structure_loss, threshold)
    decision = policy.decide(observation)
    return (
        str(observation.source.value),
        str(decision.state.value),
        float(decision.false_event_risk),
        float(decision.missed_event_risk),
        float(decision.attribution_risk),
        structure_loss,
        threshold,
    )


def smoke_test(source_root: Path) -> None:
    verify_exact_checkout(source_root)
    yy, xx = np.mgrid[:96, :128]
    background = np.clip(95 + 9 * np.sin(xx * 0.08) + 7 * np.cos(yy * 0.12), 0, 255).astype(np.uint8)
    frame = background.copy()
    frame[:, 45:82] = np.clip(frame[:, 45:82].astype(np.int16) - 30, 0, 255).astype(np.uint8)
    outputs = [
        _decision_tuple(source_root, background, frame, index)
        for index in (0, 1, 5759)
    ]
    if not (outputs[0] == outputs[1] == outputs[2]):
        raise RuntimeError("V13 exact InsePi decision depends on bookkeeping frame index")
    print("V13_INSEPI_FROZEN_SMOKE PASS", outputs[0][0], outputs[0][1])
    print("V13_INSEPI_FRAME_INDEX_INVARIANCE PASS 0 1 5759")


def run(source_root: Path, artifact_dir: Path, output: Path) -> None:
    verify_exact_checkout(source_root)
    # Load the current truth-free artifact before replacing the current package
    # namespace with the exact frozen InsePi checkout.
    artifact = load_pixel_artifact(artifact_dir)
    policy, threshold, infer, local_loss, apply_audit = components(source_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    provenance = {
        "record_type": "provenance",
        "schema": TRACE_SCHEMA,
        "source_commit": INSEPI_COMMIT,
        "pixel_receipt_sha256": sha256_file(artifact_dir / "v13_pixel_receipt.json"),
        "frames_raw_sha256": artifact.receipt["array_contract"]["frames_raw_sha256"],
        "backgrounds_raw_sha256": artifact.receipt["array_contract"]["backgrounds_raw_sha256"],
        "result_row_count": 180 * 4 * 8,
        "bookkeeping_frame_index": BOOKKEEPING_FRAME_INDEX,
        "occlusion_threshold": threshold,
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
                observation = infer(background, frame, BOOKKEEPING_FRAME_INDEX)
                structure_loss = float(local_loss(background, frame, observation))
                observation = apply_audit(observation, structure_loss, threshold)
                decision = policy.decide(observation)
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
                    "inferred_noise_source": str(observation.source.value),
                    "observability_state": str(decision.state.value),
                    "false_event_risk": float(decision.false_event_risk),
                    "missed_event_risk": float(decision.missed_event_risk),
                    "attribution_risk": float(decision.attribution_risk),
                    "local_structure_loss": structure_loss,
                    "occlusion_threshold": threshold,
                }
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                rows_written += 1
    if rows_written != 5760:
        raise RuntimeError(f"V13 InsePi trace row count changed: {rows_written}")
    print("V13_INSEPI_TRACE PASS", rows_written, sha256_file(output))


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
