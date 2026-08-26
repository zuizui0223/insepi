"""Fail-closed readiness gate for the V15-v2 empirical held-out phase.

This module does not choose scientific thresholds or invent missing measurements.
It only externalises whether every predeclared V15-v2 freeze item has actually
been frozen before held-out scoring may begin.

A blocked gate is a safe state, not a test failure.  Future held-out execution
must call :func:`assert_ready_for_heldout`, which fails closed until the registry
is complete.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping
import json
import re


class FreezeStatus(str, Enum):
    UNSET = "unset"
    DEVELOPMENT_DEFINED = "development_defined"
    FROZEN = "frozen"


class AbsenceStrategy(str, Enum):
    UNDECIDED = "undecided"
    RETAIN_UPPER_BOUND_1 = "retain_upper_bound_1_without_A_minus"
    VALIDATED_A_MINUS = "validated_independent_A_minus"


class PrefreezeGateState(str, Enum):
    BLOCKED_SAFE = "blocked_safe"
    READY = "ready"


CORE_FREEZE_ITEMS: tuple[str, ...] = (
    "biological_truth_annotation",
    "coupling_truth_annotation",
    "nuisance_truth_annotation",
    "support_truth_annotation",
    "split_blinding_protocol",
    "o_measurement_calibration",
    "target_field_adapter",
    "nuisance_field_adapter",
    "forced_vs_certified_absence_metrics",
    "cluster_exposure_estimand",
    "sampling_power_plan",
    "claim_thresholds",
)

A_MINUS_VALIDATION_ITEM = "a_minus_validation_protocol"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class FreezeItem:
    name: str
    status: FreezeStatus
    evidence_path: str | None = None
    sha256: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("freeze item name cannot be empty")
        if self.status is FreezeStatus.FROZEN:
            if not self.evidence_path or not self.evidence_path.strip():
                raise ValueError(f"frozen item {self.name} requires evidence_path")
            if self.sha256 is None or _SHA256_RE.fullmatch(self.sha256) is None:
                raise ValueError(f"frozen item {self.name} requires lowercase 64-hex sha256")


@dataclass(frozen=True, slots=True)
class PrefreezeReadiness:
    state: PrefreezeGateState
    blockers: tuple[str, ...]
    frozen_items: tuple[str, ...]
    development_defined_items: tuple[str, ...]
    unset_items: tuple[str, ...]
    absence_strategy: AbsenceStrategy
    safe_target_presence_upper_bound: float

    @property
    def ready(self) -> bool:
        return self.state is PrefreezeGateState.READY


def _item_from_mapping(raw: Mapping[str, Any]) -> FreezeItem:
    return FreezeItem(
        name=str(raw["name"]),
        status=FreezeStatus(str(raw["status"])),
        evidence_path=None if raw.get("evidence_path") is None else str(raw["evidence_path"]),
        sha256=None if raw.get("sha256") is None else str(raw["sha256"]),
        note=None if raw.get("note") is None else str(raw["note"]),
    )


def evaluate_prefreeze_registry(payload: Mapping[str, Any]) -> PrefreezeReadiness:
    """Evaluate one machine-readable V15-v2 prefreeze registry.

    The registry must enumerate every core item exactly once. Unknown items are
    rejected except for the conditional A-minus validation item. Merely naming an
    artifact does not count as frozen: every frozen item must carry its SHA-256.
    """

    if str(payload.get("generation")) != "V15-v2":
        raise ValueError("prefreeze registry generation must be V15-v2")

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        raise ValueError("prefreeze registry items must be a list")
    items = [_item_from_mapping(raw) for raw in raw_items]
    by_name: dict[str, FreezeItem] = {}
    for item in items:
        if item.name in by_name:
            raise ValueError(f"duplicate freeze item: {item.name}")
        by_name[item.name] = item

    allowed = set(CORE_FREEZE_ITEMS) | {A_MINUS_VALIDATION_ITEM}
    unknown = sorted(set(by_name) - allowed)
    if unknown:
        raise ValueError(f"unknown freeze items: {unknown}")

    missing = sorted(set(CORE_FREEZE_ITEMS) - set(by_name))
    if missing:
        raise ValueError(f"missing core freeze items: {missing}")

    strategy = AbsenceStrategy(str(payload.get("absence_strategy", AbsenceStrategy.UNDECIDED.value)))
    upper_bound = float(payload.get("safe_target_presence_upper_bound", 1.0))
    if not 0.0 <= upper_bound <= 1.0:
        raise ValueError("safe_target_presence_upper_bound must lie in [0, 1]")

    blockers: list[str] = []
    frozen: list[str] = []
    development_defined: list[str] = []
    unset: list[str] = []

    for name in CORE_FREEZE_ITEMS:
        item = by_name[name]
        if item.status is FreezeStatus.FROZEN:
            frozen.append(name)
        elif item.status is FreezeStatus.DEVELOPMENT_DEFINED:
            development_defined.append(name)
            blockers.append(name)
        else:
            unset.append(name)
            blockers.append(name)

    if strategy is AbsenceStrategy.UNDECIDED:
        blockers.append("absence_strategy")
    elif strategy is AbsenceStrategy.RETAIN_UPPER_BOUND_1:
        if upper_bound != 1.0:
            raise ValueError("no-A-minus strategy must retain target-presence upper bound at 1")
    else:
        validation = by_name.get(A_MINUS_VALIDATION_ITEM)
        if validation is None or validation.status is not FreezeStatus.FROZEN:
            blockers.append(A_MINUS_VALIDATION_ITEM)

    state = PrefreezeGateState.READY if not blockers else PrefreezeGateState.BLOCKED_SAFE
    return PrefreezeReadiness(
        state=state,
        blockers=tuple(blockers),
        frozen_items=tuple(frozen),
        development_defined_items=tuple(development_defined),
        unset_items=tuple(unset),
        absence_strategy=strategy,
        safe_target_presence_upper_bound=upper_bound,
    )


def load_prefreeze_registry(path: str | Path) -> Mapping[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_ready_for_heldout(payload: Mapping[str, Any]) -> PrefreezeReadiness:
    """Fail closed unless all required V15-v2 held-out prerequisites are frozen."""

    readiness = evaluate_prefreeze_registry(payload)
    if not readiness.ready:
        raise RuntimeError(
            "V15-v2 held-out execution BLOCKED_SAFE; unresolved prefreeze items: "
            + ", ".join(readiness.blockers)
        )
    return readiness
