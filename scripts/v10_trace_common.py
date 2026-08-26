#!/usr/bin/env python3
"""Shared fail-closed utilities for V10 frozen-observer trace runners.

This module intentionally does not import ``interaction_sensing``.  The exact
frozen InsePi checkout uses that same package name, so importing the current
package before the frozen checkout would risk module-cache contamination.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Mapping

import numpy as np

POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"
PIXEL_SHA256 = "b971caa2b0c06b45ccf114df99d6515765ea9ec5fb8e58ded226b424f8afad66"
CONDITION_REGISTRY_SHA256 = "1689f5ce102abfef722e3e8667e8c6e290a42fe1d4563c1655b7f14520cde393"
RECEIPT_SHA256 = "59fab9a0a503f7302d0f1c6c227850e94eef8d780eda9786f66f090c164bedeb"
CONDITION_COUNT = 6916


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_exact_checkout(source_root: Path, expected_commit: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = completed.stdout.strip()
    if actual != expected_commit:
        raise RuntimeError(f"frozen checkout mismatch: {actual} != {expected_commit}")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_trace_pixels(artifact_dir: Path, freeze_path: Path):
    """Return pixels plus condition id/index only; no truth metadata is returned."""
    freeze = _read_json(freeze_path)
    if not isinstance(freeze, Mapping):
        raise RuntimeError("V10 pixel freeze must be a JSON object")
    artifact = freeze.get("artifact")
    cardinality = freeze.get("cardinality")
    if not isinstance(artifact, Mapping) or not isinstance(cardinality, Mapping):
        raise RuntimeError("V10 pixel freeze lacks artifact/cardinality contracts")
    if artifact.get("pixel_npz_sha256") != PIXEL_SHA256:
        raise RuntimeError("V10 frozen pixel SHA constant differs from freeze file")
    if artifact.get("condition_registry_sha256") != CONDITION_REGISTRY_SHA256:
        raise RuntimeError("V10 frozen condition-registry SHA differs from freeze file")
    if artifact.get("receipt_sha256") != RECEIPT_SHA256:
        raise RuntimeError("V10 frozen receipt SHA differs from freeze file")
    if int(cardinality.get("conditions", -1)) != CONDITION_COUNT:
        raise RuntimeError("V10 frozen condition count differs from runner contract")

    npz_path = artifact_dir / "v10_real_pixel_artifact.npz"
    receipt_path = artifact_dir / "v10_real_pixel_receipt.json"
    condition_path = artifact_dir / "v10_condition_registry.json"
    for path in (npz_path, receipt_path, condition_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    if sha256_file(npz_path) != PIXEL_SHA256:
        raise RuntimeError("V10 pixel NPZ does not match frozen SHA-256")
    if sha256_file(receipt_path) != RECEIPT_SHA256:
        raise RuntimeError("V10 pixel receipt does not match frozen SHA-256")
    if sha256_file(condition_path) != CONDITION_REGISTRY_SHA256:
        raise RuntimeError("V10 condition registry does not match frozen SHA-256")

    receipt = _read_json(receipt_path)
    conditions = _read_json(condition_path)
    if not isinstance(receipt, Mapping) or receipt.get("observer_execution") is not False:
        raise RuntimeError("V10 receipt violates pre-observer boundary")
    if not isinstance(conditions, list) or len(conditions) != CONDITION_COUNT:
        raise RuntimeError("V10 condition registry cardinality mismatch")
    condition_keys: list[tuple[int, str]] = []
    for expected_index, row in enumerate(conditions):
        if not isinstance(row, Mapping):
            raise RuntimeError("V10 condition row must be an object")
        index = int(row["condition_index"])
        if index != expected_index:
            raise RuntimeError("V10 condition registry ordering changed")
        condition_keys.append((index, str(row["condition_id"])))

    with np.load(npz_path, allow_pickle=False) as archive:
        if set(archive.files) != {"backgrounds", "frames"}:
            raise RuntimeError("unexpected V10 NPZ members")
        backgrounds = np.array(archive["backgrounds"], copy=True)
        frames = np.array(archive["frames"], copy=True)
    if backgrounds.shape != (364, 96, 128) or frames.shape != (364, 19, 96, 128):
        raise RuntimeError("V10 frozen pixel tensor shape changed")
    if backgrounds.dtype != np.uint8 or frames.dtype != np.uint8:
        raise RuntimeError("V10 frozen pixel tensors must be uint8")
    return backgrounds, frames, tuple(condition_keys)


def pixels_for_condition(
    backgrounds: np.ndarray,
    frames: np.ndarray,
    condition_index: int,
) -> tuple[np.ndarray, np.ndarray]:
    base_index, variant_index = divmod(int(condition_index), 19)
    if not (0 <= base_index < 364 and 0 <= variant_index < 19):
        raise IndexError(condition_index)
    return frames[base_index, variant_index], backgrounds[base_index]


def provenance(schema: str, source_commit: str) -> dict[str, object]:
    return {
        "record_type": "provenance",
        "schema": schema,
        "source_commit": source_commit,
        "pixel_artifact_sha256": PIXEL_SHA256,
        "condition_registry_sha256": CONDITION_REGISTRY_SHA256,
        "condition_count": CONDITION_COUNT,
    }
