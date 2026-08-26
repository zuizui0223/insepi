"""Contradiction-guided development for target, nuisance, and support subsystems.

The runtime observation pattern is not itself a causal diagnosis.  In particular,
target and nuisance evidence may both be valid because biological events and
exogenous disturbance can coexist.  This module therefore separates:

1. a truth-free pattern emitted from T/C/N/O outputs;
2. a post-hoc development cause assigned only after independent truth/audit;
3. the only subsystem that is permitted to change in the next diagnostic round.

The goal is not zero disagreement.  Development stops when contradiction *types*
saturate and the remaining cases are explicitly classified as information absence,
essential ambiguity, model uncertainty, or legitimate process coupling.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..observation_triad import ObservationAvailability


class VisitSubsystem(str, Enum):
    TARGET = "target"
    NUISANCE = "nuisance"
    SUPPORT = "support"


class VisitDiagnosticPattern(str, Enum):
    CLEAN_TARGET = "clean_target"
    TARGET_NUISANCE_SUPERPOSITION = "target_nuisance_superposition"
    TARGET_SUPPORT_CONFLICT = "target_support_conflict"
    NUISANCE_POSSIBLE_MISS = "nuisance_possible_miss"
    QUIET_OBSERVABLE = "quiet_observable"
    QUIET_COMPROMISED = "quiet_compromised"
    QUIET_UNOBSERVABLE = "quiet_unobservable"
    COUPLED_RESCUE_CANDIDATE = "coupled_rescue_candidate"
    COUPLED_NUISANCE_SUPERPOSITION = "coupled_nuisance_superposition"
    INTERMEDIATE = "intermediate"


class VisitDevelopmentCause(str, Enum):
    DEFINITION_DEFECT = "definition_defect"
    REPRESENTATION_DEFECT = "representation_defect"
    INFORMATION_ABSENT = "information_absent"
    ESSENTIAL_AMBIGUITY = "essential_ambiguity"
    MODEL_UNCERTAINTY = "model_uncertainty"
    LEGITIMATE_PROCESS_COUPLING = "legitimate_process_coupling"


class VisitDevelopmentAction(str, Enum):
    REVISE_DEFINITION_NEW_GENERATION = "revise_definition_new_generation"
    MODIFY_TARGET = "modify_target"
    MODIFY_NUISANCE = "modify_nuisance"
    MODIFY_SUPPORT = "modify_support"
    RETAIN_CENSORED = "retain_censored"
    DESIGN_DISCRIMINATING_INTERVENTION = "design_discriminating_intervention"
    COLLECT_OR_CALIBRATE_MODEL = "collect_or_calibrate_model"
    RETAIN_MULTI_PROCESS_STATE = "retain_multi_process_state"


@dataclass(frozen=True, slots=True)
class VisitObserverSnapshot:
    """Truth-free outputs available before development truth is joined."""

    direct_target_score: float
    coupled_target_score: float
    nuisance_burden: float
    support_availability: ObservationAvailability
    support_ceiling: float

    def __post_init__(self) -> None:
        for name, value in (
            ("direct_target_score", self.direct_target_score),
            ("coupled_target_score", self.coupled_target_score),
            ("nuisance_burden", self.nuisance_burden),
            ("support_ceiling", self.support_ceiling),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0, 1]")


@dataclass(frozen=True, slots=True)
class VisitPatternClassifier:
    target_high: float = 0.65
    target_low: float = 0.25
    nuisance_high: float = 0.60
    coupled_high: float = 0.65

    def classify(self, row: VisitObserverSnapshot) -> VisitDiagnosticPattern:
        direct_high = row.direct_target_score >= self.target_high
        direct_low = row.direct_target_score <= self.target_low
        coupled_high = row.coupled_target_score >= self.coupled_high
        nuisance_high = row.nuisance_burden >= self.nuisance_high

        if row.support_availability is ObservationAvailability.UNOBSERVABLE:
            if direct_high or coupled_high:
                return VisitDiagnosticPattern.TARGET_SUPPORT_CONFLICT
            return VisitDiagnosticPattern.QUIET_UNOBSERVABLE

        if coupled_high and direct_low:
            if nuisance_high:
                return VisitDiagnosticPattern.COUPLED_NUISANCE_SUPERPOSITION
            return VisitDiagnosticPattern.COUPLED_RESCUE_CANDIDATE

        if direct_high and nuisance_high:
            return VisitDiagnosticPattern.TARGET_NUISANCE_SUPERPOSITION
        if direct_high:
            return VisitDiagnosticPattern.CLEAN_TARGET
        if direct_low and nuisance_high:
            return VisitDiagnosticPattern.NUISANCE_POSSIBLE_MISS
        if direct_low and row.support_availability is ObservationAvailability.OBSERVABLE:
            return VisitDiagnosticPattern.QUIET_OBSERVABLE
        if direct_low:
            return VisitDiagnosticPattern.QUIET_COMPROMISED
        return VisitDiagnosticPattern.INTERMEDIATE


def permitted_action(
    cause: VisitDevelopmentCause,
    *,
    modifiable_subsystem: VisitSubsystem | None,
) -> VisitDevelopmentAction:
    """Map a post-truth diagnosis to the only permitted next development action."""

    if cause is VisitDevelopmentCause.DEFINITION_DEFECT:
        if modifiable_subsystem is not None:
            raise ValueError("definition defect requires a new generation, not subsystem tuning")
        return VisitDevelopmentAction.REVISE_DEFINITION_NEW_GENERATION

    if cause is VisitDevelopmentCause.INFORMATION_ABSENT:
        if modifiable_subsystem is not None:
            raise ValueError("information absence cannot be repaired by tuning a subsystem")
        return VisitDevelopmentAction.RETAIN_CENSORED

    if cause is VisitDevelopmentCause.ESSENTIAL_AMBIGUITY:
        if modifiable_subsystem is not None:
            raise ValueError("essential ambiguity requires a discriminating intervention or new measurement")
        return VisitDevelopmentAction.DESIGN_DISCRIMINATING_INTERVENTION

    if cause is VisitDevelopmentCause.LEGITIMATE_PROCESS_COUPLING:
        if modifiable_subsystem is not None:
            raise ValueError("legitimate process coupling must not be tuned away")
        return VisitDevelopmentAction.RETAIN_MULTI_PROCESS_STATE

    if cause is VisitDevelopmentCause.REPRESENTATION_DEFECT:
        if modifiable_subsystem is VisitSubsystem.TARGET:
            return VisitDevelopmentAction.MODIFY_TARGET
        if modifiable_subsystem is VisitSubsystem.NUISANCE:
            return VisitDevelopmentAction.MODIFY_NUISANCE
        if modifiable_subsystem is VisitSubsystem.SUPPORT:
            return VisitDevelopmentAction.MODIFY_SUPPORT
        raise ValueError("representation defect requires exactly one modifiable subsystem")

    if cause is VisitDevelopmentCause.MODEL_UNCERTAINTY:
        if modifiable_subsystem is None:
            raise ValueError("model uncertainty must identify one subsystem to calibrate")
        return VisitDevelopmentAction.COLLECT_OR_CALIBRATE_MODEL

    raise ValueError(f"unsupported development cause: {cause}")


@dataclass(frozen=True, slots=True)
class VisitContradictionRecord:
    """One auditable development decision after truth/audit has been joined."""

    batch_id: str
    window_id: str
    block_id: str
    snapshot: VisitObserverSnapshot
    pattern: VisitDiagnosticPattern
    contradiction_type: str
    cause: VisitDevelopmentCause
    frozen_subsystems: frozenset[VisitSubsystem]
    modifiable_subsystem: VisitSubsystem | None
    planned_action: VisitDevelopmentAction
    diagnostic_test: str
    truth_joined_after_observer_output: bool
    new_type_boolean: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("batch_id", self.batch_id),
            ("window_id", self.window_id),
            ("block_id", self.block_id),
            ("contradiction_type", self.contradiction_type),
            ("diagnostic_test", self.diagnostic_test),
        ):
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")

        if not self.truth_joined_after_observer_output:
            raise ValueError("development truth must be joined only after observer output")

        expected = permitted_action(self.cause, modifiable_subsystem=self.modifiable_subsystem)
        if expected is not self.planned_action:
            raise ValueError(
                f"planned action {self.planned_action.value} violates cause contract; expected {expected.value}"
            )

        if self.modifiable_subsystem is not None and self.modifiable_subsystem in self.frozen_subsystems:
            raise ValueError("modifiable subsystem cannot also be frozen")

        if self.cause in {VisitDevelopmentCause.REPRESENTATION_DEFECT, VisitDevelopmentCause.MODEL_UNCERTAINTY}:
            if self.modifiable_subsystem is None:
                raise ValueError("observer/model defect must identify a modifiable subsystem")
            required_frozen = set(VisitSubsystem) - {self.modifiable_subsystem}
            if not required_frozen <= set(self.frozen_subsystems):
                raise ValueError("alternating development requires all sibling subsystems to remain frozen")
        elif self.modifiable_subsystem is not None:
            raise ValueError("non-model causes must not silently modify a subsystem")


@dataclass(slots=True)
class VisitContradictionSaturationTracker:
    """Stop on contradiction-type saturation, never on zero contradiction count."""

    required_strata: frozenset[str]
    zero_new_batches_required: int = 3
    seen_types: set[str] = field(default_factory=set)
    zero_new_streak: int = 0
    strata_in_streak: set[str] = field(default_factory=set)
    residual_type_counts: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.required_strata:
            raise ValueError("required_strata cannot be empty")
        if self.zero_new_batches_required < 1:
            raise ValueError("zero_new_batches_required must be positive")

    def add_batch(self, contradiction_types: set[str], sampled_strata: set[str]) -> None:
        if not sampled_strata <= self.required_strata:
            raise ValueError("sampled_strata contains unknown strata")
        new_types = contradiction_types - self.seen_types
        self.seen_types.update(contradiction_types)
        self.residual_type_counts.append(len(contradiction_types))
        if new_types:
            self.zero_new_streak = 0
            self.strata_in_streak.clear()
        else:
            self.zero_new_streak += 1
            self.strata_in_streak.update(sampled_strata)

    @property
    def saturated(self) -> bool:
        return (
            self.zero_new_streak >= self.zero_new_batches_required
            and self.required_strata <= self.strata_in_streak
        )
