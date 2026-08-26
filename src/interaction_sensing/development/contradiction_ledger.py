"""Contradiction-ledger rules for alternating observer development.

The ledger encodes an important negative capability: some contradictions must not
be "fixed" by changing an observer. Information absence remains undetermined, and
legitimate process coupling remains multi-process truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ObserverRole(str, Enum):
    TARGET = "target"
    NUISANCE = "nuisance"


class ContradictionCause(str, Enum):
    DEFINITION_DEFECT = "definition_defect"
    REPRESENTATION_DEFECT = "representation_defect"
    INFORMATION_ABSENT = "information_absent"
    PROCESS_COUPLING = "process_coupling"


class DevelopmentAction(str, Enum):
    REVISE_DEFINITION_NEW_GENERATION = "revise_definition_new_generation"
    MODIFY_TARGET_OBSERVER = "modify_target_observer"
    MODIFY_NUISANCE_OBSERVER = "modify_nuisance_observer"
    RETAIN_UNDETERMINED = "retain_undetermined"
    RETAIN_MULTI_PROCESS_TRUTH = "retain_multi_process_truth"


def action_for_contradiction(
    cause: ContradictionCause,
    *,
    modifiable_observer: ObserverRole | None,
) -> DevelopmentAction:
    if cause is ContradictionCause.DEFINITION_DEFECT:
        if modifiable_observer is not None:
            raise ValueError("definition defects require a new definition generation; do not tune an observer")
        return DevelopmentAction.REVISE_DEFINITION_NEW_GENERATION

    if cause is ContradictionCause.INFORMATION_ABSENT:
        if modifiable_observer is not None:
            raise ValueError("information absence cannot be repaired by observer tuning")
        return DevelopmentAction.RETAIN_UNDETERMINED

    if cause is ContradictionCause.PROCESS_COUPLING:
        if modifiable_observer is not None:
            raise ValueError("legitimate process coupling must not be forced into one observer class")
        return DevelopmentAction.RETAIN_MULTI_PROCESS_TRUTH

    if cause is ContradictionCause.REPRESENTATION_DEFECT:
        if modifiable_observer is ObserverRole.TARGET:
            return DevelopmentAction.MODIFY_TARGET_OBSERVER
        if modifiable_observer is ObserverRole.NUISANCE:
            return DevelopmentAction.MODIFY_NUISANCE_OBSERVER
        raise ValueError("representation defects require exactly one explicitly modifiable observer")

    raise ValueError(f"unsupported contradiction cause: {cause}")


@dataclass(frozen=True, slots=True)
class ContradictionRecord:
    batch_id: str
    frozen_observer: ObserverRole | None
    modifiable_observer: ObserverRole | None
    pi1: float
    pi2: float
    pi3: float
    pi4: float
    latent_T: bool
    latent_N: bool
    latent_C: bool
    target_output: str
    nuisance_output: str
    observation_support: float
    identifiability_margin: float
    contradiction_signature: str
    cause_class: ContradictionCause
    planned_action: DevelopmentAction
    new_type_boolean: bool

    def __post_init__(self) -> None:
        if not self.batch_id.strip():
            raise ValueError("batch_id cannot be empty")
        if not self.contradiction_signature.strip():
            raise ValueError("contradiction_signature cannot be empty")
        if self.latent_C and not self.latent_T:
            raise ValueError("C implies T in the V14 closed-world ontology")
        for name, value in (
            ("pi1", self.pi1),
            ("pi2", self.pi2),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        for name, value in (
            ("pi3", self.pi3),
            ("pi4", self.pi4),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        for name, value in (
            ("observation_support", self.observation_support),
            ("identifiability_margin", self.identifiability_margin),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must lie in [0,1]")

        expected = action_for_contradiction(
            self.cause_class,
            modifiable_observer=self.modifiable_observer,
        )
        if expected is not self.planned_action:
            raise ValueError(
                f"planned action {self.planned_action.value} violates cause-class contract; expected {expected.value}"
            )
        if self.frozen_observer is not None and self.frozen_observer is self.modifiable_observer:
            raise ValueError("the same observer cannot be both frozen and modifiable")
        if self.cause_class is ContradictionCause.REPRESENTATION_DEFECT:
            if self.frozen_observer is None:
                raise ValueError("alternating development requires the sibling observer to be explicitly frozen")
            if self.modifiable_observer is None:
                raise ValueError("representation defect must identify one modifiable observer")


@dataclass(slots=True)
class SaturationTracker:
    """Operational type-saturation stop rule for V14b.

    The tracker does not optimise contradiction rate. It only tracks whether new
    contradiction *types* continue to appear and whether all required phase
    strata have been sampled during the zero-new-type streak.
    """

    required_strata: frozenset[str]
    zero_new_batches_required: int = 3
    seen_types: set[str] = field(default_factory=set)
    zero_new_streak: int = 0
    strata_in_current_streak: set[str] = field(default_factory=set)
    residual_rates: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.zero_new_batches_required < 1:
            raise ValueError("zero_new_batches_required must be positive")
        if not self.required_strata:
            raise ValueError("required_strata cannot be empty")

    def add_batch(
        self,
        contradiction_types: set[str],
        sampled_strata: set[str],
        *,
        residual_rate: float,
    ) -> None:
        if not 0.0 <= residual_rate <= 1.0:
            raise ValueError("residual_rate must lie in [0,1]")
        if not sampled_strata <= self.required_strata:
            unknown = sorted(sampled_strata - self.required_strata)
            raise ValueError(f"unknown sampled strata: {unknown}")

        new_types = contradiction_types - self.seen_types
        self.seen_types.update(contradiction_types)
        self.residual_rates.append(residual_rate)

        if new_types:
            self.zero_new_streak = 0
            self.strata_in_current_streak.clear()
        else:
            self.zero_new_streak += 1
            self.strata_in_current_streak.update(sampled_strata)

    @property
    def saturated(self) -> bool:
        return (
            self.zero_new_streak >= self.zero_new_batches_required
            and self.required_strata <= self.strata_in_current_streak
        )

    @property
    def monotonic_residual_warning(self) -> bool:
        if len(self.residual_rates) < self.zero_new_batches_required:
            return False
        recent = self.residual_rates[-self.zero_new_batches_required :]
        return all(a > b for a, b in zip(recent, recent[1:]))
