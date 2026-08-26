#!/usr/bin/env python3
from __future__ import annotations

import argparse, itertools, json
from pathlib import Path
from typing import Any
import numpy as np

from interaction_sensing.evaluation.risk_calibration import upper_negative_quantile_threshold
from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalPoint, signature_for, temporally_resolved

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / 'benchmarks/v14b_nuisance_familywise_risk_protocol.json'
WORLD_PROTOCOL = ROOT / 'benchmarks/v14a2_spatiotemporal_world_protocol.json'


def _coordinates(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep=world['focused_collision_sweep']
    values=[sweep['pi1_values'],sweep['pi2_values'],sweep['pi3_values'],sweep['pi4_values'],sweep['pi5_values'],sweep['pi6_values']]
    return [SpatiotemporalPoint(*(float(v) for v in c)) for c in itertools.product(*values)]


def _score(point: SpatiotemporalPoint, regime: LatentRegime, seed: int) -> tuple[float,float]:
    obs=observe_nuisance_v14b(signature_for(point, regime, seed=seed))
    return obs.nuisance_process_support, obs.nuisance_observation_support


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    p=json.loads(protocol_path.read_text())
    world=json.loads(WORLD_PROTOCOL.read_text())
    frozen=world['operational_thresholds_prefrozen']
    min_samples=float(frozen['minimum_samples_per_process_timescale_for_resolved_slice'])
    min_timescales=float(frozen['minimum_process_timescales_per_window_for_resolved_slice'])
    alpha=float(p['definition_correction']['alpha'])
    min_obs=float(p['validation']['minimum_observation_support'])
    cal=[int(x) for x in p['calibration']['calibration_seeds']]
    val=[int(x) for x in p['validation']['validation_seeds']]
    points=[x for x in _coordinates(world) if temporally_resolved(x, minimum_samples=min_samples, minimum_timescales_per_window=min_timescales)]

    family_regimes={
      'target_only': LatentRegime.TARGET_ONLY,
      'target_nuisance_coupled': LatentRegime.TARGET_COUPLED,
    }
    family_thresholds={}
    for name,regime in family_regimes.items():
        scores=[]
        for point in points:
            for seed in cal:
                s,_=_score(point,regime,seed); scores.append(s)
        family_thresholds[name]=upper_negative_quantile_threshold(np.asarray(scores,float),alpha)
    threshold=max(family_thresholds.values())

    negatives={name:[] for name in family_regimes}
    nuisance=[]; coverage={}
    for point in points:
        key=f'pi5={point.pi5:.12g}'
        coverage.setdefault(key,[0,0])
        for seed in val:
            for name,regime in family_regimes.items():
                s,o=_score(point,regime,seed)
                negatives[name].append(s>=threshold and o>=min_obs)
            s,o=_score(point,LatentRegime.NUISANCE_ONLY,seed)
            supported=s>=threshold and o>=min_obs
            nuisance.append(supported); coverage[key][0]+=int(supported); coverage[key][1]+=1

    fprs={name:float(np.mean(vals)) for name,vals in negatives.items()}
    limits={
      'target_only':float(p['validation']['heldout_target_only_fpr_max']),
      'target_nuisance_coupled':float(p['validation']['heldout_target_coupled_fpr_max']),
    }
    checks={name:fprs[name] <= limits[name] for name in family_regimes}
    contradictions={f'false_nuisance_attribution_{name}':1 for name,ok in checks.items() if not ok}
    result={
      'schema':'insepi-v14b-nuisance-familywise-risk-result-v1',
      'alpha':alpha,
      'family_calibration_thresholds':family_thresholds,
      'operational_threshold':threshold,
      'heldout_family_fpr':fprs,
      'heldout_nuisance_coverage':float(np.mean(nuisance)),
      'nuisance_coverage_by_pi5':{k:v[0]/v[1] for k,v in sorted(coverage.items())},
      'checks':checks,
      'contradiction_types_observed':contradictions,
      'new_contradiction_type_count':len(contradictions),
      'nuisance_decision_contract_freezable':all(checks.values()) and not contradictions,
      'target_observer_modified':False,
      'nuisance_feature_representation_modified':False,
      'claim_boundary':p['claim_boundary']
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',default=str(DEFAULT_PROTOCOL)); ap.add_argument('--output',default='v14b_nuisance_familywise_output/result.json'); a=ap.parse_args()
    print(json.dumps(run(Path(a.protocol),Path(a.output)),indent=2,sort_keys=True))
