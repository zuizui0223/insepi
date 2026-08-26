from interaction_sensing.nuisance_observer_v14b import NuisanceObservationV14b
from interaction_sensing.target_observer_v14b import TargetObservationV14b, TargetRouteState
from interaction_sensing.ternary_decision_v14b import decide_v14b, TernaryState, UndeterminedReason

THRESHOLD = 4.33898869355123e-06


def _t(direct=0.0, local=0.0):
    supported = direct > 0
    return TargetObservationV14b(direct, local, TargetRouteState.DIRECT_SUPPORTED if supported else (TargetRouteState.INDIRECT_UNATTRIBUTED if local > 0 else TargetRouteState.NONE), supported, (not supported and local > 0))


def _n(process=0.0, obs=1.0):
    return NuisanceObservationV14b(0.0, 0.0, process, obs)


def test_baseline_is_outside_ternary_query():
    d = decide_v14b(_t(), _n(), nuisance_threshold=THRESHOLD)
    assert d.state is TernaryState.BASELINE
    assert d.reason is UndeterminedReason.NONE


def test_positive_routes_are_defined_independently():
    assert decide_v14b(_t(direct=0.2), _n(), nuisance_threshold=THRESHOLD).state is TernaryState.TARGET
    assert decide_v14b(_t(), _n(process=1.0), nuisance_threshold=THRESHOLD).state is TernaryState.NUISANCE


def test_simultaneous_positive_support_is_overlap_u_not_forced_class():
    d = decide_v14b(_t(direct=0.2), _n(process=1.0), nuisance_threshold=THRESHOLD)
    assert d.state is TernaryState.UNDETERMINED
    assert d.reason is UndeterminedReason.OVERLAP_OR_ATTRIBUTION


def test_indirect_only_response_remains_attribution_u():
    d = decide_v14b(_t(local=0.2), _n(), nuisance_threshold=THRESHOLD)
    assert d.state is TernaryState.UNDETERMINED
    assert d.reason is UndeterminedReason.OVERLAP_OR_ATTRIBUTION
