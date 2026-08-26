from __future__ import annotations

import inspect
import json
from pathlib import Path

from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalSignature

ROOT = Path(__file__).resolve().parents[1]


def signature(*, spatial: float, restoration: float, spectral: float, sampling: float, window: float) -> SpatiotemporalSignature:
    return SpatiotemporalSignature(
        net_displacement_over_path_length=0.0,
        focal_reference_correlation=spatial,
        spatial_coherence=spatial,
        spatial_structure_function=1.0 - spatial,
        restoration_score=restoration,
        spectral_concentration=spectral,
        entry_exit_completeness=0.0,
        local_excess_motion_fraction=0.0,
        direct_target_signal_fraction=0.0,
        target_sampling_support=1.0,
        nuisance_sampling_support=sampling,
        nuisance_window_support=window,
    )


def test_process_evidence_is_separate_from_observation_support() -> None:
    well = observe_nuisance_v14b(signature(spatial=0.81, restoration=0.64, spectral=0.2, sampling=1.0, window=1.0))
    poor = observe_nuisance_v14b(signature(spatial=0.81, restoration=0.64, spectral=0.2, sampling=0.1, window=0.2))
    assert well.nuisance_process_support == poor.nuisance_process_support
    assert well.nuisance_observation_support == 1.0
    assert poor.nuisance_observation_support == 0.1


def test_process_support_requires_both_spatial_and_temporal_positive_properties() -> None:
    no_spatial = observe_nuisance_v14b(signature(spatial=0.0, restoration=1.0, spectral=1.0, sampling=1.0, window=1.0))
    no_temporal = observe_nuisance_v14b(signature(spatial=1.0, restoration=0.0, spectral=0.0, sampling=1.0, window=1.0))
    assert no_spatial.nuisance_process_support == 0.0
    assert no_temporal.nuisance_process_support == 0.0


def test_nuisance_observer_does_not_consume_target_observer_output() -> None:
    source = inspect.getsource(observe_nuisance_v14b)
    assert "observe_target_v14b" not in source
    assert "target_supported" not in source
    assert "direct_target_signal_fraction" not in source


def test_protocol_freezes_target_and_uses_fresh_validation_seeds() -> None:
    protocol = json.loads((ROOT / "benchmarks/v14b_nuisance_observer_process_scale_protocol.json").read_text())
    assert protocol["alternating_freeze"]["modifiable_observer"] == "nuisance"
    assert protocol["alternating_freeze"]["frozen_observer"] == "target"
    assert protocol["validation_rules"]["no_training"] is True
    seeds = protocol["validation_rules"]["validation_seeds"]
    assert len(seeds) == 32
    assert min(seeds) == 91001 and max(seeds) == 91032
    assert protocol["representation"]["observation_support"].endswith("retained separately")
