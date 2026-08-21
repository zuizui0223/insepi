"""Fail-closed V7 lock verification.

The final V7 master seed is intentionally unavailable until every frozen input is
explicitly reachable and the lock manifest is marked ready.  This module contains
no default identifiers and never infers reachability from a SHA string alone.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping


LOCK_SCHEMA = "pollipi-insepi-v7-lock-v1"
SEED_DOMAIN = "pollipi-insepi-v7-master-seed-v1"
EXPECTED_WEIGHTS = {
    "exploration": 0.5,
    "pollipi": 0.1,
    "insepi": 0.4,
    "disagreement": 0.0,
}
EXPECTED_PREVALENCES = (0.1, 0.5, 0.9)
EXPECTED_BUDGETS = (0.1, 0.25, 0.5)


class V7LockError(RuntimeError):
    """Raised whenever V7 materialisation preconditions are not satisfied."""


@dataclass(frozen=True, slots=True)
class V7FrozenInputs:
    pollipi_method_sha: str
    insepi_method_sha: str
    allocator_sha: str
    generator_sha: str
    baseline_registry_sha256: str
    world_spec_sha256: str


def _is_git_sha(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def _is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def load_lock_manifest(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_manifest_is_safely_blocked(manifest: Mapping[str, object]) -> tuple[str, ...]:
    """Verify a blocked manifest contains no materialised V7 seed/fingerprint."""

    if manifest.get("schema") != LOCK_SCHEMA:
        raise V7LockError("unexpected V7 lock schema")
    if manifest.get("status") != "blocked":
        raise V7LockError("manifest is not in blocked state")
    forbidden = (
        "master_seed_hex",
        "world_fingerprint",
        "pollipi_trace_sha256",
        "cross_report_sha256",
    )
    present = tuple(key for key in forbidden if manifest.get(key) not in (None, ""))
    if present:
        raise V7LockError(f"blocked manifest contains materialised evidence: {present}")
    blockers = manifest.get("blockers")
    if not isinstance(blockers, list) or not blockers:
        raise V7LockError("blocked manifest must enumerate at least one blocker")
    return tuple(str(item) for item in blockers)


def validate_ready_manifest(
    manifest: Mapping[str, object],
    *,
    reachable_shas: Mapping[str, str],
    current_allocator_sha: str,
    current_generator_sha: str,
    expected_world_spec_sha256: str,
) -> V7FrozenInputs:
    """Validate all frozen inputs before any final seed may be derived.

    ``reachable_shas`` must come from an external repository-resolution step.  A
    manifest merely containing a 40-hex value is never treated as proof that the
    commit is actually materialisable.
    """

    if manifest.get("schema") != LOCK_SCHEMA:
        raise V7LockError("unexpected V7 lock schema")
    if manifest.get("status") != "ready":
        raise V7LockError("V7 lock is not ready; seed derivation is forbidden")

    ids = manifest.get("frozen_inputs")
    if not isinstance(ids, Mapping):
        raise V7LockError("missing frozen_inputs")

    for key in ("pollipi_method_sha", "insepi_method_sha", "allocator_sha", "generator_sha"):
        if not _is_git_sha(ids.get(key)):
            raise V7LockError(f"invalid or missing {key}")
    if not _is_sha256(ids.get("baseline_registry_sha256")):
        raise V7LockError("invalid baseline_registry_sha256")
    if not _is_sha256(ids.get("world_spec_sha256")):
        raise V7LockError("invalid world_spec_sha256")

    pollipi_sha = str(ids["pollipi_method_sha"]).lower()
    insepi_sha = str(ids["insepi_method_sha"]).lower()
    allocator_sha = str(ids["allocator_sha"]).lower()
    generator_sha = str(ids["generator_sha"]).lower()

    if reachable_shas.get("pollipi_method_sha", "").lower() != pollipi_sha:
        raise V7LockError("PolliPi frozen method SHA is not externally verified as reachable")
    if reachable_shas.get("insepi_method_sha", "").lower() != insepi_sha:
        raise V7LockError("InsePi frozen method SHA is not externally verified as reachable")
    if current_allocator_sha.lower() != allocator_sha:
        raise V7LockError("allocator SHA differs from frozen lock")
    if current_generator_sha.lower() != generator_sha:
        raise V7LockError("generator SHA differs from frozen lock")
    if str(ids["world_spec_sha256"]).lower() != expected_world_spec_sha256.lower():
        raise V7LockError("world-spec fingerprint differs from frozen lock")

    weights = manifest.get("weights")
    if weights != EXPECTED_WEIGHTS:
        raise V7LockError(f"V7 weights differ from frozen V6 candidate: {weights}")
    if tuple(manifest.get("prevalences", ())) != EXPECTED_PREVALENCES:
        raise V7LockError("V7 prevalence registry differs from preregistration")
    if tuple(manifest.get("budgets", ())) != EXPECTED_BUDGETS:
        raise V7LockError("V7 budget registry differs from preregistration")
    if int(manifest.get("world_windows", 0)) != 4800:
        raise V7LockError("V7 world_windows must remain 4800")
    if int(manifest.get("replicates", 0)) != 200:
        raise V7LockError("V7 replicates must remain 200")

    pass_rules = manifest.get("pass_rules")
    if not isinstance(pass_rules, Mapping):
        raise V7LockError("missing pass_rules")
    required_rules = {
        "joint_ratio_floor": 0.98,
        "mean_joint_ratio_strictly_above": 1.0,
        "max_tv": 0.25,
        "legacy_tolerance": 0.01,
    }
    for key, expected in required_rules.items():
        if float(pass_rules.get(key, float("nan"))) != expected:
            raise V7LockError(f"pass rule changed: {key}")

    for forbidden in ("master_seed_hex", "world_fingerprint", "pollipi_trace_sha256", "cross_report_sha256"):
        if manifest.get(forbidden) not in (None, ""):
            raise V7LockError(f"ready pre-execution manifest already contains {forbidden}")

    return V7FrozenInputs(
        pollipi_method_sha=pollipi_sha,
        insepi_method_sha=insepi_sha,
        allocator_sha=allocator_sha,
        generator_sha=generator_sha,
        baseline_registry_sha256=str(ids["baseline_registry_sha256"]).lower(),
        world_spec_sha256=str(ids["world_spec_sha256"]).lower(),
    )


def derive_master_seed_hex(inputs: V7FrozenInputs) -> str:
    """Derive the one-shot V7 seed only from already validated immutable inputs."""

    payload = "|".join((
        SEED_DOMAIN,
        inputs.pollipi_method_sha,
        inputs.insepi_method_sha,
        inputs.allocator_sha,
        inputs.generator_sha,
        inputs.baseline_registry_sha256,
        inputs.world_spec_sha256,
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
