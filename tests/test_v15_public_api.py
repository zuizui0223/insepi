from interaction_sensing.v15 import (
    PrimaryStreamSupportEstimator,
    TargetAbsenceEvidence,
    VisitSystemVariant,
    VisitTruthState,
)


def test_v15_facade_exposes_empirical_bridge_without_replacing_root_api() -> None:
    assert PrimaryStreamSupportEstimator().observable_threshold == 0.70
    assert TargetAbsenceEvidence.unavailable().supports_absence is False
    assert VisitSystemVariant.FULL_TRIAD.value.startswith("full_direct_coupled")
    assert VisitTruthState.VISIT_EVENT.is_visit is True
