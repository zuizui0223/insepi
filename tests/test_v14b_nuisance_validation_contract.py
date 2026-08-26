from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nuisance_validation_contract_is_prefrozen() -> None:
    p = json.loads((ROOT / "benchmarks/v14b_nuisance_observer_process_scale_protocol.json").read_text())
    assert p["schema"] == "insepi-v14b-nuisance-observer-process-scale-protocol-v1"
    assert p["status"] == "nuisance-side-prefreeze-before-validation"
    assert p["parent_target_freeze"]["target_side_type_saturated"] is True
    assert p["alternating_freeze"]["modifiable_observer"] == "nuisance"
    assert p["alternating_freeze"]["frozen_observer"] == "target"
    assert p["problem"]["prior_nuisance_auc"] == 1.0
    assert p["problem"]["prior_recall_at_0_55"] == 0.015625
    expected = p["prefrozen_expected_invariants"]
    assert expected["nuisance_vs_target_only_auc_min"] == 0.90
    assert expected["nuisance_vs_target_coupled_auc_min"] == 0.90
    assert expected["coherent_nuisance_recall_at_0_55_min"] == 0.80
    assert expected["target_only_false_positive_at_0_55_max"] == 0.05
    assert expected["target_coupled_false_positive_at_0_55_max"] == 0.05
