"""Outcome-blind trial planning for a future V12 causal physical validation.

This module is engineering infrastructure only. It does not define final V12
sample sizes or claim thresholds. It enforces the structural requirements that
must be satisfied before physical clips are collected:

- event and disturbance interventions are factorially randomised;
- whole day/camera/scene blocks are assigned to development or held-out use;
- treatment order is derived without images or observer outputs;
- observer manifests exclude intervention truth;
- observer-facing trial ids/filenames do not encode treatment labels;
- development and held-out observer bundles cannot be mixed;
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
ID_DOMAIN = "interaction-sensing-v12-opaque-trial-id-v1"


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


def _require_sha256(value: str, name: str) -> str:
    digest = value.strip().lower()
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError(f"{name} must be exactly 64 hex characters")
    return digest


def _digest(seed_hex: str, *parts: object) -> str:
    seed = _require_seed(seed_hex)
    text = "|".join((SEED_DOMAIN, seed, *(str(part) for part in parts)))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _opaque_trial_id(seed_hex: str, block_id: str, randomised_order: int) -> str:
    """Create an observer-facing id from a neutral randomised slot, not treatment labels."""
    seed = _require_seed(seed_hex)
    text = f"{ID_DOMAIN}|{seed}|{block_id}|slot{int(randomised_order)}"
    return "v12-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


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

    `heldout_block_ids` must be decided before outcomes exist. The planner never
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
        order = order_by_key[key]
        trial_id = _opaque_trial_id(seed_hex, block.block_id, order)
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
                randomised_order=order,
                randomisation_digest=digest,
            )
        )
    trials.sort(key=lambda trial: (trial.block_id, trial.randomised_order))
    if len({trial.trial_id for trial in trials}) != len(trials):
        raise AssertionError("opaque V12 trial ids collided")
    return tuple(trials)


def observer_manifest(
    trials: Sequence[Trial],
    clip_identity: dict[str, tuple[str, str]],
    *,
    allowed_split: str,
) -> tuple[ObserverClip, ...]:
    """Return a truth-free manifest for exactly one preregistered split.

    Treatment/split/block labels are omitted. Observer-facing filenames use only
    opaque trial ids. Mixing held-out trials into a development manifest (or vice
    versa) fails before observer execution.
    """
    if allowed_split not in {"development", "heldout"}:
        raise ValueError("allowed_split must be development or heldout")
    if not trials:
        raise ValueError("observer manifest trials cannot be empty")
    if any(trial.split != allowed_split for trial in trials):
        raise ValueError(f"observer manifest mixes trials outside {allowed_split} split")
    if {trial.trial_id for trial in trials} != set(clip_identity):
        raise ValueError("clip identity must contain exactly one entry per trial")
    rows: list[ObserverClip] = []
    for trial in trials:
        path, digest = clip_identity[trial.trial_id]
        if Path(path).stem != trial.trial_id:
            raise ValueError(
                f"observer-facing clip filename must equal opaque trial id: {path}"
            )
        rows.append(
            ObserverClip(
                OBSERVER_SCHEMA,
                trial.trial_id,
                str(path),
                _require_sha256(digest, f"clip SHA-256 for {trial.trial_id}"),
            )
        )
    return tuple(rows)


def intervention_truth(
    trial: Trial,
    *,
    event_controller_log_sha256: str,
    disturbance_controller_log_sha256: str,
    external_sensor_log_sha256: str | None,
) -> InterventionTruth:
    event_hash = _require_sha256(event_controller_log_sha256, "event controller log SHA-256")
    disturbance_hash = _require_sha256(
        disturbance_controller_log_sha256, "disturbance controller log SHA-256"
    )
    sensor_hash = (
        None
        if external_sensor_log_sha256 is None
        else _require_sha256(external_sensor_log_sha256, "external sensor log SHA-256")
    )
    return InterventionTruth(
        schema=TRUTH_SCHEMA,
        trial_id=trial.trial_id,
        event_intervention=trial.event_intervention,
        disturbance_intervention=trial.disturbance_intervention,
        disturbance_family=trial.disturbance_family,
        intensity_label=trial.intensity_label,
        event_controller_log_sha256=event_hash,
        disturbance_controller_log_sha256=disturbance_hash,
        external_sensor_log_sha256=sensor_hash,
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
