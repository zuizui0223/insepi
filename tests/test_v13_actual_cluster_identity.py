from __future__ import annotations

import json
from pathlib import Path

from interaction_sensing import physical_evaluation_v13 as v13e

ROOT = Path(__file__).resolve().parents[1]


def test_v13_heldout_truth_uses_actual_capture_cluster_fields() -> None:
    fields = tuple(v13e.HeldoutTruth.__dataclass_fields__)
    assert fields == (
        "block_id",
        "treatment_class",
        "recording_date_local",
        "physical_scene_code",
    )
    assert "day_id" not in fields
    assert "scene_id" not in fields


def test_v13_protocol_forbids_synthetic_randomisation_slots_for_cluster_bootstrap() -> None:
    protocol = json.loads((ROOT / "benchmarks/v13_physical_intervention_protocol.json").read_text())
    physical = protocol["actual_physical_cluster_contract"]
    analysis = protocol["analysis"]
    assert physical["cluster_identity_source"] == "completed capture log recording_date_local x physical_scene_code"
    assert physical["randomisation_day_scene_slots_used_for_final_uncertainty"] is False
    assert physical["blocks_per_day_x_scene_cluster"] == 12
    assert physical["replicates_per_treatment_class_per_day_x_scene_cluster"] == 3
    assert analysis["synthetic_randomisation_day_scene_slots_used_for_cluster_bootstrap"] is False
    assert analysis["required_blocks_per_heldout_cluster"] == 12
    assert analysis["required_replicates_per_treatment_per_heldout_cluster"] == 3
