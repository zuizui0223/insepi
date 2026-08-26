import pytest

from interaction_sensing.target_field_adapter_v15 import (
    POLLIPI_ORDINAL_TARGET_SCALE,
    POLLIPI_TARGET_EVIDENCE_MAPPING,
    PolliPiTargetEvidenceInput,
    adapt_pollipi_target_evidence,
)


def test_frozen_pollipi_mapping_is_exact_and_positive_only() -> None:
    assert POLLIPI_TARGET_EVIDENCE_MAPPING == {
        "no_activity": 0.0,
        "environmental_noise": 0.0,
        "uncertain_local_activity": 0.5,
        "strong_visitation_candidate": 1.0,
    }
    for state, score in POLLIPI_TARGET_EVIDENCE_MAPPING.items():
        record = PolliPiTargetEvidenceInput(state, score)
        adapted = adapt_pollipi_target_evidence(record)
        routes = adapted.to_target_routes()
        assert adapted.direct_target_score == score
        assert adapted.source_scale == POLLIPI_ORDINAL_TARGET_SCALE
        assert routes.direct_insect_score == score
        assert routes.coupled_response_score == 0.0
        assert routes.target_link_confidence == 0.0
        assert routes.source_state == f"pollipi:{state}"


def test_zero_pollipi_score_is_not_absence_or_nuisance_and_has_no_coupled_route() -> None:
    for state in ("no_activity", "environmental_noise"):
        record = PolliPiTargetEvidenceInput(state, 0.0)
        routes = adapt_pollipi_target_evidence(record).to_target_routes()
        assert routes.direct_insect_score == 0.0
        assert routes.aggregate_score == 0.0
        # The adapter exposes no negative-evidence, nuisance, or observability field.
        assert not hasattr(record, "negative_evidence")
        assert not hasattr(record, "nuisance")
        assert not hasattr(record, "observability")


def test_adapter_rejects_score_remapping_scale_change_and_confirmed_visit() -> None:
    with pytest.raises(ValueError, match="requires frozen ordinal score"):
        PolliPiTargetEvidenceInput("uncertain_local_activity", 0.6)
    with pytest.raises(ValueError, match="unsupported PolliPi target-evidence scale"):
        PolliPiTargetEvidenceInput("uncertain_local_activity", 0.5, scale="probability")
    with pytest.raises(ValueError, match="cannot certify visitation"):
        PolliPiTargetEvidenceInput("strong_visitation_candidate", 1.0, confirmed_visit=True)
    with pytest.raises(ValueError, match="unsupported PolliPi target-evidence state"):
        PolliPiTargetEvidenceInput("invented_state", 0.0)
