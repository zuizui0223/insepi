#!/usr/bin/env python3
"""Locate empirical V15 blocks on the frozen V14b coordinate grid."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from interaction_sensing.phase_localisation import (
    FROZEN_V14B_PHASE_SURFACE_SHA256,
    EmpiricalPhaseMeasurements,
    PhaseMeasurementProvenance,
    localise_on_frozen_v14b_grid,
)

INPUT_SCHEMA = "insepi-v15-empirical-phase-measurements-v1"
OUTPUT_SCHEMA = "insepi-v15-frozen-phase-localisation-v1"
MEASUREMENT_FIELDS = (
    "observation_window_duration",
    "target_process_timescale",
    "nuisance_or_coupled_response_timescale",
    "direct_target_motion_amplitude",
    "reference_nuisance_motion_amplitude",
    "target_driven_local_response_amplitude",
    "nuisance_spatial_correlation_length",
    "target_spatial_support_width",
    "sampling_frequency",
)


def _load_input(input_path: Path) -> tuple[dict[str, Any], str]:
    source_bytes = input_path.read_bytes()
    try:
        payload = json.loads(source_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("input must be UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise TypeError("input JSON root must be an object")
    return payload, hashlib.sha256(source_bytes).hexdigest()


def _require_object(parent: dict[str, Any], name: str) -> dict[str, Any]:
    value = parent.get(name)
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be an object")
    return value


def _require_string(parent: dict[str, Any], name: str) -> str:
    value = parent.get(name)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    return value


def _measurements_from_block(
    block: dict[str, Any],
    *,
    profile_sha256: str,
    units: dict[str, Any],
) -> EmpiricalPhaseMeasurements:
    missing = [field for field in MEASUREMENT_FIELDS if field not in block]
    if missing:
        raise ValueError(f"measurement block is missing fields: {', '.join(missing)}")
    provenance = PhaseMeasurementProvenance(
        block_id=_require_string(block, "block_id"),
        measurement_profile_sha256=profile_sha256,
        time_unit=_require_string(units, "time"),
        amplitude_unit=_require_string(units, "amplitude"),
        length_unit=_require_string(units, "length"),
    )
    return EmpiricalPhaseMeasurements(
        provenance=provenance,
        **{field: block[field] for field in MEASUREMENT_FIELDS},
    )


def run(input_path: Path, output_path: Path) -> dict[str, Any]:
    payload, source_sha256 = _load_input(input_path)
    if payload.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"input schema must be {INPUT_SCHEMA}")

    profile_sha256 = _require_string(payload, "measurement_profile_sha256")
    units = _require_object(payload, "units")
    raw_blocks = payload.get("blocks")
    if not isinstance(raw_blocks, list) or not raw_blocks:
        raise ValueError("blocks must be a non-empty array")
    if not all(isinstance(block, dict) for block in raw_blocks):
        raise ValueError("every measurement block must be an object")

    measurements = [
        _measurements_from_block(
            block,
            profile_sha256=profile_sha256,
            units=units,
        )
        for block in raw_blocks
    ]
    block_ids = [measurement.provenance.block_id for measurement in measurements]
    if len(set(block_ids)) != len(block_ids):
        raise ValueError("block_id values must be unique")

    locations = [localise_on_frozen_v14b_grid(item) for item in measurements]
    status_counts = Counter(
        "exact"
        if location.exact_grid_coordinate
        else "bracketed"
        if location.within_frozen_support
        else "out_of_support"
        for location in locations
    )
    result: dict[str, Any] = {
        "schema": OUTPUT_SCHEMA,
        "source_measurements_sha256": source_sha256,
        "measurement_profile_sha256": profile_sha256,
        "frozen_v14b_phase_surface_sha256": FROZEN_V14B_PHASE_SURFACE_SHA256,
        "block_count": len(locations),
        "location_counts": {
            "exact": status_counts["exact"],
            "bracketed": status_counts["bracketed"],
            "out_of_support": status_counts["out_of_support"],
        },
        "surface_interpolation_permitted": False,
        "surface_extrapolation_permitted": False,
        "observer_or_threshold_changed": False,
        "frozen_surface_values_read": False,
        "locations": [location.to_dict() for location in locations],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map raw V15 measurements to the frozen V14b Pi grid without interpolation."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.input, args.output)
    print(
        json.dumps(
            {key: value for key, value in result.items() if key != "locations"},
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
