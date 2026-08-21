from interaction_sensing.simulation.portable_visual_v2 import (
    PORTABLE_VISUAL_V2_FINGERPRINT,
    SCENARIO_IDS,
    suite_fingerprint,
)
from interaction_sensing.simulation.visual_contradiction_v2 import run_visual_contradiction_v2


def test_portable_visual_world_fingerprint_is_stable():
    assert suite_fingerprint() == PORTABLE_VISUAL_V2_FINGERPRINT


def test_v2_runs_pixel_observability_front_end_deterministically():
    first = run_visual_contradiction_v2()
    second = run_visual_contradiction_v2()
    assert [row.to_dict() for row in first] == [row.to_dict() for row in second]
    assert [row.scenario_id for row in first] == list(SCENARIO_IDS)
    assert all(0.0 <= row.false_event_risk <= 1.0 for row in first)
    assert all(0.0 <= row.missed_event_risk <= 1.0 for row in first)
    assert all(0.0 <= row.attribution_risk <= 1.0 for row in first)
    print("INSEPI_V2", [(row.scenario_id, row.true_visit, row.inferred_noise_source, row.observability_state) for row in first])
