import pytest

from interaction_sensing.development.visit_contradiction import (
    VisitContradictionRecord,
    VisitContradictionSaturationTracker,
    VisitDevelopmentAction,
    VisitDevelopmentCause,
    VisitDiagnosticPattern,
    VisitObserverSnapshot,
    VisitPatternClassifier,
    VisitSubsystem,
    permitted_action,
)
from interaction_sensing.observation_triad import ObservationAvailability


def snapshot(
    direct: float,
    coupled: float,
    nuisance: float,
    availability: ObservationAvailability,
    support: float = 0.9,
) -> VisitObserverSnapshot:
    return VisitObserverSnapshot(direct, coupled, nuisance, availability, support)


def test_target_and_nuisance_high_is_superposition_not_automatic_error() -> None:
    pattern = VisitPatternClassifier().classify(
        snapshot(0.9, 0.1, 0.9, ObservationAvailability.OBSERVABLE)
    )
    assert pattern is VisitDiagnosticPattern.TARGET_NUISANCE_SUPERPOSITION


def test_quiet_low_nuisance_unobservable_is_information_pattern_not_absence() -> None:
    pattern = VisitPatternClassifier().classify(
        snapshot(0.1, 0.1, 0.1, ObservationAvailability.UNOBSERVABLE, support=0.1)
    )
    assert pattern is VisitDiagnosticPattern.QUIET_UNOBSERVABLE


def test_weak_direct_but_high_coupled_route_is_rescue_candidate() -> None:
    pattern = VisitPatternClassifier().classify(
        snapshot(0.1, 0.9, 0.1, ObservationAvailability.OBSERVABLE)
    )
    assert pattern is VisitDiagnosticPattern.COUPLED_RESCUE_CANDIDATE


def test_high_target_under_unobservable_support_is_target_support_conflict() -> None:
    pattern = VisitPatternClassifier().classify(
        snapshot(0.9, 0.1, 0.1, ObservationAvailability.UNOBSERVABLE, support=0.1)
    )
    assert pattern is VisitDiagnosticPattern.TARGET_SUPPORT_CONFLICT


def test_representation_defect_modifies_exactly_one_subsystem() -> None:
    assert permitted_action(
        VisitDevelopmentCause.REPRESENTATION_DEFECT,
        modifiable_subsystem=VisitSubsystem.SUPPORT,
    ) is VisitDevelopmentAction.MODIFY_SUPPORT
    with pytest.raises(ValueError, match="exactly one"):
        permitted_action(VisitDevelopmentCause.REPRESENTATION_DEFECT, modifiable_subsystem=None)


def test_information_absence_cannot_be_repaired_by_tuning_target() -> None:
    assert permitted_action(
        VisitDevelopmentCause.INFORMATION_ABSENT,
        modifiable_subsystem=None,
    ) is VisitDevelopmentAction.RETAIN_CENSORED
    with pytest.raises(ValueError, match="cannot be repaired"):
        permitted_action(
            VisitDevelopmentCause.INFORMATION_ABSENT,
            modifiable_subsystem=VisitSubsystem.TARGET,
        )


def test_essential_ambiguity_selects_intervention_not_observer_tuning() -> None:
    assert permitted_action(
        VisitDevelopmentCause.ESSENTIAL_AMBIGUITY,
        modifiable_subsystem=None,
    ) is VisitDevelopmentAction.DESIGN_DISCRIMINATING_INTERVENTION


def test_legitimate_coupling_is_retained_not_forced_into_target_or_nuisance() -> None:
    assert permitted_action(
        VisitDevelopmentCause.LEGITIMATE_PROCESS_COUPLING,
        modifiable_subsystem=None,
    ) is VisitDevelopmentAction.RETAIN_MULTI_PROCESS_STATE


def test_alternating_record_requires_both_siblings_frozen() -> None:
    row = VisitContradictionRecord(
        batch_id="batch-1",
        window_id="w1",
        block_id="block-1",
        snapshot=snapshot(0.1, 0.1, 0.1, ObservationAvailability.UNOBSERVABLE, support=0.1),
        pattern=VisitDiagnosticPattern.QUIET_UNOBSERVABLE,
        contradiction_type="support_undercoverage",
        cause=VisitDevelopmentCause.REPRESENTATION_DEFECT,
        frozen_subsystems=frozenset({VisitSubsystem.TARGET, VisitSubsystem.NUISANCE}),
        modifiable_subsystem=VisitSubsystem.SUPPORT,
        planned_action=VisitDevelopmentAction.MODIFY_SUPPORT,
        diagnostic_test="compare O estimate to independent primary-stream support truth",
        truth_joined_after_observer_output=True,
        new_type_boolean=True,
    )
    assert row.modifiable_subsystem is VisitSubsystem.SUPPORT

    with pytest.raises(ValueError, match="all sibling"):
        VisitContradictionRecord(
            batch_id="batch-1",
            window_id="w1",
            block_id="block-1",
            snapshot=row.snapshot,
            pattern=row.pattern,
            contradiction_type="support_undercoverage",
            cause=VisitDevelopmentCause.REPRESENTATION_DEFECT,
            frozen_subsystems=frozenset({VisitSubsystem.TARGET}),
            modifiable_subsystem=VisitSubsystem.SUPPORT,
            planned_action=VisitDevelopmentAction.MODIFY_SUPPORT,
            diagnostic_test="support truth comparison",
            truth_joined_after_observer_output=True,
            new_type_boolean=True,
        )


def test_truth_must_be_joined_only_after_observer_output() -> None:
    with pytest.raises(ValueError, match="joined only after"):
        VisitContradictionRecord(
            batch_id="batch-1",
            window_id="w1",
            block_id="block-1",
            snapshot=snapshot(0.9, 0.1, 0.9, ObservationAvailability.OBSERVABLE),
            pattern=VisitDiagnosticPattern.TARGET_NUISANCE_SUPERPOSITION,
            contradiction_type="target_nuisance_disagreement",
            cause=VisitDevelopmentCause.LEGITIMATE_PROCESS_COUPLING,
            frozen_subsystems=frozenset(),
            modifiable_subsystem=None,
            planned_action=VisitDevelopmentAction.RETAIN_MULTI_PROCESS_STATE,
            diagnostic_test="reference truth",
            truth_joined_after_observer_output=False,
            new_type_boolean=True,
        )


def test_saturation_is_type_saturation_not_zero_residual_count() -> None:
    tracker = VisitContradictionSaturationTracker(
        required_strata=frozenset({"clean", "nuisance", "low_support"}),
        zero_new_batches_required=2,
    )
    tracker.add_batch({"type_a", "type_b"}, {"clean", "nuisance", "low_support"})
    assert tracker.saturated is False
    tracker.add_batch({"type_a", "type_b"}, {"clean", "nuisance"})
    assert tracker.saturated is False
    tracker.add_batch({"type_a", "type_b"}, {"low_support"})
    assert tracker.saturated is True
    assert tracker.residual_type_counts[-1] == 2  # contradictions may remain at stop
