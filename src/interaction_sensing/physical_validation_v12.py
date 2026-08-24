"""Outcome-blind trial planning for a future V12 causal physical validation.

This module is engineering infrastructure only. It does not define final V12
sample sizes or claim thresholds. It enforces the structural requirements that
must be satisfied before physical clips are collected:

- event and disturbance interventions are factorially randomised;
- whole day/camera/scene blocks are assigned to development or held-out use;
- treatment order is derived without images or observer outputs;
- observer manifests exclude intervention truth;
- evaluation truth is joined later by immutable trial_id.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence


PLAN_SCHEMA = "interaction-sensing-v12-physical-trial-plan-v1"
OBSERVER_SCHEMA = "interaction-sensing-v12-observer-manifest-v1"
TRUTH_SCHEMA = "interaction-sensing-v12-intervention-truth-v1"
SEED_DOMAIN = "interaction-sensing-v12-physical-randomisation-v1"


@dataclass(frozen=True, slots=True, order=True)
class PhysicalBlock:
    day_id: str
    camera_id: str
    scene_id: str

    @property
    def block_id(self) -> str:
        return f"{self.day_id}|{self.camera_id}|{self.scene_id}"


@dataclass(frozen=True, slots=True)
class Trial:
    trial_id: str
    block_id: str
    day_id: str
    camera_id: str
    scene_id: str
    split: str
    disturbance_family: str
    intensity_label: str
    event_intervention: int
    disturbance_intervention: int
    replicate: int
    randomised_order: int
    randomisation_digest: str


@dataclass(frozen=True, slots=True)
class ObserverClip:
    schema: str
    trial_id: str
    clip_path: str
    clip_sha256: str


@dataclass(frozen=True, slots=True)
class InterventionTruth:
    schema: str
    trial_id: str
    event_intervention: int
    disturbance_intervention: int
    disturbance_family: str
    intensity_label: str
    event_controller_log_sha256: str
    disturbance_controller_log_sha256: str
    external_sensor_log_sha256: str | None


def _require_seed(seed_hex: str) -> str:
    value = seed_hex.strip().lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("V12 randomisation seed must be exactly 64 hex characters")
    return value


def _digest(seed_hex: str, *parts: object) -> str:
    seed = _require_seed(seed_hex)
    text = "|".join((SEED_DOMAIN, seed, *(str(part) for part in parts)))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_trial_plan(
    *,
    seed_hex: str,
    blocks: Sequence[PhysicalBlock],
    heldout_block_ids: Iterable[str],
    disturbance_families: Sequence[str],
    intensity_labels: Sequence[str],
    replicates_per_cell: int,
) -> tuple[Trial, ...]:
    """Build a balanced 2x2 causal-intervention schedule.

    `heldout_block_ids` must be decided before outcomes exist.  The planner never
    examines images or observer outputs and cannot split a physical block across
    development and held-out phases.
    """
    _require_seed(seed_hex)
    if not blocks:
        raise ValueError("at least one physical block is required")
    if len({block.block_id for block in blocks}) != len(blocks):
        raise ValueError("physical block ids must be unique")
    heldout = set(heldout_block_ids)
    available = {block.block_id for block in blocks}
    if not heldout:
        raise ValueError("at least one complete held-out block is required")
    if not heldout < available:
        raise ValueError("held-out blocks must be a non-empty proper subset of blocks")
    if not disturbance_families or len(set(disturbance_families)) != len(disturbance_families):
        raise ValueError("disturbance families must be unique and non-empty")
    if not intensity_labels or len(set(intensity_labels)) != len(intensity_labels):
        raise ValueError("intensity labels must be unique and non-empty")
    if replicates_per_cell < 1:
        raise ValueError("replicates_per_cell must be >= 1")

    provisional: list[tuple[PhysicalBlock, str, str, int, int, int, str]] = []
    for block in sorted(blocks):
        split = "heldout" if block.block_id in heldout else "development"
        for family in disturbance_families:
            for intensity in intensity_labels:
                for event in (0, 1):
                    for disturbance in (0, 1):
                        for replicate in range(replicates_per_cell):
                            digest = _digest(
                                seed_hex,
                                block.block_id,
                                family,
                                intensity,
                                event,
                                disturbance,
                                replicate,
                            )
                            provisional.append(
                                (block, family, intensity, event, disturbance, replicate, digest)
                            )

    # Randomise order within each physical block only.  This preserves a clean
    # block definition while preventing a fixed event/disturbance sequence.
    order_by_key: dict[tuple[str, str, str, int, int, int], int] = {}
    for block in sorted(blocks):
        members = [row for row in provisional if row[0] == block]
        members.sort(key=lambda row: (row[-1], row[1], row[2], row[3], row[4], row[5]))
        for order, row in enumerate(members):
            key = (block.block_id, row[1], row[2], row[3], row[4], row[5])
            order_by_key[key] = order

    trials: list[Trial] = []
    for block, family, intensity, event, disturbance, replicate, digest in provisional:
        split = "heldout" if block.block_id in heldout else "development"
        key = (block.block_id, family, intensity, event, disturbance, replicate)
        trial_id = "v12-" + hashlib.sha256(
            f"{block.block_id}|{family}|{intensity}|{event}|{disturbance}|{replicate}".encode()
        ).hexdigest()[:20]
        trials.append(
            Trial(
                trial_id=trial_id,
                block_id=block.block_id,
                day_id=block.day_id,
                camera_id=block.camera_id,
                scene_id=block.scene_id,
                split=split,
                disturbance_family=family,
                intensity_label=intensity,
                event_intervention=event,
                disturbance_intervention=disturbance,
                replicate=replicate,
                randomised_order=order_by_key[key],
                randomisation_digest=digest,
            )
        )
    trials.sort(key=lambda trial: (trial.block_id, trial.randomised_order))
    return tuple(trials)


def observer_manifest(
    trials: Sequence[Trial],
    clip_identity: dict[str, tuple[str, str]],
) -> tuple[ObserverClip, ...]:
    """Return a truth-free manifest for observer execution.

    `clip_identity[trial_id] = (path, sha256)`.  Treatment/split/block labels are
    deliberately omitted, so an observer runner cannot infer causal truth from
    this manifest.
    """
    if {trial.trial_id for trial in trials} != set(clip_identity):
        raise ValueError("clip identity must contain exactly one entry per trial")
    rows: list[ObserverClip] = []
    for trial in trials:
        path, digest = clip_identity[trial.trial_id]
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest.lower()):
            raise ValueError(f"invalid clip SHA-256 for {trial.trial_id}")
        rows.append(ObserverClip(OBSERVER_SCHEMA, trial.trial_id, str(path), digest.lower()))
    return tuple(rows)


def intervention_truth(
    trial: Trial,
    *,
    event_controller_log_sha256: str,
    disturbance_controller_log_sha256: str,
    external_sensor_log_sha256: str | None,
) -> InterventionTruth:
    for digest in (event_controller_log_sha256, disturbance_controller_log_sha256):
        if len(digest) != 64:
            raise ValueError("controller log hashes must be SHA-256 hex")
    if external_sensor_log_sha256 is not None and len(external_sensor_log_sha256) != 64:
        raise ValueError("external sensor log hash must be SHA-256 hex")
    return InterventionTruth(
        schema=TRUTH_SCHEMA,
        trial_id=trial.trial_id,
        event_intervention=trial.event_intervention,
        disturbance_intervention=trial.disturbance_intervention,
        disturbance_family=trial.disturbance_family,
        intensity_label=trial.intensity_label,
        event_controller_log_sha256=event_controller_log_sha256.lower(),
        disturbance_controller_log_sha256=disturbance_controller_log_sha256.lower(),
        external_sensor_log_sha256=(
            None if external_sensor_log_sha256 is None else external_sensor_log_sha256.lower()
        ),
    )


def write_trial_plan(path: str | Path, trials: Sequence[Trial], *, seed_hex: str) -> Path:
    output = Path(path)
    payload = {
        "schema": PLAN_SCHEMA,
        "seed_sha256": hashlib.sha256(_require_seed(seed_hex).encode()).hexdigest(),
        "trial_count": len(trials),
        "trials": [asdict(trial) for trial in trials],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return output
