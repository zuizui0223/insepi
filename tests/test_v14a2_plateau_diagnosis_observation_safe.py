from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing.evaluation.plateau_diagnosis import (
    OBSERVATION_SAFE_FEATURE_NAMES,
    observation_safe_vector,
)
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalSignature

ROOT = Path(__file__).resolve().parents[1]


def make_signature(*, net: float, entry_exit: float) -> SpatiotemporalSignature:
    return SpatiotemporalSignature(
        net_displacement_over_path_length=net,
        focal_reference_correlation=0.2,
        spatial_coherence=0.3,
        spatial_structure_function=0.7,
        restoration_score=0.4,
        spectral_concentration=0.5,
        entry_exit_completeness=entry_exit,
        local_excess_motion_fraction=0.6,
        direct_target_signal_fraction=0.1,
        target_sampling_support=1.0,
        nuisance_sampling_support=1.0,
        nuisance_window_support=1.0,
    )


def test_observation_safe_vector_excludes_latent_topology() -> None:
    a = observation_safe_vector(make_signature(net=0.0, entry_exit=0.0))
    b = observation_safe_vector(make_signature(net=1.0, entry_exit=1.0))
    assert (a == b).all()
    assert "entry_exit_completeness" not in OBSERVATION_SAFE_FEATURE_NAMES
    assert "net_displacement_over_path_length" not in OBSERVATION_SAFE_FEATURE_NAMES


def test_corrected_protocol_preserves_first_audit_seeds_and_thresholds() -> None:
    old = json.loads((ROOT / "benchmarks/v14a2_plateau_diagnosis_protocol.json").read_text())
    new = json.loads((ROOT / "benchmarks/v14a2_plateau_diagnosis_observation_safe_protocol.json").read_text())
    assert new["status"] == "correction-prefrozen-before-first-observation-safe-run"
    assert new["seeds"] == old["seeds"]
    assert new["lda"] == old["lda"]
    assert "0.80" in new["interpretation_rules_prefrozen"]["representation_defect_candidate"]
    assert "0.60" in new["interpretation_rules_prefrozen"]["essential_ambiguity_candidate"]
    assert new["correction_only"]["v14a2_locked_surface_unchanged"] is True


def test_safe_feature_set_is_exactly_the_prefrozen_protocol_set() -> None:
    protocol = json.loads(
        (ROOT / "benchmarks/v14a2_plateau_diagnosis_observation_safe_protocol.json").read_text()
    )
    assert tuple(protocol["observation_safe_signature"]["included"]) == OBSERVATION_SAFE_FEATURE_NAMES
