from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_familywise_protocol_is_prefrozen_and_disjoint() -> None:
    p=json.loads((ROOT/'benchmarks/v14b_nuisance_familywise_risk_protocol.json').read_text())
    assert p['definition_correction']['alpha']==0.05
    assert p['definition_correction']['observer_features_changed'] is False
    assert p['definition_correction']['observer_aggregation_changed'] is False
    assert p['definition_correction']['target_observer_changed'] is False
    assert p['definition_correction']['no_positive_worlds_in_calibration'] is True
    assert p['definition_correction']['no_threshold_search'] is True
    assert set(p['calibration']['calibration_seeds']).isdisjoint(p['validation']['validation_seeds'])
    assert len(p['calibration']['calibration_seeds'])==32
    assert len(p['validation']['validation_seeds'])==32
    assert p['validation']['nuisance_recall_is_not_a_freeze_gate'] is True
    assert 'maximum family boundary' in p['definition_correction']['single_threshold_rule']
