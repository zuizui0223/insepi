from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from interaction_sensing.evaluation.plateau_diagnosis import auc, fit_lda


ROOT = Path(__file__).resolve().parents[1]


def test_auc_handles_order_and_ties() -> None:
    assert auc(np.array([2.0, 3.0]), np.array([0.0, 1.0])) == 1.0
    assert auc(np.array([0.0, 1.0]), np.array([2.0, 3.0])) == 0.0
    assert auc(np.array([1.0, 1.0]), np.array([1.0, 1.0])) == 0.5


def test_fixed_lda_separates_simple_balanced_clouds() -> None:
    x0 = np.array([[0.0, 0.0], [0.1, -0.1], [-0.1, 0.1], [0.05, 0.0]])
    x1 = np.array([[2.0, 2.0], [2.1, 1.9], [1.9, 2.1], [2.0, 2.05]])
    w = fit_lda(x0, x1, 0.001)
    assert auc(x1 @ w, x0 @ w) == 1.0


def test_plateau_protocol_is_post_result_and_does_not_rewrite_v14a2() -> None:
    protocol = json.loads(
        (ROOT / "benchmarks/v14a2_plateau_diagnosis_protocol.json").read_text(encoding="utf-8")
    )
    assert protocol["status"] == "post-result-audit-prefrozen-before-diagnostic-run"
    source = protocol["source_locked_result"]
    assert source["workflow_run_id"] == 32921177706
    assert source["registered_q3_supported"] is False
    assert protocol["lda"]["no_hyperparameter_search"] is True
    assert len(protocol["seeds"]["train"]) == 32
    assert len(protocol["seeds"]["heldout"]) == 32
    assert set(protocol["seeds"]["train"]).isdisjoint(protocol["seeds"]["heldout"])
    rules = protocol["interpretation_rules_prefrozen"]
    assert "0.80" in rules["representation_defect_candidate"]
    assert "0.60" in rules["essential_ambiguity_candidate"]
    assert "do not authorize changing V14a2" in rules["no_retuning"]
