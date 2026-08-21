import json
from pathlib import Path

import pytest

from interaction_sensing.simulation.locked_world_v7 import (
    build_registry,
    spec_fingerprint,
    suite_fingerprint,
)
from interaction_sensing.simulation.v7_lock import (
    V7FrozenInputs,
    V7LockError,
    assert_manifest_is_safely_blocked,
    derive_master_seed_hex,
    load_lock_manifest,
    validate_ready_manifest,
)


DUMMY_MASTER_SEED = "ab" * 32
DUMMY_POLLIPI_SHA = "1" * 40
DUMMY_INSEPI_SHA = "2" * 40
DUMMY_ALLOCATOR_SHA = "3" * 40
DUMMY_GENERATOR_SHA = "4" * 40
DUMMY_BASELINE_SHA256 = "5" * 64
DUMMY_WORLD_SPEC_SHA256 = "6" * 64


def test_v7_world_contract_is_seed_locked_and_exactly_180_conditions():
    rows = build_registry(DUMMY_MASTER_SEED)
    assert len(rows) == 180
    assert len({row.condition_id for row in rows}) == 180
    assert {row.true_visit for row in rows} == {False, True}
    assert spec_fingerprint() == "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3"


def test_dummy_world_is_deterministic_but_is_not_a_validation_seed():
    # This uses an explicit test-only seed unrelated to any frozen method SHA.
    first = suite_fingerprint(DUMMY_MASTER_SEED)
    second = suite_fingerprint(DUMMY_MASTER_SEED)
    assert first == second
    assert len(first) == 64


def test_committed_v7_manifest_is_safely_blocked():
    manifest_path = Path("benchmarks/v7_lock_manifest.json")
    manifest = load_lock_manifest(manifest_path)
    blockers = assert_manifest_is_safely_blocked(manifest)
    assert len(blockers) >= 2
    assert "master_seed_hex" not in manifest
    assert "world_fingerprint" not in manifest


def test_blocked_manifest_cannot_validate_or_derive_final_seed():
    manifest = load_lock_manifest("benchmarks/v7_lock_manifest.json")
    with pytest.raises(V7LockError, match="not ready"):
        validate_ready_manifest(
            manifest,
            reachable_shas={},
            current_allocator_sha=DUMMY_ALLOCATOR_SHA,
            current_generator_sha=DUMMY_GENERATOR_SHA,
            expected_world_spec_sha256=DUMMY_WORLD_SPEC_SHA256,
        )


def _dummy_ready_manifest():
    return {
        "schema": "pollipi-insepi-v7-lock-v1",
        "status": "ready",
        "frozen_inputs": {
            "pollipi_method_sha": DUMMY_POLLIPI_SHA,
            "insepi_method_sha": DUMMY_INSEPI_SHA,
            "allocator_sha": DUMMY_ALLOCATOR_SHA,
            "generator_sha": DUMMY_GENERATOR_SHA,
            "baseline_registry_sha256": DUMMY_BASELINE_SHA256,
            "world_spec_sha256": DUMMY_WORLD_SPEC_SHA256,
        },
        "weights": {
            "exploration": 0.5,
            "pollipi": 0.1,
            "insepi": 0.4,
            "disagreement": 0.0,
        },
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


def test_ready_validation_requires_external_reachability_and_exact_freeze_ids():
    manifest = _dummy_ready_manifest()
    with pytest.raises(V7LockError, match="PolliPi"):
        validate_ready_manifest(
            manifest,
            reachable_shas={},
            current_allocator_sha=DUMMY_ALLOCATOR_SHA,
            current_generator_sha=DUMMY_GENERATOR_SHA,
            expected_world_spec_sha256=DUMMY_WORLD_SPEC_SHA256,
        )

    frozen = validate_ready_manifest(
        manifest,
        reachable_shas={
            "pollipi_method_sha": DUMMY_POLLIPI_SHA,
            "insepi_method_sha": DUMMY_INSEPI_SHA,
        },
        current_allocator_sha=DUMMY_ALLOCATOR_SHA,
        current_generator_sha=DUMMY_GENERATOR_SHA,
        expected_world_spec_sha256=DUMMY_WORLD_SPEC_SHA256,
    )
    assert frozen.pollipi_method_sha == DUMMY_POLLIPI_SHA
    assert frozen.insepi_method_sha == DUMMY_INSEPI_SHA


def test_seed_derivation_is_deterministic_only_after_validated_inputs_exist():
    frozen = V7FrozenInputs(
        pollipi_method_sha=DUMMY_POLLIPI_SHA,
        insepi_method_sha=DUMMY_INSEPI_SHA,
        allocator_sha=DUMMY_ALLOCATOR_SHA,
        generator_sha=DUMMY_GENERATOR_SHA,
        baseline_registry_sha256=DUMMY_BASELINE_SHA256,
        world_spec_sha256=DUMMY_WORLD_SPEC_SHA256,
    )
    seed_a = derive_master_seed_hex(frozen)
    seed_b = derive_master_seed_hex(frozen)
    assert seed_a == seed_b
    assert len(seed_a) == 64
