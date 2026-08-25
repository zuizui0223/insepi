"""Annotation contracts for V15 real visit-observation validation.

Raw truth annotation is intentionally isolated from algorithm output. The schema
contains primary/reference clip provenance, biological reference truth,
primary-stream observation support, and nuisance labels. It contains no PolliPi,
InsePi, target-evidence, nuisance-score, triad-state, or acquisition-policy field.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .nuisance_effects import NuisanceEffect
from .observation_triad import ObservationAvailability
from .visit_validation import VisitTruthResolution, VisitTruthState


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_ALGORITHM_FIELD_TOKENS = (
    "pollipi",
    "insepi",
    "target_score",
    "nuisance_burden",
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
    primary_support_truth: ObservationAvailability
    nuisance_effects: tuple[NuisanceEffect, ...] = ()
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


@dataclass(frozen=True, slots=True)
class AnnotationBatchSummary:
    windows: int
    annotation_rows: int
    multiply_annotated_windows: int
    double_annotation_fraction: float
    unresolved_reference_truth_windows: int


def validate_raw_annotations(
    rows: list[RawVisitAnnotation],
    *,
    minimum_double_annotation_fraction: float = 0.20,
) -> AnnotationBatchSummary:
    """Validate provenance and the preregistered independent-annotation fraction.

    This validator never adjudicates biological labels automatically. Conflicting
    raw annotations must be resolved by an explicit blinded adjudication step
    before a final VisitTruthRecord is constructed.
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
    return AnnotationBatchSummary(
        windows=len(by_window),
        annotation_rows=len(rows),
        multiply_annotated_windows=multiply,
        double_annotation_fraction=fraction,
        unresolved_reference_truth_windows=unresolved,
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
