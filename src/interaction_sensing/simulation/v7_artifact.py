"""Canonical pixel artifact contract for one-shot V7 validation.

The final world is rendered once, after lock release, then both observers consume
the same immutable NPZ bytes.  Observer decisions receive only image arrays;
latent truth remains metadata for post-decision scoring.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np

from interaction_sensing.simulation.locked_world_v7 import (
    build_registry,
    render_condition,
    spec_fingerprint,
    suite_fingerprint,
)

ARTIFACT_SCHEMA = "pollipi-insepi-v7-pixel-artifact-v1"


@dataclass(frozen=True, slots=True)
class V7ArtifactManifest:
    schema: str
    world_spec_sha256: str
    world_fingerprint: str
    condition_count: int
    shape: tuple[int, int]
    npz_sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_world_artifact(
    npz_path: str | Path,
    manifest_path: str | Path,
    *,
    master_seed_hex: str,
) -> V7ArtifactManifest:
    """Materialise a canonical V7 artifact from an already-unlocked seed.

    This function has no default seed and must never be called by ordinary CI.
    """

    conditions = build_registry(master_seed_hex)
    backgrounds: list[np.ndarray] = []
    frames: list[np.ndarray] = []
    metadata: list[dict[str, object]] = []
    for condition in conditions:
        background, frame = render_condition(condition)
        backgrounds.append(background)
        frames.append(frame)
        metadata.append(asdict(condition))

    output = Path(npz_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    np.savez_compressed(
        output,
        backgrounds=np.stack(backgrounds).astype(np.uint8),
        frames=np.stack(frames).astype(np.uint8),
        metadata_json=np.array(metadata_json),
    )

    manifest = V7ArtifactManifest(
        schema=ARTIFACT_SCHEMA,
        world_spec_sha256=spec_fingerprint(),
        world_fingerprint=suite_fingerprint(master_seed_hex),
        condition_count=len(conditions),
        shape=tuple(int(v) for v in backgrounds[0].shape),
        npz_sha256=_sha256_file(output),
    )
    manifest_output = Path(manifest_path)
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_world_artifact(
    npz_path: str | Path,
    manifest_path: str | Path,
) -> tuple[V7ArtifactManifest, np.ndarray, np.ndarray, list[dict[str, object]]]:
    """Read and fully verify a canonical artifact before observer inference."""

    npz_file = Path(npz_path)
    manifest_raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest_raw.get("schema") != ARTIFACT_SCHEMA:
        raise ValueError("unexpected V7 pixel artifact schema")
    manifest = V7ArtifactManifest(
        schema=str(manifest_raw["schema"]),
        world_spec_sha256=str(manifest_raw["world_spec_sha256"]),
        world_fingerprint=str(manifest_raw["world_fingerprint"]),
        condition_count=int(manifest_raw["condition_count"]),
        shape=tuple(int(v) for v in manifest_raw["shape"]),
        npz_sha256=str(manifest_raw["npz_sha256"]),
    )
    if _sha256_file(npz_file) != manifest.npz_sha256:
        raise ValueError("V7 pixel artifact SHA-256 mismatch")
    if manifest.world_spec_sha256 != spec_fingerprint():
        raise ValueError("V7 pixel artifact world-spec mismatch")

    with np.load(npz_file, allow_pickle=False) as payload:
        backgrounds = payload["backgrounds"].astype(np.uint8)
        frames = payload["frames"].astype(np.uint8)
        metadata_json = str(payload["metadata_json"].item())
    metadata = json.loads(metadata_json)

    if backgrounds.shape != frames.shape:
        raise ValueError("V7 background/frame tensor shapes differ")
    if backgrounds.ndim != 3:
        raise ValueError("V7 pixel arrays must be [condition,height,width]")
    if backgrounds.shape[0] != manifest.condition_count:
        raise ValueError("V7 condition count differs from manifest")
    if tuple(backgrounds.shape[1:]) != manifest.shape:
        raise ValueError("V7 pixel shape differs from manifest")
    if len(metadata) != manifest.condition_count:
        raise ValueError("V7 metadata count differs from manifest")
    ids = [str(row["condition_id"]) for row in metadata]
    if len(ids) != len(set(ids)):
        raise ValueError("V7 condition IDs are not unique")
    return manifest, backgrounds, frames, metadata
