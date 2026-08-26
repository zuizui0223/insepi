"""Annotation contracts for V15 real visit-observation validation.

Raw truth annotation is intentionally isolated from algorithm output. The schema
contains primary/reference clip provenance, biological reference truth,
target-coupled local-response truth, component-level primary-stream observation
support, and exogenous nuisance labels. It contains no PolliPi, InsePi,
target-evidence, nuisance-score, triad-state, target-route, or acquisition-policy
field.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .nuisance_effects import NuisanceEffect
from .support_truth import PrimaryStreamSupportTruth, SupportTruthResolution
from .visit_validation import (
    CoupledResponseResolution,
    VisitTruthResolution,
    VisitTruthState,
)


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_ALGORITHM_FIELD_TOKENS = (
    "pollipi",
    "insepi",
    "target_score",
    "direct_target_score",
    "coupled_target_score",
    "target_route",
    "nuisance_burden",
    "nuisance_score",
    "observability_score",
    "support_score",
    "triad_state",
    "prediction",
    "acquisition_policy",
)


@dataclass(frozen=True, slots=True)
class RawVisitAnnotation:
    window_id: str
    block_id: str
    recording_date_local: str
    physical_scene_code: str
    annotator_id: str
    primary_clip_sha256: str
    reference_clip_sha256: str
    biological_truth_resolution: VisitTruthResolution
    biological_state: VisitTruthState | None
    primary_support_truth: PrimaryStreamSupportTruth
    nuisance_effects: tuple[NuisanceEffect, ...] = ()
    target_coupled_response_resolution: CoupledResponseResolution = CoupledResponseResolution.RESOLVED
    target_coupled_response_present: bool | None = False
    notes: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("window_id", self.window_id),
            ("block_id", self.block_id),
            ("recording_date_local", self.recording_date_local),
            ("physical_scene_code", self.physical_scene_code),
            ("annotator_id", self.annotator_id),
        ):
            if not value:
                raise ValueError(f"{name} cannot be empty")
        for name, value in (
            ("primary_clip_sha256", self.primary_clip_sha256),
            ("reference_clip_sha256", self.reference_clip_sha256),
        ):
            if not _SHA256.fullmatch(value):
                raise ValueError(f"{name} must be a lowercase 64-hex SHA-256")
        if self.biological_truth_resolution is VisitTruthResolution.RESOLVED and self.biological_state is None:
            raise ValueError("resolved annotation requires biological_state")
        if self.biological_truth_resolution is VisitTruthResolution.UNRESOLVED and self.biological_state is not None:
            raise ValueError("unresolved annotation must not carry biological_state")

        if self.target_coupled_response_resolution is CoupledResponseResolution.RESOLVED:
            if self.target_coupled_response_present is None:
                raise ValueError("resolved coupled-response annotation requires a boolean state")
        elif self.target_coupled_response_present is not None:
            raise ValueError("unresolved coupled-response annotation must not carry a present/absent state")

        if self.target_coupled_response_present is True:
            if self.biological_truth_resolution is not VisitTruthResolution.RESOLVED:
                raise ValueError("resolved target-coupled response requires resolved biological truth")
            if self.biological_state not in {VisitTruthState.TARGET_CONTACT, VisitTruthState.VISIT_EVENT}:
                raise ValueError("target-coupled response requires target_contact or visit_event truth")

    @property
    def primary_support_availability(self):
        """Derived observable/compromised/unobservable state, or None if unresolved."""

        return self.primary_support_truth.availability


@dataclass(frozen=True, slots=True)
class AnnotationBatchSummary:
    windows: int
    annotation_rows: int
    multiply_annotated_windows: int
    double_annotation_fraction: float
    unresolved_reference_truth_windows: int
    unresolved_coupled_response_windows: int
    unresolved_primary_support_windows: int


def validate_raw_annotations(
    rows: list[RawVisitAnnotation],
    *,
    minimum_double_annotation_fraction: float = 0.20,
) -> AnnotationBatchSummary:
    """Validate provenance and the preregistered independent-annotation fraction.

    This validator never adjudicates biological, coupling, nuisance, or support
    labels automatically. Conflicting raw annotations must be resolved by an
    explicit blinded adjudication step before a final VisitTruthRecord is built.
    """

    if not 0.0 <= minimum_double_annotation_fraction <= 1.0:
        raise ValueError("minimum_double_annotation_fraction must lie in [0, 1]")
    if not rows:
        raise ValueError("annotation batch cannot be empty")

    by_window: dict[str, list[RawVisitAnnotation]] = {}
    for row in rows:
        by_window.setdefault(row.window_id, []).append(row)

    for window_id, annotations in by_window.items():
        first = annotations[0]
        annotators = {row.annotator_id for row in annotations}
        if len(annotators) != len(annotations):
            raise ValueError(f"duplicate annotator for window {window_id}")
        for row in annotations[1:]:
            invariant_fields = (
                row.block_id == first.block_id,
                row.recording_date_local == first.recording_date_local,
                row.physical_scene_code == first.physical_scene_code,
                row.primary_clip_sha256 == first.primary_clip_sha256,
                row.reference_clip_sha256 == first.reference_clip_sha256,
            )
            if not all(invariant_fields):
                raise ValueError(f"provenance mismatch between annotations for window {window_id}")

    multiply = sum(len(items) >= 2 for items in by_window.values())
    fraction = multiply / len(by_window)
    if fraction + 1e-12 < minimum_double_annotation_fraction:
        raise ValueError(
            f"double-annotation fraction {fraction:.6f} below required {minimum_double_annotation_fraction:.6f}"
        )

    unresolved = sum(
        all(row.biological_truth_resolution is VisitTruthResolution.UNRESOLVED for row in items)
        for items in by_window.values()
    )
    unresolved_coupling = sum(
        all(row.target_coupled_response_resolution is CoupledResponseResolution.UNRESOLVED for row in items)
        for items in by_window.values()
    )
    unresolved_support = sum(
        all(row.primary_support_truth.resolution is SupportTruthResolution.UNRESOLVED for row in items)
        for items in by_window.values()
    )
    return AnnotationBatchSummary(
        windows=len(by_window),
        annotation_rows=len(rows),
        multiply_annotated_windows=multiply,
        double_annotation_fraction=fraction,
        unresolved_reference_truth_windows=unresolved,
        unresolved_coupled_response_windows=unresolved_coupling,
        unresolved_primary_support_windows=unresolved_support,
    )


def assert_algorithm_fields_absent(field_names: list[str]) -> None:
    """Fail if a raw truth table schema contains algorithm-derived fields."""

    lowered = [name.lower() for name in field_names]
    leaks = [
        name
        for name in lowered
        if any(token in name for token in FORBIDDEN_ALGORITHM_FIELD_TOKENS)
    ]
    if leaks:
        raise ValueError(f"algorithm-derived fields are forbidden in raw truth annotations: {leaks}")
