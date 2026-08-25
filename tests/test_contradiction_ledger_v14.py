import pytest

from interaction_sensing.development.contradiction_ledger import (
    ContradictionCause,
    ContradictionRecord,
    DevelopmentAction,
    ObserverRole,
    SaturationTracker,
    action_for_contradiction,
)


def test_information_absence_cannot_be_repaired_by_observer_tuning() -> None:
    with pytest.raises(ValueError, match="information absence"):
        action_for_contradiction(
            ContradictionCause.INFORMATION_ABSENT,
            modifiable_observer=ObserverRole.TARGET,
        )
    assert action_for_contradiction(
        ContradictionCause.INFORMATION_ABSENT,
        modifiable_observer=None,
    ) is DevelopmentAction.RETAIN_UNDETERMINED


def test_process_coupling_cannot_be_forced_into_one_observer() -> None:
    with pytest.raises(ValueError, match="coupling"):
        action_for_contradiction(
            ContradictionCause.PROCESS_COUPLING,
            modifiable_observer=ObserverRole.NUISANCE,
        )
    assert action_for_contradiction(
        ContradictionCause.PROCESS_COUPLING,
        modifiable_observer=None,
    ) is DevelopmentAction.RETAIN_MULTI_PROCESS_TRUTH


def test_representation_defect_changes_exactly_one_observer() -> None:
    assert action_for_contradiction(
        ContradictionCause.REPRESENTATION_DEFECT,
        modifiable_observer=ObserverRole.TARGET,
    ) is DevelopmentAction.MODIFY_TARGET_OBSERVER
    assert action_for_contradiction(
        ContradictionCause.REPRESENTATION_DEFECT,
        modifiable_observer=ObserverRole.NUISANCE,
    ) is DevelopmentAction.MODIFY_NUISANCE_OBSERVER
    with pytest.raises(ValueError):
        action_for_contradiction(
            ContradictionCause.REPRESENTATION_DEFECT,
            modifiable_observer=None,
        )


def test_record_enforces_alternating_freeze_and_action_contract() -> None:
    record = ContradictionRecord(
        batch_id="b1",
        frozen_observer=ObserverRole.NUISANCE,
        modifiable_observer=ObserverRole.TARGET,
        pi1=1.0,
        pi2=1.0,
        pi3=0.1,
        pi4=0.0,
        latent_T=True,
        latent_N=False,
        latent_C=False,
        target_output="low",
        nuisance_output="low",
        observation_support=0.8,
        identifiability_margin=0.9,
        contradiction_signature="target_miss_despite_support",
        cause_class=ContradictionCause.REPRESENTATION_DEFECT,
        planned_action=DevelopmentAction.MODIFY_TARGET_OBSERVER,
        new_type_boolean=True,
    )
    assert record.frozen_observer is ObserverRole.NUISANCE

    with pytest.raises(ValueError, match="violates cause-class contract"):
        ContradictionRecord(
            batch_id="b2",
            frozen_observer=None,
            modifiable_observer=None,
            pi1=0.1,
            pi2=1.0,
            pi3=0.0,
            pi4=0.0,
            latent_T=True,
            latent_N=False,
            latent_C=False,
            target_output="low",
            nuisance_output="low",
            observation_support=0.0,
            identifiability_margin=1.0,
            contradiction_signature="no_information",
            cause_class=ContradictionCause.INFORMATION_ABSENT,
            planned_action=DevelopmentAction.MODIFY_TARGET_OBSERVER,
            new_type_boolean=False,
        )


def test_c_implies_t_is_fail_closed() -> None:
    with pytest.raises(ValueError, match="C implies T"):
        ContradictionRecord(
            batch_id="bad",
            frozen_observer=None,
            modifiable_observer=None,
            pi1=1.0,
            pi2=1.0,
            pi3=1.0,
            pi4=1.0,
            latent_T=False,
            latent_N=True,
            latent_C=True,
            target_output="low",
            nuisance_output="high",
            observation_support=0.5,
            identifiability_margin=0.5,
            contradiction_signature="invalid_truth",
            cause_class=ContradictionCause.PROCESS_COUPLING,
            planned_action=DevelopmentAction.RETAIN_MULTI_PROCESS_TRUTH,
            new_type_boolean=True,
        )


def test_saturation_requires_type_stasis_and_full_transition_strata_coverage() -> None:
    strata = frozenset({"short_window", "pi2_near_one", "small_target", "indirect_rescue"})
    tracker = SaturationTracker(required_strata=strata, zero_new_batches_required=3)

    tracker.add_batch({"type-a"}, {"short_window"}, residual_rate=0.30)
    assert tracker.saturated is False

    tracker.add_batch({"type-a"}, {"short_window", "pi2_near_one"}, residual_rate=0.25)
    tracker.add_batch({"type-a"}, {"small_target"}, residual_rate=0.20)
    tracker.add_batch({"type-a"}, {"indirect_rescue"}, residual_rate=0.15)
    assert tracker.saturated is True
    assert tracker.monotonic_residual_warning is True


def test_new_type_resets_saturation_streak() -> None:
    tracker = SaturationTracker(required_strata=frozenset({"all"}), zero_new_batches_required=2)
    tracker.add_batch({"a"}, {"all"}, residual_rate=0.4)
    tracker.add_batch({"a"}, {"all"}, residual_rate=0.3)
    tracker.add_batch({"b"}, {"all"}, residual_rate=0.3)
    assert tracker.zero_new_streak == 0
    assert tracker.saturated is False
