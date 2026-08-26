import pytest

from interaction_sensing.absence_certification import TargetAbsenceEvidence


def test_absence_evidence_defaults_to_unavailable() -> None:
    evidence = TargetAbsenceEvidence.unavailable()
    assert evidence.supports_absence is False
    assert evidence.source is None
    assert evidence.validation_ref is None
    assert evidence.independent_of_positive_target_path is False


def test_positive_absence_evidence_requires_named_independent_validation() -> None:
    with pytest.raises(ValueError, match="named source"):
        TargetAbsenceEvidence(supports_absence=True, independent_of_positive_target_path=True, validation_ref="v1")
    with pytest.raises(ValueError, match="validation reference"):
        TargetAbsenceEvidence(supports_absence=True, independent_of_positive_target_path=True, source="negative-channel")
    with pytest.raises(ValueError, match="inverting the positive target path"):
        TargetAbsenceEvidence(
            supports_absence=True,
            source="one-minus-target-score",
            validation_ref="not-independent",
            independent_of_positive_target_path=False,
        )


def test_independently_validated_constructor_records_provenance() -> None:
    evidence = TargetAbsenceEvidence.independently_validated(
        source="independent_negative_channel",
        validation_ref="heldout-v15-negative-evidence",
    )
    assert evidence.supports_absence is True
    assert evidence.independent_of_positive_target_path is True
    assert evidence.source == "independent_negative_channel"
    assert evidence.validation_ref == "heldout-v15-negative-evidence"
