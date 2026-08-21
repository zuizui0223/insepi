import numpy as np

from interaction_sensing.simulation.v7_artifact import write_world_artifact
from interaction_sensing.simulation.v7_insepi_adapter import run_insepi_v7_artifact


DUMMY_MASTER_SEED = "12" * 32


def test_insepi_adapter_passes_only_pixels_to_decision_fn(tmp_path):
    npz = tmp_path / "dummy-v7.npz"
    manifest = tmp_path / "dummy-v7.json"
    write_world_artifact(npz, manifest, master_seed_hex=DUMMY_MASTER_SEED)

    calls = []

    def decision_fn(frame, background):
        assert isinstance(frame, np.ndarray)
        assert isinstance(background, np.ndarray)
        calls.append((frame.shape, background.shape))
        return {
            "inferred_noise_source": "stable_scene",
            "observability_state": "clean",
            "false_event_risk": 0.0,
            "missed_event_risk": 0.0,
            "attribution_risk": 0.0,
        }

    loaded, rows = run_insepi_v7_artifact(npz, manifest, decision_fn=decision_fn)
    assert loaded.condition_count == 180
    assert len(calls) == 180
    assert len(rows) == 180
    assert {row.true_visit for row in rows} == {False, True}
