import json

import numpy as np
import pytest

from interaction_sensing.simulation.v7_artifact import (
    read_world_artifact,
    write_world_artifact,
)


DUMMY_MASTER_SEED = "cd" * 32


def test_dummy_v7_artifact_round_trip(tmp_path):
    npz = tmp_path / "dummy-v7.npz"
    manifest_path = tmp_path / "dummy-v7.json"
    written = write_world_artifact(npz, manifest_path, master_seed_hex=DUMMY_MASTER_SEED)
    loaded, backgrounds, frames, metadata = read_world_artifact(npz, manifest_path)

    assert loaded == written
    assert backgrounds.shape == (180, 96, 128)
    assert frames.shape == backgrounds.shape
    assert backgrounds.dtype == np.uint8
    assert frames.dtype == np.uint8
    assert len(metadata) == 180
    assert len({row["condition_id"] for row in metadata}) == 180


def test_artifact_hash_tampering_is_rejected(tmp_path):
    npz = tmp_path / "dummy-v7.npz"
    manifest_path = tmp_path / "dummy-v7.json"
    write_world_artifact(npz, manifest_path, master_seed_hex=DUMMY_MASTER_SEED)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["npz_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        read_world_artifact(npz, manifest_path)
