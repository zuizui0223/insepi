from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nuisance_score_distribution_diagnosis_is_prefrozen() -> None:
    p = json.loads((ROOT / "benchmarks/v14b_nuisance_score_distribution_diagnosis_protocol.json").read_text())
    assert p["status"] == "post-result-diagnostic-prefrozen-before-run"
    assert p["frozen_inputs"]["no_observer_change"] is True
    assert p["frozen_inputs"]["no_threshold_search"] is True
    assert p["frozen_inputs"]["threshold"] == 0.55
    assert len(p["frozen_inputs"]["validation_seeds"]) == 32
    rules = p["interpretation_rules_prefrozen"]
    assert "Pi5=1" in rules["coherent_stratum_definition_defect"]
    assert "spatial" in rules["spatial_representation_bottleneck"]
    assert "temporal" in rules["temporal_representation_bottleneck"]
    assert "both component" in rules["aggregation_bottleneck"]
