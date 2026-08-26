"""Layer-separated truth ledgers for V15 real visit validation.

The four V15 truth layers are scientifically independent and should not be
annotated in one cognitively coupled pass.  In particular, knowing from the
reference camera that an insect visited must not influence whether the primary
stream is judged observable.

This module therefore keeps biological/coupling truth on the reference channel and
nuisance/support truth on the primary channel in separate ledgers.  They are
joined only after layer-specific annotation/adjudication is complete.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .nuisance_effects import NuisanceEffect
from .support_truth import PrimaryStreamSupportTruth
from .visit_validation import (
    CoupledResponseResolution,
    VisitTruthRecord,
    VisitTruthResolution,
    VisitTruthState,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _require_sha(name: str, value: str) -> None:
    if not _SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase 64-hex SHA-256")


@dataclass(frozen=True, slots=True)
class BiologicalTruthAnnotation:
    """Reference-channel biological state; primary stream is not shown."""

    window_id: str
    block_id: str
    reference_clip_sha256: str
    annotator_id: str
    resolution: VisitTruthResolution
    state: VisitTruthState | None
    event_id: str | None = None

    def __post_init__(self) -> None:
        _require_sha("reference_clip_sha256", self.reference_clip_sha256)
        if not self.window_id or not self.block_id or not self.annotator_id:
            raise ValueError("window_id, block_id and annotator_id are required")
        if self.resolution is VisitTruthResolution.RESOLVED and self.state is None:
            raise ValueError("resolved biological annotation requires state")
        if self.resolution is VisitTruthResolution.UNRESOLVED and self.state is not None:
            raise ValueError("unresolved biological annotation must not carry state")
        if self.resolution is VisitTruthResolution.UNRESOLVED and self.event_id is not None:
            raise ValueError("unresolved biological annotation must not carry event_id")
        if self.state is VisitTruthState.VISIT_EVENT and not self.event_id:
            raise ValueError("visit_event requires stable event_id")
        if self.state is not VisitTruthState.VISIT_EVENT and self.event_id is not None:
            raise ValueError("event_id is reserved for visit_event")


@dataclass(frozen=True, slots=True)
class CouplingTruthAnnotation:
    """Reference-channel causal attribution of local target response."""

    window_id: str
    reference_clip_sha256: str
    annotator_id: str
    resolution: CoupledResponseResolution
    present: bool | None

    def __post_init__(self) -> None:
        _require_sha("reference_clip_sha256", self.reference_clip_sha256)
        if not self.window_id or not self.annotator_id:
            raise ValueError("window_id and annotator_id are required")
        if self.resolution is CoupledResponseResolution.RESOLVED and self.present is None:
            raise ValueError("resolved coupling annotation requires boolean present")
        if self.resolution is CoupledResponseResolution.UNRESOLVED and self.present is not None:
            raise ValueError("unresolved coupling annotation must not carry present/absent state")


@dataclass(frozen=True, slots=True)
class NuisanceTruthAnnotation:
    """Primary-stream exogenous nuisance effects; biological reference is hidden."""

    window_id: str
    primary_clip_sha256: str
    annotator_id: str
    effects: tuple[NuisanceEffect, ...]

    def __post_init__(self) -> None:
        _require_sha("primary_clip_sha256", self.primary_clip_sha256)
        if not self.window_id or not self.annotator_id:
            raise ValueError("window_id and annotator_id are required")
        if len(set(self.effects)) != len(self.effects):
            raise ValueError("nuisance effects must be unique")


@dataclass(frozen=True, slots=True)
class SupportTruthAnnotation:
    """Primary-stream observation support; biological reference is hidden."""

    window_id: str
    primary_clip_sha256: str
    annotator_id: str
    truth: PrimaryStreamSupportTruth

    def __post_init__(self) -> None:
        _require_sha("primary_clip_sha256", self.primary_clip_sha256)
        if not self.window_id or not self.annotator_id:
            raise ValueError("window_id and annotator_id are required")


@dataclass(frozen=True, slots=True)
class LayeredTruthJoin:
    visit_truth: VisitTruthRecord
    nuisance_effects: tuple[NuisanceEffect, ...]
    biological_annotator_id: str
    coupling_annotator_id: str
    nuisance_annotator_id: str
    support_annotator_id: str


def join_layered_truth(
    biological: BiologicalTruthAnnotation,
    coupling: CouplingTruthAnnotation,
    nuisance: NuisanceTruthAnnotation,
    support: SupportTruthAnnotation,
) -> LayeredTruthJoin:
    """Join independently completed truth ledgers by window provenance.

    The function validates cross-ledger consistency but never resolves a conflict
    automatically.  A positive coupling label must be supported by independently
    resolved biological contact/visit truth.
    """

    window_ids = {biological.window_id, coupling.window_id, nuisance.window_id, support.window_id}
    if len(window_ids) != 1:
        raise ValueError("layered truth window_id values must match")
    if coupling.reference_clip_sha256 != biological.reference_clip_sha256:
        raise ValueError("reference clip provenance mismatch between biological and coupling truth")
    if nuisance.primary_clip_sha256 != support.primary_clip_sha256:
        raise ValueError("primary clip provenance mismatch between nuisance and support truth")

    if coupling.present is True:
        if biological.resolution is not VisitTruthResolution.RESOLVED:
            raise ValueError("positive coupling requires resolved biological truth")
        if biological.state not in {VisitTruthState.TARGET_CONTACT, VisitTruthState.VISIT_EVENT}:
            raise ValueError("positive coupling requires target_contact or visit_event truth")

    truth = VisitTruthRecord(
        window_id=biological.window_id,
        block_id=biological.block_id,
        biological_state=biological.state,
        primary_support_truth=support.truth,
        nuisance_labels=tuple(effect.value for effect in nuisance.effects),
        biological_truth_resolution=biological.resolution,
        reference_truth_source="independent_reference_channel",
        event_id=biological.event_id,
        target_coupled_response_present=coupling.present,
        target_coupled_response_resolution=coupling.resolution,
    )
    return LayeredTruthJoin(
        visit_truth=truth,
        nuisance_effects=nuisance.effects,
        biological_annotator_id=biological.annotator_id,
        coupling_annotator_id=coupling.annotator_id,
        nuisance_annotator_id=nuisance.annotator_id,
        support_annotator_id=support.annotator_id,
    )
