from __future__ import annotations

from collections import Counter

import pytest

from interaction_sensing.physical_validation_v12 import (
    PhysicalBlock,
    _opaque_trial_id,
    build_trial_plan,
    intervention_truth,
    observer_manifest,
)

SEED = "ab" * 32


def blocks() -> list[PhysicalBlock]:
    return [
        PhysicalBlock("day1", "cam1", "sceneA"),
        PhysicalBlock("day1", "cam2", "sceneA"),
        PhysicalBlock("day2", "cam1", "sceneB"),
        PhysicalBlock("day3", "cam1", "sceneC"),
    ]


def plan():
    return build_trial_plan(
        seed_hex=SEED,
        blocks=blocks(),
        heldout_block_ids={"day3|cam1|sceneC"},
        disturbance_families=("wind_like", "occlusion"),
        intensity_labels=("low", "high"),
        replicates_per_cell=2,
    )


def test_v12_plan_is_deterministic_and_seals_whole_heldout_blocks() -> None:
    first = plan()
    second = plan()
    assert first == second
    by_block = {}
    for trial in first:
        by_block.setdefault(trial.block_id, set()).add(trial.split)
    assert all(len(splits) == 1 for splits in by_block.values())
    assert by_block["day3|cam1|sceneC"] == {"heldout"}
    assert all(splits == {"development"} for block, splits in by_block.items() if block != "day3|cam1|sceneC")


def test_v12_each_block_family_intensity_is_exactly_balanced_two_by_two() -> None:
    trials = plan()
    keys = Counter(
        (trial.block_id, trial.disturbance_family, trial.intensity_label, trial.event_intervention, trial.disturbance_intervention)
        for trial in trials
    )
    assert set(keys.values()) == {2}
    groups = {
        (trial.block_id, trial.disturbance_family, trial.intensity_label)
        for trial in trials
    }
    for group in groups:
        assert {
            (event, disturbance)
            for block_id, family, intensity, event, disturbance in keys
            if (block_id, family, intensity) == group
        } == {(0, 0), (1, 0), (0, 1), (1, 1)}


def test_v12_randomised_order_is_unique_within_block() -> None:
    by_block = {}
    for trial in plan():
        by_block.setdefault(trial.block_id, []).append(trial.randomised_order)
    for orders in by_block.values():
        assert sorted(orders) == list(range(len(orders)))


def test_v12_trial_id_depends_on_neutral_slot_not_treatment_tuple() -> None:
    trials = plan()
    for trial in trials:
        assert trial.trial_id == _opaque_trial_id(SEED, trial.block_id, trial.randomised_order)
        # Observer id itself carries no readable treatment/family/intensity token.
        assert trial.disturbance_family not in trial.trial_id
        assert trial.intensity_label not in trial.trial_id
        assert trial.block_id not in trial.trial_id


def test_v12_observer_manifest_contains_no_intervention_or_split_truth() -> None:
    trials = plan()
    clips = {trial.trial_id: (f"clips/{trial.trial_id}.mp4", "12" * 32) for trial in trials}
    manifest = observer_manifest(trials, clips)
    assert len(manifest) == len(trials)
    forbidden = {
        "event_intervention", "disturbance_intervention", "disturbance_family",
        "intensity_label", "split", "block_id", "day_id", "camera_id", "scene_id",
    }
    for row in manifest:
        assert forbidden.isdisjoint(row.__dataclass_fields__)
        assert row.trial_id in clips


def test_v12_observer_manifest_rejects_descriptive_truth_leaking_filename() -> None:
    trials = plan()
    clips = {trial.trial_id: (f"clips/{trial.trial_id}.mp4", "12" * 32) for trial in trials}
    first = trials[0]
    clips[first.trial_id] = (
        f"clips/{first.trial_id}-{first.disturbance_family}-E{first.event_intervention}.mp4",
        "12" * 32,
    )
    with pytest.raises(ValueError, match="opaque trial id"):
        observer_manifest(trials, clips)


def test_v12_truth_is_joined_separately_by_trial_id() -> None:
    trial = plan()[0]
    truth = intervention_truth(
        trial,
        event_controller_log_sha256="34" * 32,
        disturbance_controller_log_sha256="56" * 32,
        external_sensor_log_sha256="78" * 32,
    )
    assert truth.trial_id == trial.trial_id
    assert truth.event_intervention == trial.event_intervention
    assert truth.disturbance_intervention == trial.disturbance_intervention


def test_v12_requires_nonempty_proper_heldout_block_set() -> None:
    with pytest.raises(ValueError):
        build_trial_plan(
            seed_hex=SEED,
            blocks=blocks(),
            heldout_block_ids=set(),
            disturbance_families=("wind",),
            intensity_labels=("low",),
            replicates_per_cell=1,
        )
    with pytest.raises(ValueError):
        build_trial_plan(
            seed_hex=SEED,
            blocks=blocks(),
            heldout_block_ids={block.block_id for block in blocks()},
            disturbance_families=("wind",),
            intensity_labels=("low",),
            replicates_per_cell=1,
        )
