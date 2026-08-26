import json

import pytest

from interaction_sensing.simulation.v7_materialization import materialise_locked_v7


ALLOCATOR_SHA = "a8ac75991ab28fd74a3f3a5482304a2b127a97bc"
GENERATOR_SHA = "1c4c5ffc214ebdfb71ddabe170a071352acd4879"
BASELINE_SHA = "94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975"
WORLD_SPEC_SHA = "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3"
DUMMY_POLLIPI = "1" * 40
DUMMY_INSEPI = "2" * 40


def test_committed_blocked_lock_cannot_materialise_v7(tmp_path):
    with pytest.raises(RuntimeError, match="not ready"):
        materialise_locked_v7(
            lock_manifest_path="benchmarks/v7_lock_manifest.json",
            baseline_registry_path="benchmarks/v7_baseline_registry.json",
            npz_path=tmp_path / "v7.npz",
            artifact_manifest_path=tmp_path / "v7-artifact.json",
            receipt_path=tmp_path / "v7-receipt.json",
            reachable_shas={},
            current_allocator_sha=ALLOCATOR_SHA,
            current_generator_sha=GENERATOR_SHA,
        )
    assert not (tmp_path / "v7.npz").exists()


def _write_dummy_ready_lock(path):
    payload = {
        "schema": "pollipi-insepi-v7-lock-v1",
        "status": "ready",
        "frozen_inputs": {
            "pollipi_method_sha": DUMMY_POLLIPI,
            "insepi_method_sha": DUMMY_INSEPI,
            "allocator_sha": ALLOCATOR_SHA,
            "generator_sha": GENERATOR_SHA,
            "baseline_registry_sha256": BASELINE_SHA,
            "world_spec_sha256": WORLD_SPEC_SHA,
        },
        "weights": {"exploration": 0.5, "pollipi": 0.1, "insepi": 0.4, "disagreement": 0.0},
        "prevalences": [0.1, 0.5, 0.9],
        "budgets": [0.1, 0.25, 0.5],
        "world_windows": 4800,
        "replicates": 200,
        "pass_rules": {
            "joint_ratio_floor": 0.98,
            "mean_joint_ratio_strictly_above": 1.0,
            "max_tv": 0.25,
            "legacy_tolerance": 0.01,
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_dummy_ready_lock_materialises_one_deterministic_receipt_and_refuses_overwrite(tmp_path):
    lock = tmp_path / "dummy-lock.json"
    _write_dummy_ready_lock(lock)
    kwargs = dict(
        lock_manifest_path=lock,
        baseline_registry_path="benchmarks/v7_baseline_registry.json",
        npz_path=tmp_path / "v7.npz",
        artifact_manifest_path=tmp_path / "v7-artifact.json",
        receipt_path=tmp_path / "v7-receipt.json",
        reachable_shas={
            "pollipi_method_sha": DUMMY_POLLIPI,
            "insepi_method_sha": DUMMY_INSEPI,
        },
        current_allocator_sha=ALLOCATOR_SHA,
        current_generator_sha=GENERATOR_SHA,
    )
    receipt = materialise_locked_v7(**kwargs)
    assert receipt["condition_count"] == 180
    assert len(receipt["master_seed_hex"]) == 64
    assert len(receipt["world_fingerprint"]) == 64
    assert len(receipt["receipt_sha256"]) == 64

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        materialise_locked_v7(**kwargs)
