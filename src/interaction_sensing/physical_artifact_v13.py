"""Truth-free V13 physical pixel artifact utilities.

The artifact is built only from the observer-safe phase plan and phase video
bytes.  Latent treatment class/subtype is not part of the registry.  Pixel
arrays are stored as deterministic ``.npy`` files rather than a ZIP container.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np

from interaction_sensing.physical_measurement_v13 import (
    SAMPLE_NATIVE_FRAME_INDICES,
    canonicalize_sampled_rgb24,
    placebo_background,
)

SCHEMA = "interaction-sensing-v13-physical-pixel-artifact-v1"
PHASE_NAMES = ("placebo", "event_restore", "observability_restore", "shared_restore")
BLOCK_COUNT = 180
PHASE_COUNT = 4
SAMPLE_COUNT = 8


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def raw_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(array).tobytes(order="C")).hexdigest()


def read_observer_plan(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        expected = ["opaque_block_id", "split", "phase_name", "phase_order", "clip_key"]
        if list(reader.fieldnames or []) != expected:
            raise RuntimeError(f"V13 observer plan columns changed: {reader.fieldnames}")
        rows = tuple(dict(row) for row in reader)
    if len(rows) != BLOCK_COUNT * PHASE_COUNT:
        raise RuntimeError(f"V13 observer plan must contain 720 phase rows, got {len(rows)}")
    return rows


def canonical_registry(plan_rows: Sequence[Mapping[str, str]]) -> tuple[dict[str, object], ...]:
    grouped: dict[str, list[Mapping[str, str]]] = {}
    for row in plan_rows:
        grouped.setdefault(str(row["opaque_block_id"]), []).append(row)
    if len(grouped) != BLOCK_COUNT:
        raise RuntimeError(f"V13 requires exactly 180 opaque blocks, got {len(grouped)}")

    registry: list[dict[str, object]] = []
    for block_index, block_id in enumerate(sorted(grouped)):
        phases = sorted(grouped[block_id], key=lambda row: int(row["phase_order"]))
        if len(phases) != PHASE_COUNT:
            raise RuntimeError(f"V13 block {block_id} does not have exactly four phases")
        if [int(row["phase_order"]) for row in phases] != [0, 1, 2, 3]:
            raise RuntimeError(f"V13 phase-order contract changed for {block_id}")
        if phases[0]["phase_name"] != "placebo":
            raise RuntimeError(f"V13 placebo is not phase zero for {block_id}")
        active = {str(row["phase_name"]) for row in phases[1:]}
        if active != set(PHASE_NAMES[1:]):
            raise RuntimeError(f"V13 active intervention set changed for {block_id}: {active}")
        split = str(phases[0]["split"])
        if split not in {"development", "heldout"}:
            raise RuntimeError(f"V13 split changed for {block_id}: {split}")
        if any(str(row["split"]) != split for row in phases):
            raise RuntimeError(f"V13 block split differs across phases: {block_id}")
        for phase_index, row in enumerate(phases):
            registry.append({
                "block_index": block_index,
                "opaque_block_id": block_id,
                "split": split,
                "phase_index": phase_index,
                "phase_order": int(row["phase_order"]),
                "phase_name": str(row["phase_name"]),
                "clip_key": str(row["clip_key"]),
            })
    return tuple(registry)


@dataclass(frozen=True, slots=True)
class V13PixelArtifact:
    frames: np.ndarray
    backgrounds: np.ndarray
    registry: tuple[Mapping[str, object], ...]
    receipt: Mapping[str, object]


def materialise_pixel_artifact(
    observer_plan_path: Path,
    output_dir: Path,
    *,
    phase_loader: Callable[[str], tuple[Sequence[np.ndarray], str]],
    decoder_identity: Mapping[str, object],
) -> Mapping[str, object]:
    """Build canonical pixels from safe plan rows via an injected RGB frame loader.

    ``phase_loader(clip_key)`` must return exactly eight native 1920x1080 RGB24
    frames and the SHA-256 of the source clip bytes.  It receives no treatment
    truth because ``clip_key`` comes from the safe observer plan only.
    """
    plan_rows = read_observer_plan(observer_plan_path)
    registry = canonical_registry(plan_rows)
    frames = np.empty((BLOCK_COUNT, PHASE_COUNT, SAMPLE_COUNT, 96, 128), dtype=np.uint8)
    backgrounds = np.empty((BLOCK_COUNT, 96, 128), dtype=np.uint8)
    safe_registry: list[dict[str, object]] = []

    by_block: dict[int, list[Mapping[str, object]]] = {}
    for row in registry:
        by_block.setdefault(int(row["block_index"]), []).append(row)

    for block_index in range(BLOCK_COUNT):
        rows = sorted(by_block[block_index], key=lambda row: int(row["phase_index"]))
        placebo_rgb, placebo_clip_sha = phase_loader(str(rows[0]["clip_key"]))
        placebo = canonicalize_sampled_rgb24(placebo_rgb)
        for sample_index, frame in enumerate(placebo):
            frames[block_index, 0, sample_index] = frame
        backgrounds[block_index] = placebo_background(placebo)
        safe_registry.append({**rows[0], "clip_sha256": placebo_clip_sha})

        for phase_index in range(1, PHASE_COUNT):
            rgb_frames, clip_sha = phase_loader(str(rows[phase_index]["clip_key"]))
            canonical = canonicalize_sampled_rgb24(rgb_frames)
            for sample_index, frame in enumerate(canonical):
                frames[block_index, phase_index, sample_index] = frame
            safe_registry.append({**rows[phase_index], "clip_sha256": clip_sha})

    output_dir.mkdir(parents=True, exist_ok=True)
    frames_path = output_dir / "v13_frames.npy"
    backgrounds_path = output_dir / "v13_backgrounds.npy"
    registry_path = output_dir / "v13_safe_registry.json"
    receipt_path = output_dir / "v13_pixel_receipt.json"
    np.save(frames_path, frames, allow_pickle=False)
    np.save(backgrounds_path, backgrounds, allow_pickle=False)
    registry_path.write_text(json.dumps(safe_registry, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    receipt = {
        "schema": SCHEMA,
        "observer_execution": False,
        "truth_metadata_present": False,
        "observer_plan_sha256": sha256_file(observer_plan_path),
        "decoder_identity": dict(decoder_identity),
        "sample_native_frame_indices": list(SAMPLE_NATIVE_FRAME_INDICES),
        "array_contract": {
            "frames_shape": list(frames.shape),
            "backgrounds_shape": list(backgrounds.shape),
            "dtype": "uint8",
            "frames_raw_sha256": raw_sha256(frames),
            "backgrounds_raw_sha256": raw_sha256(backgrounds),
        },
        "files": {
            "frames_npy_sha256": sha256_file(frames_path),
            "backgrounds_npy_sha256": sha256_file(backgrounds_path),
            "safe_registry_sha256": sha256_file(registry_path),
        },
        "block_count": BLOCK_COUNT,
        "phase_count_per_block": PHASE_COUNT,
        "sample_count_per_phase": SAMPLE_COUNT,
    }
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def load_pixel_artifact(directory: Path) -> V13PixelArtifact:
    receipt_path = directory / "v13_pixel_receipt.json"
    frames_path = directory / "v13_frames.npy"
    backgrounds_path = directory / "v13_backgrounds.npy"
    registry_path = directory / "v13_safe_registry.json"
    for path in (receipt_path, frames_path, backgrounds_path, registry_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != SCHEMA or receipt.get("truth_metadata_present") is not False:
        raise RuntimeError("V13 pixel receipt violates truth-free artifact contract")
    if sha256_file(frames_path) != receipt["files"]["frames_npy_sha256"]:
        raise RuntimeError("V13 frames file hash mismatch")
    if sha256_file(backgrounds_path) != receipt["files"]["backgrounds_npy_sha256"]:
        raise RuntimeError("V13 backgrounds file hash mismatch")
    if sha256_file(registry_path) != receipt["files"]["safe_registry_sha256"]:
        raise RuntimeError("V13 safe registry hash mismatch")
    frames = np.load(frames_path, allow_pickle=False)
    backgrounds = np.load(backgrounds_path, allow_pickle=False)
    if frames.shape != (180, 4, 8, 96, 128) or backgrounds.shape != (180, 96, 128):
        raise RuntimeError("V13 pixel array shape mismatch")
    if frames.dtype != np.uint8 or backgrounds.dtype != np.uint8:
        raise RuntimeError("V13 pixel arrays must be uint8")
    if raw_sha256(frames) != receipt["array_contract"]["frames_raw_sha256"]:
        raise RuntimeError("V13 frames raw-byte hash mismatch")
    if raw_sha256(backgrounds) != receipt["array_contract"]["backgrounds_raw_sha256"]:
        raise RuntimeError("V13 backgrounds raw-byte hash mismatch")
    registry_obj = json.loads(registry_path.read_text(encoding="utf-8"))
    if not isinstance(registry_obj, list) or len(registry_obj) != 720:
        raise RuntimeError("V13 safe registry cardinality mismatch")
    return V13PixelArtifact(frames, backgrounds, tuple(registry_obj), receipt)
