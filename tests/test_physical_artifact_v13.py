from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from interaction_sensing import physical_artifact_v13 as artifact


def _write_small_plan(path: Path, block_count: int = 2) -> None:
    rows = []
    for block in range(block_count):
        block_id = f"b{block:02d}"
        split = "development" if block == 0 else "heldout"
        phases = ("placebo", "shared_restore", "event_restore", "observability_restore")
        for order, phase in enumerate(phases):
            rows.append({
                "opaque_block_id": block_id,
                "split": split,
                "phase_name": phase,
                "phase_order": order,
                "clip_key": f"{block_id}__p{order}_{phase}.mp4",
            })
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["opaque_block_id", "split", "phase_name", "phase_order", "clip_key"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def test_v13_canonical_registry_contains_safe_metadata_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(artifact, "BLOCK_COUNT", 2)
    plan = tmp_path / "plan.csv"
    _write_small_plan(plan)
    rows = artifact.read_observer_plan(plan)
    registry = artifact.canonical_registry(rows)
    assert len(registry) == 8
    forbidden = {"treatment_class", "treatment_subtype", "day_id", "scene_id"}
    assert all(not (set(row) & forbidden) for row in registry)
    assert [row["opaque_block_id"] for row in registry[:4]] == ["b00"] * 4
    assert registry[0]["phase_name"] == "placebo"


def test_v13_materializer_uses_only_placebo_frames_for_background(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(artifact, "BLOCK_COUNT", 2)
    plan = tmp_path / "plan.csv"
    _write_small_plan(plan)

    def fake_canonicalize(frames):
        return tuple(np.asarray(frame, dtype=np.uint8) for frame in frames)

    monkeypatch.setattr(artifact, "canonicalize_sampled_rgb24", fake_canonicalize)

    def loader(clip_key: str):
        # Placebo uses small values. Active phases use much larger values; if
        # they leak into the background the assertion below changes.
        base = 10 if "placebo" in clip_key else 200
        frames = [np.full((96, 128), base + index, dtype=np.uint8) for index in range(8)]
        return frames, hashlib.sha256(clip_key.encode()).hexdigest()

    out = tmp_path / "artifact"
    receipt = artifact.materialise_pixel_artifact(
        plan,
        out,
        phase_loader=loader,
        decoder_identity={"test": True},
    )
    loaded = artifact.load_pixel_artifact(out)
    assert loaded.frames.shape == (2, 4, 8, 96, 128)
    assert loaded.backgrounds.shape == (2, 96, 128)
    # placebo values 10..17 -> central pair 13/14 -> half-up 14.
    assert np.all(loaded.backgrounds == 14)
    assert receipt["truth_metadata_present"] is False
    assert len(loaded.registry) == 8


def test_v13_npy_artifact_is_byte_deterministic_for_same_safe_inputs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(artifact, "BLOCK_COUNT", 2)
    plan = tmp_path / "plan.csv"
    _write_small_plan(plan)
    monkeypatch.setattr(
        artifact,
        "canonicalize_sampled_rgb24",
        lambda frames: tuple(np.asarray(frame, dtype=np.uint8) for frame in frames),
    )

    def loader(clip_key: str):
        value = int(hashlib.sha256(clip_key.encode()).hexdigest()[:2], 16)
        frames = [np.full((96, 128), (value + index) % 256, dtype=np.uint8) for index in range(8)]
        return frames, hashlib.sha256(("clip|" + clip_key).encode()).hexdigest()

    a = tmp_path / "a"
    b = tmp_path / "b"
    artifact.materialise_pixel_artifact(plan, a, phase_loader=loader, decoder_identity={"id": 1})
    artifact.materialise_pixel_artifact(plan, b, phase_loader=loader, decoder_identity={"id": 1})
    for name in ("v13_frames.npy", "v13_backgrounds.npy", "v13_safe_registry.json", "v13_pixel_receipt.json"):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_v13_artifact_loader_rejects_byte_tamper(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(artifact, "BLOCK_COUNT", 2)
    plan = tmp_path / "plan.csv"
    _write_small_plan(plan)
    monkeypatch.setattr(
        artifact,
        "canonicalize_sampled_rgb24",
        lambda frames: tuple(np.asarray(frame, dtype=np.uint8) for frame in frames),
    )

    def loader(clip_key: str):
        frames = [np.zeros((96, 128), dtype=np.uint8) for _ in range(8)]
        return frames, hashlib.sha256(clip_key.encode()).hexdigest()

    out = tmp_path / "artifact"
    artifact.materialise_pixel_artifact(plan, out, phase_loader=loader, decoder_identity={})
    path = out / "v13_safe_registry.json"
    path.write_text(path.read_text() + " ", encoding="utf-8")
    with pytest.raises(RuntimeError, match="safe registry hash mismatch"):
        artifact.load_pixel_artifact(out)


def test_v13_safe_registry_rejects_missing_placebo_or_active_phase(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(artifact, "BLOCK_COUNT", 1)
    plan = tmp_path / "bad.csv"
    with plan.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["opaque_block_id", "split", "phase_name", "phase_order", "clip_key"],
            lineterminator="\n",
        )
        writer.writeheader()
        for order, phase in enumerate(("placebo", "event_restore", "observability_restore", "observability_restore")):
            writer.writerow({
                "opaque_block_id": "b00",
                "split": "development",
                "phase_name": phase,
                "phase_order": order,
                "clip_key": f"p{order}.mp4",
            })
    rows = artifact.read_observer_plan(plan)
    with pytest.raises(RuntimeError, match="active intervention set"):
        artifact.canonical_registry(rows)
