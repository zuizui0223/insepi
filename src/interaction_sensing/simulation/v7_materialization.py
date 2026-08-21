"""Fail-closed materialisation step for locked V7 validation.

This is the only layer allowed to derive the final master seed.  It first validates
an externally verified ready lock, then writes one canonical pixel artifact and a
provenance receipt.  With the currently committed blocked manifest this function
raises before seed derivation or pixel generation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from interaction_sensing.simulation.locked_world_v7 import spec_fingerprint
from interaction_sensing.simulation.v7_artifact import write_world_artifact
from interaction_sensing.simulation.v7_evaluator import load_baseline_registry
from interaction_sensing.simulation.v7_lock import (
    derive_master_seed_hex,
    load_lock_manifest,
    validate_ready_manifest,
)


RECEIPT_SCHEMA = "pollipi-insepi-v7-materialisation-receipt-v1"


def _canonical_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


def materialise_locked_v7(
    *,
    lock_manifest_path: str | Path,
    baseline_registry_path: str | Path,
    npz_path: str | Path,
    artifact_manifest_path: str | Path,
    receipt_path: str | Path,
    reachable_shas: Mapping[str, str],
    current_allocator_sha: str,
    current_generator_sha: str,
) -> dict[str, object]:
    """Validate the complete lock then deterministically materialise V7 once."""

    outputs = [Path(npz_path), Path(artifact_manifest_path), Path(receipt_path)]
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite V7 materialisation outputs: {existing}")

    lock = load_lock_manifest(lock_manifest_path)
    baseline_registry = load_baseline_registry(baseline_registry_path)
    frozen = validate_ready_manifest(
        lock,
        reachable_shas=reachable_shas,
        current_allocator_sha=current_allocator_sha,
        current_generator_sha=current_generator_sha,
        expected_world_spec_sha256=spec_fingerprint(),
    )
    if baseline_registry["registry_sha256"] != frozen.baseline_registry_sha256:
        raise ValueError("baseline registry does not match the validated V7 lock")

    # This line is intentionally unreachable while the committed lock is blocked.
    master_seed_hex = derive_master_seed_hex(frozen)
    artifact = write_world_artifact(
        npz_path,
        artifact_manifest_path,
        master_seed_hex=master_seed_hex,
    )
    receipt: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "frozen_inputs": {
            "pollipi_method_sha": frozen.pollipi_method_sha,
            "insepi_method_sha": frozen.insepi_method_sha,
            "allocator_sha": frozen.allocator_sha,
            "generator_sha": frozen.generator_sha,
            "baseline_registry_sha256": frozen.baseline_registry_sha256,
            "world_spec_sha256": frozen.world_spec_sha256,
        },
        "master_seed_hex": master_seed_hex,
        "world_fingerprint": artifact.world_fingerprint,
        "pixel_artifact_sha256": artifact.npz_sha256,
        "condition_count": artifact.condition_count,
        "artifact_manifest": artifact.to_dict(),
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    Path(receipt_path).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt
