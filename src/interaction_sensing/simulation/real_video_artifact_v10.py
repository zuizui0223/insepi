"""Fail-closed reader for the frozen V10 real-pixel artifact.

This module performs integrity validation only. It contains no observer logic and
never infers missing provenance from filenames or array shapes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterator, Mapping

import numpy as np


SCHEMA = "interaction-sensing-v10-real-pixel-artifact-v1"
PROTOCOL_SHA256 = "c84947c998f69d4c8f2d056e79c7f91c6c6736b938236c17386618ac5a924e03"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class V10ConditionRecord:
    condition_index: int
    condition_id: str
    base_index: int
    variant_index: int
    family: str | None
    tier_index: int | None
    intensity: float | None
    known_disturbed: bool


@dataclass(frozen=True, slots=True)
class V10LoadedArtifact:
    backgrounds: np.ndarray
    frames: np.ndarray
    base_registry: tuple[Mapping[str, object], ...]
    variant_registry: tuple[Mapping[str, object], ...]
    condition_registry: tuple[Mapping[str, object], ...]
    panel_registry: tuple[Mapping[str, object], ...]
    receipt: Mapping[str, object]

    def condition(self, condition_index: int) -> tuple[np.ndarray, np.ndarray, V10ConditionRecord]:
        if not 0 <= condition_index < len(self.condition_registry):
            raise IndexError(condition_index)
        row = self.condition_registry[condition_index]
        base_index = int(row["base_index"])
        variant_index = int(row["variant_index"])
        expected = base_index * 19 + variant_index
        if condition_index != expected or int(row["condition_index"]) != expected:
            raise RuntimeError("V10 condition registry ordering is not canonical")
        record = V10ConditionRecord(
            condition_index=condition_index,
            condition_id=str(row["condition_id"]),
            base_index=base_index,
            variant_index=variant_index,
            family=None if row["family"] is None else str(row["family"]),
            tier_index=None if row["tier_index"] is None else int(row["tier_index"]),
            intensity=None if row["intensity"] is None else float(row["intensity"]),
            known_disturbed=bool(row["known_disturbed"]),
        )
        return self.frames[base_index, variant_index], self.backgrounds[base_index], record

    def iter_conditions(self) -> Iterator[tuple[np.ndarray, np.ndarray, V10ConditionRecord]]:
        for index in range(len(self.condition_registry)):
            yield self.condition(index)


def _load_json(path: Path) -> tuple[object, str]:
    payload = path.read_bytes()
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def load_v10_artifact(directory: str | Path) -> V10LoadedArtifact:
    root = Path(directory)
    receipt_path = root / "v10_real_pixel_receipt.json"
    npz_path = root / "v10_real_pixel_artifact.npz"
    base_path = root / "v10_base_windows.json"
    variants_path = root / "v10_variant_registry.json"
    conditions_path = root / "v10_condition_registry.json"
    panels_path = root / "v10_panel_registry.json"
    for path in (receipt_path, npz_path, base_path, variants_path, conditions_path, panels_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    receipt_obj, _receipt_sha = _load_json(receipt_path)
    if not isinstance(receipt_obj, dict) or receipt_obj.get("schema") != SCHEMA:
        raise RuntimeError("unexpected V10 artifact receipt schema")
    receipt = receipt_obj
    if receipt.get("protocol_sha256") != PROTOCOL_SHA256:
        raise RuntimeError("V10 artifact protocol hash differs from frozen V10 protocol")
    if receipt.get("observer_execution") is not False or receipt.get("v7_materialisation") is not False:
        raise RuntimeError("V10 artifact receipt violates pre-observer/non-V7 boundary")

    files = receipt.get("files")
    arrays = receipt.get("array_contract")
    if not isinstance(files, dict) or not isinstance(arrays, dict):
        raise RuntimeError("V10 artifact receipt is missing file/array integrity fields")
    expected_hashes = {
        npz_path: files.get("pixel_npz_sha256"),
        base_path: files.get("base_registry_sha256"),
        variants_path: files.get("variant_registry_sha256"),
        conditions_path: files.get("condition_registry_sha256"),
        panels_path: files.get("panel_registry_sha256"),
    }
    for path, expected in expected_hashes.items():
        if not isinstance(expected, str) or len(expected) != 64:
            raise RuntimeError(f"V10 receipt has invalid expected SHA-256 for {path.name}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"V10 artifact file hash mismatch for {path.name}: {actual} != {expected}")

    base_obj, _ = _load_json(base_path)
    variants_obj, _ = _load_json(variants_path)
    conditions_obj, _ = _load_json(conditions_path)
    panels_obj, _ = _load_json(panels_path)
    if not all(isinstance(value, list) for value in (base_obj, variants_obj, conditions_obj, panels_obj)):
        raise RuntimeError("V10 registries must be JSON arrays")
    if (len(base_obj), len(variants_obj), len(conditions_obj), len(panels_obj)) != (364, 19, 6916, 18):
        raise RuntimeError("V10 registry cardinality differs from frozen protocol")

    with np.load(npz_path, allow_pickle=False) as archive:
        if set(archive.files) != {"backgrounds", "frames"}:
            raise RuntimeError(f"unexpected V10 NPZ members: {archive.files}")
        backgrounds = np.array(archive["backgrounds"], copy=True)
        frames = np.array(archive["frames"], copy=True)
    if backgrounds.shape != (364, 96, 128) or frames.shape != (364, 19, 96, 128):
        raise RuntimeError("V10 array shape differs from frozen protocol")
    if backgrounds.dtype != np.uint8 or frames.dtype != np.uint8:
        raise RuntimeError("V10 arrays must be uint8")
    if hashlib.sha256(backgrounds.tobytes(order="C")).hexdigest() != arrays.get("backgrounds_raw_sha256"):
        raise RuntimeError("V10 backgrounds raw-byte hash mismatch")
    if hashlib.sha256(frames.tobytes(order="C")).hexdigest() != arrays.get("frames_raw_sha256"):
        raise RuntimeError("V10 frames raw-byte hash mismatch")

    for base_index, row in enumerate(base_obj):
        if int(row["base_index"]) != base_index:
            raise RuntimeError("V10 base registry is not in canonical base_index order")
    for variant_index, row in enumerate(variants_obj):
        if int(row["variant_index"]) != variant_index:
            raise RuntimeError("V10 variant registry is not in canonical variant_index order")
    for condition_index, row in enumerate(conditions_obj):
        if int(row["condition_index"]) != condition_index:
            raise RuntimeError("V10 condition registry is not in canonical condition_index order")
    for row in panels_obj:
        disturbed = row.get("disturbed_base_indices")
        if not isinstance(disturbed, list) or len(disturbed) != 182 or len(set(map(int, disturbed))) != 182:
            raise RuntimeError("V10 panel is not the frozen 182/182 balanced assignment")

    return V10LoadedArtifact(
        backgrounds=backgrounds,
        frames=frames,
        base_registry=tuple(base_obj),
        variant_registry=tuple(variants_obj),
        condition_registry=tuple(conditions_obj),
        panel_registry=tuple(panels_obj),
        receipt=receipt,
    )
