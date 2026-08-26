from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APPARATUS = ROOT / "benchmarks/v13_physical_apparatus_freeze.json"


def _load() -> dict[str, object]:
    return json.loads(APPARATUS.read_text(encoding="utf-8"))


def test_v13_apparatus_is_single_pre_field_recipe() -> None:
    spec = _load()
    assert spec["schema"] == "interaction-sensing-v13-physical-apparatus-freeze-v1"
    assert spec["status"] == "pre-field-frozen-before-any-physical-acquisition"
    assert spec["standard_event_proxy"]["diameter_mm"] == 100
    assert spec["standard_event_proxy"]["diameter_tolerance_mm"] == 2
    assert spec["common_geometry"]["camera_to_target_plane_mm"] == 1000
    assert spec["common_geometry"]["camera_to_target_tolerance_mm"] == 20


def test_v13_development_and_heldout_mechanisms_are_distinct_and_fixed() -> None:
    spec = _load()
    dev = spec["development_treatments"]
    held = spec["heldout_treatments"]
    assert dev["event_side"]["subtype"] == "local_target_contrast_attenuation"
    assert held["event_side"]["subtype"] == "local_target_scale_shift"
    assert dev["nuisance_side"]["subtype"] == "fan_driven_background_motion"
    assert held["nuisance_side"]["subtype"] == "moving_shadow"
    assert dev["shared_optical"]["subtype"] == "partial_optical_occlusion"
    assert held["shared_optical"]["subtype"] == "full_aperture_diffusion_filter"
    assert held["event_side"]["diameter_mm"] == 50


def test_v13_apparatus_tolerances_are_numeric_and_non_degenerate() -> None:
    spec = _load()
    dev = spec["development_treatments"]
    held = spec["heldout_treatments"]
    assert 0 < dev["nuisance_side"]["air_speed_tolerance_m_per_s"] < dev["nuisance_side"]["air_speed_m_per_s_at_background"]
    assert 0 < dev["shared_optical"]["occlusion_fraction_tolerance"] < dev["shared_optical"]["occluded_canonical_frame_width_fraction"] < 1
    assert 0 < held["nuisance_side"]["shadow_cycle_tolerance_hz"] < held["nuisance_side"]["shadow_cycle_hz"]
    assert 0 < held["nuisance_side"]["trough_illuminance_fraction_of_unshadowed"] < 1
    assert 0 < held["shared_optical"]["visible_transmittance_fraction"] < 1
    assert 0 < held["shared_optical"]["transmittance_tolerance"] < held["shared_optical"]["visible_transmittance_fraction"]


def test_v13_apparatus_calibration_cannot_use_observer_outputs() -> None:
    spec = _load()
    measurement = spec["physical_measurement_rules"]
    assert measurement["measurements_are_made_without_observer_outputs"] is True
    forbidden = " ".join(spec["forbidden_adaptations_after_acquisition_begins"]).lower()
    assert "pollipi" in forbidden
    assert "insepi" in forbidden
    assert "glare" in forbidden


def test_v13_active_interventions_remain_non_cumulative() -> None:
    spec = _load()
    rule = spec["non_cumulative_rule"]
    assert rule == {
        "all_active_phases_start_from_the_same_latent_placebo_treatment_state": True,
        "restore_latent_baseline_during_washout": True,
        "abort_block_if_baseline_cannot_be_restored": True,
    }
