from collections import Counter

from interaction_sensing.simulation.locked_benchmark_v5 import run_locked_v5
from interaction_sensing.simulation.locked_world_v5 import (
    CONTRACT_INSEPI_COMMIT,
    CONTRACT_POLLIPI_COMMIT,
)


def test_locked_v5_observer_uses_every_prevalence_world_without_tuning():
    rows = run_locked_v5(CONTRACT_POLLIPI_COMMIT, CONTRACT_INSEPI_COMMIT)
    assert len(rows) == 180
    assert Counter(row.prevalence_regime for row in rows) == {
        "rare": 60,
        "balanced": 60,
        "common": 60,
    }
    assert len({row.occlusion_threshold for row in rows}) == 1
