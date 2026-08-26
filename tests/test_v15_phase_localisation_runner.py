from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/locate_v15_on_frozen_phase_surface.py"
SPEC = importlib.util.spec_from_file_location("phase_localisation_runner", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def _payload() -> dict[str, object]:
    return {
        "schema": "insepi-v15-empirical-phase-measurements-v1",
        "measurement_profile_sha256": "b" * 64,
        "units": {"time": "s", "amplitude": "px", "length": "px"},
        "blocks": [
            {
                "block_id": "exact",
                "observation_window_duration": 10.0,
                "target_process_timescale": 1.0,
                "nuisance_or_coupled_response_timescale": 1.0,
                "direct_target_motion_amplitude": 1.0,
                "reference_nuisance_motion_amplitude": 1.0,
                "target_driven_local_response_amplitude": 1.0,
                "nuisance_spatial_correlation_length": 1.0,
                "target_spatial_support_width": 1.0,
                "sampling_frequency": 8.0,
            },
            {
                "block_id": "outside",
                "observation_window_duration": 0.01,
                "target_process_timescale": 1.0,
                "nuisance_or_coupled_response_timescale": 1.0,
                "direct_target_motion_amplitude": 1.0,
                "reference_nuisance_motion_amplitude": 1.0,
                "target_driven_local_response_amplitude": 1.0,
                "nuisance_spatial_correlation_length": 1.0,
                "target_spatial_support_width": 1.0,
                "sampling_frequency": 64.0,
            },
        ],
    }


def test_runner_writes_auditable_fail_closed_locations(tmp_path: Path) -> None:
    input_path = tmp_path / "measurements.json"
    output_path = tmp_path / "locations.json"
    input_path.write_text(json.dumps(_payload()), encoding="utf-8")

    result = RUNNER.run(input_path, output_path)

    assert result == json.loads(output_path.read_text(encoding="utf-8"))
    assert result["location_counts"] == {
        "exact": 1,
        "bracketed": 0,
        "out_of_support": 1,
    }
    assert result["surface_interpolation_permitted"] is False
    assert result["surface_extrapolation_permitted"] is False
    assert result["observer_or_threshold_changed"] is False
    assert result["frozen_surface_values_read"] is False
    assert result["locations"][1]["out_of_support_axes"] == ["pi1", "pi6"]


def test_runner_rejects_duplicate_block_ids(tmp_path: Path) -> None:
    payload = _payload()
    blocks = payload["blocks"]
    assert isinstance(blocks, list)
    blocks[1]["block_id"] = blocks[0]["block_id"]
    input_path = tmp_path / "duplicates.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="block_id values must be unique"):
        RUNNER.run(input_path, tmp_path / "unused.json")


def test_runner_requires_frozen_measurement_profile_hash(tmp_path: Path) -> None:
    payload = _payload()
    payload["measurement_profile_sha256"] = "not-frozen"
    input_path = tmp_path / "bad-profile.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="64 lowercase hex"):
        RUNNER.run(input_path, tmp_path / "unused.json")
