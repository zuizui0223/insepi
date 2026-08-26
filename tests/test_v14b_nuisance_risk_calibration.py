from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from scripts.run_v14b_nuisance_risk_calibration import _threshold

ROOT=Path(__file__).resolve().parents[1]


def test_threshold_is_strictly_above_negative_quantile() -> None:
    scores=np.array([0.0,0.1,0.2,0.3,0.4])
    t=_threshold(scores,0.20)
    assert t > float(np.quantile(scores,0.80,method='higher'))


def test_protocol_uses_disjoint_calibration_and_validation_seeds() -> None:
    p=json.loads((ROOT/'benchmarks/v14b_nuisance_risk_calibration_protocol.json').read_text())
    assert p['definition_correction']['alpha']==0.05
    assert p['definition_correction']['observer_features_changed'] is False
    assert p['definition_correction']['observer_aggregation_changed'] is False
    assert p['calibration']['no_threshold_search'] is True
    assert p['validation']['nuisance_recall_is_not_a_freeze_gate'] is True
    assert set(p['calibration']['calibration_seeds']).isdisjoint(p['validation']['validation_seeds'])
    assert len(p['calibration']['calibration_seeds'])==32
    assert len(p['validation']['validation_seeds'])==32
