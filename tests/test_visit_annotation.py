import pytest

from interaction_sensing.nuisance_effects import NuisanceEffect
from interaction_sensing.observation_triad import ObservationAvailability
from interaction_sensing.visit_annotation import (
    RawVisitAnnotation,
    assert_algorithm_fields_absent,
    validate_raw_annotations,
)
from interaction_sensing.visit_validation import VisitTruthResolution, VisitTruthState


SHA_A = "a" * 64
SHA_B = "b" * 64


def row(
    window_id: str,
    annotator: str,
    *,
    resolution: VisitTruthResolution = VisitTruthResolution.RESOLVED,
    biological_state: VisitTruthState | None = VisitTruthState.NO_INSECT,
) -> RawVisitAnnotation:
    return RawVisitAnnotation(
        window_id=window_id,
        block_id="block-1",
        recording_date_local="2026-08-25",
        physical_scene_code="scene-A",
        annotator_id=annotator,
        primary_clip_sha256=SHA_A,
        reference_clip_sha256=SHA_B,
        biological_truth_resolution=resolution,
        biological_state=biological_state,
        primary_support_truth=ObservationAvailability.OBSERVABLE,
        nuisance_effects=(NuisanceEffect.MIMIC_TARGET,),
    )


def test_double_annotation_fraction_is_enforced() -> None:
    rows = [
        row("w1", "a"),
        row("w1", "b"),
        row("w2", "a"),
        row("w3", "a"),
        row("w4", "a"),
        row("w5", "a"),
    ]
    summary = validate_raw_annotations(rows)
    assert summary.windows == 5
    assert summary.multiply_annotated_windows == 1
    assert summary.double_annotation_fraction == 0.2


def test_batch_below_double_annotation_fraction_fails() -> None:
    with pytest.raises(ValueError, match="double-annotation fraction"):
        validate_raw_annotations([row(f"w{i}", "a") for i in range(5)])


def test_unresolved_reference_truth_has_no_biological_label() -> None:
    unresolved = row(
        "w1",
        "a",
        resolution=VisitTruthResolution.UNRESOLVED,
        biological_state=None,
    )
    assert unresolved.biological_state is None


def test_unresolved_reference_truth_cannot_be_no_insect() -> None:
    with pytest.raises(ValueError, match="must not carry"):
        row(
            "w1",
            "a",
            resolution=VisitTruthResolution.UNRESOLVED,
            biological_state=VisitTruthState.NO_INSECT,
        )


def test_annotation_provenance_mismatch_fails() -> None:
    first = row("w1", "a")
    second = RawVisitAnnotation(
        window_id="w1",
        block_id="block-2",
        recording_date_local="2026-08-25",
        physical_scene_code="scene-A",
        annotator_id="b",
        primary_clip_sha256=SHA_A,
        reference_clip_sha256=SHA_B,
        biological_truth_resolution=VisitTruthResolution.RESOLVED,
        biological_state=VisitTruthState.NO_INSECT,
        primary_support_truth=ObservationAvailability.OBSERVABLE,
    )
    with pytest.raises(ValueError, match="provenance mismatch"):
        validate_raw_annotations([first, second], minimum_double_annotation_fraction=1.0)


def test_raw_truth_schema_rejects_algorithm_fields() -> None:
    assert_algorithm_fields_absent(
        [
            "window_id",
            "biological_state",
            "primary_support_truth",
            "reference_clip_sha256",
        ]
    )
    with pytest.raises(ValueError, match="algorithm-derived fields"):
        assert_algorithm_fields_absent(["window_id", "pollipi_state", "triad_state"])


def test_clip_hashes_are_required() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        RawVisitAnnotation(
            window_id="w1",
            block_id="b1",
            recording_date_local="2026-08-25",
            physical_scene_code="scene-A",
            annotator_id="a",
            primary_clip_sha256="not-a-hash",
            reference_clip_sha256=SHA_B,
            biological_truth_resolution=VisitTruthResolution.RESOLVED,
            biological_state=VisitTruthState.NO_INSECT,
            primary_support_truth=ObservationAvailability.OBSERVABLE,
        )
