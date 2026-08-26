import pytest

from interaction_sensing.layered_visit_truth import (
    BiologicalTruthAnnotation,
    CouplingTruthAnnotation,
    NuisanceTruthAnnotation,
    SupportTruthAnnotation,
    join_layered_truth,
)
from interaction_sensing.nuisance_effects import NuisanceEffect
from interaction_sensing.support_truth import PrimaryStreamSupportTruth, SupportComponentState
from interaction_sensing.visit_validation import (
    CoupledResponseResolution,
    VisitTruthResolution,
    VisitTruthState,
)


REF = "a" * 64
PRIMARY = "b" * 64


def observable_truth() -> PrimaryStreamSupportTruth:
    a = SupportComponentState.ADEQUATE
    return PrimaryStreamSupportTruth(a, a, a, a, a, "blinded_primary_support_pass")


def test_layered_join_keeps_reference_and_primary_truth_provenance_separate() -> None:
    biological = BiologicalTruthAnnotation(
        "w1", "b1", REF, "bio-a", VisitTruthResolution.RESOLVED, VisitTruthState.VISIT_EVENT, "event-1"
    )
    coupling = CouplingTruthAnnotation(
        "w1", REF, "coupling-a", CoupledResponseResolution.RESOLVED, True
    )
    nuisance = NuisanceTruthAnnotation(
        "w1", PRIMARY, "nuisance-a", (NuisanceEffect.MASK_TARGET,)
    )
    support = SupportTruthAnnotation("w1", PRIMARY, "support-a", observable_truth())

    joined = join_layered_truth(biological, coupling, nuisance, support)
    assert joined.visit_truth.is_visit is True
    assert joined.visit_truth.support_truth.value == "observable"
    assert joined.visit_truth.nuisance_labels == ("mask_target",)
    assert joined.biological_annotator_id == "bio-a"
    assert joined.support_annotator_id == "support-a"


def test_positive_coupling_cannot_override_no_insect_reference_truth() -> None:
    biological = BiologicalTruthAnnotation(
        "w1", "b1", REF, "bio-a", VisitTruthResolution.RESOLVED, VisitTruthState.NO_INSECT
    )
    coupling = CouplingTruthAnnotation(
        "w1", REF, "coupling-a", CoupledResponseResolution.RESOLVED, True
    )
    nuisance = NuisanceTruthAnnotation("w1", PRIMARY, "nuisance-a", ())
    support = SupportTruthAnnotation("w1", PRIMARY, "support-a", observable_truth())
    with pytest.raises(ValueError, match="requires target_contact"):
        join_layered_truth(biological, coupling, nuisance, support)


def test_reference_clip_mismatch_fails_closed() -> None:
    biological = BiologicalTruthAnnotation(
        "w1", "b1", REF, "bio-a", VisitTruthResolution.RESOLVED, VisitTruthState.NO_INSECT
    )
    coupling = CouplingTruthAnnotation(
        "w1", "c" * 64, "coupling-a", CoupledResponseResolution.RESOLVED, False
    )
    nuisance = NuisanceTruthAnnotation("w1", PRIMARY, "nuisance-a", ())
    support = SupportTruthAnnotation("w1", PRIMARY, "support-a", observable_truth())
    with pytest.raises(ValueError, match="reference clip provenance"):
        join_layered_truth(biological, coupling, nuisance, support)


def test_primary_clip_mismatch_fails_closed() -> None:
    biological = BiologicalTruthAnnotation(
        "w1", "b1", REF, "bio-a", VisitTruthResolution.RESOLVED, VisitTruthState.NO_INSECT
    )
    coupling = CouplingTruthAnnotation(
        "w1", REF, "coupling-a", CoupledResponseResolution.RESOLVED, False
    )
    nuisance = NuisanceTruthAnnotation("w1", PRIMARY, "nuisance-a", ())
    support = SupportTruthAnnotation("w1", "d" * 64, "support-a", observable_truth())
    with pytest.raises(ValueError, match="primary clip provenance"):
        join_layered_truth(biological, coupling, nuisance, support)


def test_unresolved_biological_truth_remains_unresolved_after_join() -> None:
    biological = BiologicalTruthAnnotation(
        "w1", "b1", REF, "bio-a", VisitTruthResolution.UNRESOLVED, None
    )
    coupling = CouplingTruthAnnotation(
        "w1", REF, "coupling-a", CoupledResponseResolution.UNRESOLVED, None
    )
    nuisance = NuisanceTruthAnnotation("w1", PRIMARY, "nuisance-a", ())
    support = SupportTruthAnnotation("w1", PRIMARY, "support-a", observable_truth())
    joined = join_layered_truth(biological, coupling, nuisance, support)
    assert joined.visit_truth.biological_truth_resolved is False
    assert joined.visit_truth.biological_state is None
