from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing.development.pi2_negative_diagnosis import diagnose_pi2_negative


ROOT = Path(__file__).resolve().parents[1]


def protocol(*, include_spatial_axis: bool = False) -> dict:
    coordinates = {
        "pi1": "observation window / target timescale",
        "pi2": "nuisance timescale / target timescale",
        "pi3": "direct target amplitude / nuisance amplitude",
        "pi4": "coupled response amplitude / nuisance amplitude",
    }
    if include_spatial_axis:
        coordinates["pi5"] = "nuisance spatial correlation length / target spatial support width"
    return {
        "dimensionless_coordinates": coordinates,
        "sweep": {
            "pi2_values": [0.01, 1.0, 100.0],
            "pi3_values": [0.0, 0.1, 0.31622776601683794, 1.0],
            "pi4_values": [0.0, 0.1, 0.31622776601683794, 1.0],
        },
        "process_model": {
            "exogenous_nuisance": "restorative spatially coherent oscillatory scene process",
            "neighbor_channel": "receives coherent exogenous nuisance but not target coupling",
        },
    }


def row(pi2: float, regime: str, ambiguity: float, *, support: float = 0.8) -> dict:
    return {
        "pi1": 1.0,
        "pi2": pi2,
        "pi3": 0.1,
        "pi4": 0.1,
        "regime": regime,
        "essential_ambiguity_rate": ambiguity,
        "information_absence_rate": 0.0,
        "mean_observation_support": support,
        "mean_identifiability_margin": 1.0 - ambiguity,
    }


def test_negative_p3_with_fixed_spatial_separator_requires_new_generation() -> None:
    rows = [
        row(0.01, "target_nuisance_superposed", 0.4),
        row(1.0, "target_nuisance_superposed", 0.2),
        row(100.0, "target_nuisance_superposed", 0.4),
        row(0.01, "target_nuisance_coupled", 0.3),
        row(1.0, "target_nuisance_coupled", 0.1),
        row(100.0, "target_nuisance_coupled", 0.3),
    ]
    result = diagnose_pi2_negative(rows, protocol())
    assert result.registered_prediction_supported is False
    assert result.observable_slice_supports_prediction is False
    assert result.mixed_slice_supports_prediction is False
    assert result.spatial_separation_coordinate_present is False
    assert result.fixed_neighbor_spatial_separator is True
    assert result.next_generation_required is True
    assert "spatial_separation" in result.diagnosis
    assert result.recommended_dimensionless_axis.startswith("Pi5 =")


def test_diagnosis_does_not_blame_fixed_spatial_axis_when_axis_is_swept() -> None:
    rows = [
        row(0.01, "target_nuisance_superposed", 0.4),
        row(1.0, "target_nuisance_superposed", 0.2),
        row(100.0, "target_nuisance_superposed", 0.4),
    ]
    result = diagnose_pi2_negative(rows, protocol(include_spatial_axis=True))
    assert result.registered_prediction_supported is False
    assert result.spatial_separation_coordinate_present is True
    assert "without_a_single_structural_explanation" in result.diagnosis


def test_canonical_post_result_registry_keeps_p3_negative() -> None:
    payload = json.loads(
        (ROOT / "benchmarks/v14a_p3_negative_diagnosis.json").read_text(encoding="utf-8")
    )
    diagnosis = payload["diagnosis"]
    assert payload["status"] == "post-result-diagnostic-does-not-alter-v14a"
    assert diagnosis["registered_prediction_supported"] is False
    assert diagnosis["observable_slice_supports_prediction"] is False
    assert diagnosis["mixed_slice_supports_prediction"] is False
    assert diagnosis["spatial_separation_coordinate_present"] is False
    assert diagnosis["fixed_neighbor_spatial_separator"] is True
    assert payload["next_generation"]["required"] is True
