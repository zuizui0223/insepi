from interaction_sensing.nuisance_observer_v14b import NuisanceObservationV14b
from interaction_sensing.target_observer_v14b import TargetObservationV14b, TargetRouteState
from interaction_sensing.ternary_decision_v14b import decide_v14b
from interaction_sensing.ternary_semantics_v14c import (
    ClarifiedUndeterminedReason,
    PI3_CLAIM_BOUNDARY,
    clarified_reason,
    legacy_non_target_decision_width,
    visit_presence_bounds,
)

THRESHOLD = 4.33898869355123e-06


def _t(direct=0.0, local=0.0):
    supported = direct > 0
    state = (
        TargetRouteState.DIRECT_WITH_LOCAL_RESPONSE
        if supported and local > 0
        else TargetRouteState.DIRECT_SUPPORTED
        if supported
        else TargetRouteState.INDIRECT_UNATTRIBUTED
        if local > 0
        else TargetRouteState.NONE
    )
    return TargetObservationV14b(direct, local, state, supported, (not supported and local > 0))


def _n(process=0.0, obs=1.0):
    return NuisanceObservationV14b(0.0, 0.0, process, obs)


def test_historical_information_absent_is_weakened_to_no_supported_evidence():
    d = decide_v14b(_t(), _n(process=1e-9), nuisance_threshold=THRESHOLD)
    assert clarified_reason(d) is ClarifiedUndeterminedReason.NO_SUPPORTED_EVIDENCE


def test_overlap_reason_is_preserved():
    d = decide_v14b(_t(direct=0.2), _n(process=1.0), nuisance_threshold=THRESHOLD)
    assert clarified_reason(d) is ClarifiedUndeterminedReason.OVERLAP_OR_ATTRIBUTION


def test_positive_only_target_observer_gives_upper_bound_one_without_absence_channel():
    bounds = visit_presence_bounds(target_supported_rate=0.42873333333333336)
    assert bounds.lower == 0.42873333333333336
    assert bounds.upper == 1.0
    assert abs(bounds.width - 0.5712666666666667) < 1e-12
    assert bounds.absence_certifying_channel_available is False


def test_certified_absence_channel_can_tighten_upper_bound_later():
    bounds = visit_presence_bounds(target_supported_rate=0.4, certified_target_absence_rate=0.3)
    assert bounds.lower == 0.4
    assert bounds.upper == 0.7
    assert abs(bounds.width - 0.3) < 1e-12
    assert bounds.absence_certifying_channel_available is True


def test_legacy_metric_is_explicitly_separate():
    assert abs(legacy_non_target_decision_width(baseline_rate=0.2302328231292517, undetermined_rate=0.2533362244897959) - 0.4835690476190476) < 1e-12


def test_pi3_claim_boundary_is_structural_not_universal_amplitude_claim():
    assert "structural" in PI3_CLAIM_BOUNDARY
    assert "not evidence" in PI3_CLAIM_BOUNDARY
