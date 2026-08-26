from __future__ import annotations

import inspect
import json
from pathlib import Path

from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalSignature
from interaction_sensing.target_observer_v14b import (
    TargetRouteState,
    observe_target_v14b,
)

ROOT = Path(__file__).resolve().parents[1]


def signature(*, direct: float, local: float) -> SpatiotemporalSignature:
    return SpatiotemporalSignature(
        net_displacement_over_path_length=0.0,
        focal_reference_correlation=0.4,
        spatial_coherence=0.5,
        spatial_structure_function=0.5,
        restoration_score=0.5,
        spectral_concentration=0.5,
        entry_exit_completeness=0.0,
        local_excess_motion_fraction=local,
        direct_target_signal_fraction=direct,
        target_sampling_support=1.0,
        nuisance_sampling_support=1.0,
        nuisance_window_support=1.0,
    )


def test_direct_evidence_is_preserved_as_positive_target_route() -> None:
    obs = observe_target_v14b(signature(direct=0.1, local=0.0))
    assert obs.target_supported is True
    assert obs.unresolved_indirect_only is False
    assert obs.route_state is TargetRouteState.DIRECT_SUPPORTED


def test_indirect_only_response_is_retained_but_not_promoted() -> None:
    obs = observe_target_v14b(signature(direct=0.0, local=0.4))
    assert obs.target_supported is False
    assert obs.unresolved_indirect_only is True
    assert obs.route_state is TargetRouteState.INDIRECT_UNATTRIBUTED


def test_no_target_or_local_response_remains_none() -> None:
    obs = observe_target_v14b(signature(direct=0.0, local=0.0))
    assert obs.target_supported is False
    assert obs.unresolved_indirect_only is False
    assert obs.route_state is TargetRouteState.NONE


def test_target_observer_does_not_consume_nuisance_score_or_route() -> None:
    source = inspect.getsource(observe_target_v14b)
    assert "route_scores" not in source
    assert "nuisance_support" not in source
    assert "nuisance_high" not in source


def test_protocol_freezes_nuisance_and_forbids_indirect_forcing() -> None:
    protocol = json.loads((ROOT / "benchmarks/v14b_target_observer_direct_first_protocol.json").read_text())
    assert protocol["alternating_freeze"]["modifiable_observer"] == "target"
    assert protocol["alternating_freeze"]["frozen_observer"] == "nuisance"
    assert protocol["target_representation"]["no_lda_import"] is True
    assert "never promote" in protocol["target_representation"]["indirect_only"]
    assert protocol["validation_rules"]["no_training"] is True
