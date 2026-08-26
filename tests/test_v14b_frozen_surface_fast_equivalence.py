from __future__ import annotations

import importlib.util
from pathlib import Path

from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.target_observer_v14b import observe_target_v14b
from interaction_sensing.ternary_decision_v14b import decide_v14b
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalPoint, signature_for

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('fast_surface',ROOT/'scripts/run_v14b_frozen_ternary_phase_surface_fast.py')
mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)

THRESHOLD=4.33898869355123e-06
MIN_OBS=0.20


def canonical(point,regime,seed):
    sig=signature_for(point,regime,seed=seed)
    return decide_v14b(observe_target_v14b(sig),observe_nuisance_v14b(sig),nuisance_threshold=THRESHOLD,minimum_nuisance_observation_support=MIN_OBS)


def test_fast_decision_matches_canonical_across_frozen_semantic_strata():
    points=[
      SpatiotemporalPoint(0.1,0.01,0.0,0.0,0.01,2.0),
      SpatiotemporalPoint(1.0,1.0,0.1,0.1,1.0,8.0),
      SpatiotemporalPoint(3.1622776601683795,0.31622776601683794,0.31622776601683794,1.0,3.1622776601683795,16.0),
      SpatiotemporalPoint(10.0,100.0,3.1622776601683795,3.1622776601683795,100.0,32.0),
    ]
    for point in points:
      for regime in LatentRegime:
        for seed in (141001,141017,141032):
          a=canonical(point,regime,seed)
          b=mod._fast_decision(point,regime,seed,THRESHOLD,MIN_OBS)
          assert (a.state,a.reason,a.target_supported,a.nuisance_supported,a.dynamic_gate)==(b.state,b.reason,b.target_supported,b.nuisance_supported,b.dynamic_gate)
