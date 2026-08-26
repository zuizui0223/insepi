#!/usr/bin/env python3
from __future__ import annotations

import argparse, itertools, json
from pathlib import Path
from typing import Any
import numpy as np

from interaction_sensing.nuisance_observer_v14b import observe_nuisance_v14b
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalPoint, signature_for, temporally_resolved

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / 'benchmarks/v14b_nuisance_risk_calibration_protocol.json'
WORLD_PROTOCOL = ROOT / 'benchmarks/v14a2_spatiotemporal_world_protocol.json'


def _coordinates(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    sweep = world['focused_collision_sweep']
    values = [sweep['pi1_values'], sweep['pi2_values'], sweep['pi3_values'], sweep['pi4_values'], sweep['pi5_values'], sweep['pi6_values']]
    return [SpatiotemporalPoint(*(float(v) for v in c)) for c in itertools.product(*values)]


def _threshold(scores: np.ndarray, alpha: float) -> float:
    q = float(np.quantile(scores, 1.0-alpha, method='higher'))
    return float(np.nextafter(q, np.inf))


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    p = json.loads(protocol_path.read_text())
    world = json.loads(WORLD_PROTOCOL.read_text())
    frozen = world['operational_thresholds_prefrozen']
    min_samples = float(frozen['minimum_samples_per_process_timescale_for_resolved_slice'])
    min_timescales = float(frozen['minimum_process_timescales_per_window_for_resolved_slice'])
    min_obs = float(p['validation']['minimum_observation_support'])
    alpha = float(p['definition_correction']['alpha'])
    cal = [int(x) for x in p['calibration']['calibration_seeds']]
    val = [int(x) for x in p['validation']['validation_seeds']]

    points = [x for x in _coordinates(world) if temporally_resolved(x, minimum_samples=min_samples, minimum_timescales_per_window=min_timescales)]

    neg_cal=[]
    for point in points:
        for seed in cal:
            for regime in (LatentRegime.TARGET_ONLY, LatentRegime.TARGET_COUPLED):
                neg_cal.append(observe_nuisance_v14b(signature_for(point, regime, seed=seed)).nuisance_process_support)
    threshold = _threshold(np.asarray(neg_cal,float), alpha)

    target_only=[]; target_coupled=[]; nuisance=[]; coverage={}
    for point in points:
        key=f'pi5={point.pi5:.12g}'
        coverage.setdefault(key,[0,0])
        for seed in val:
            o=observe_nuisance_v14b(signature_for(point, LatentRegime.NUISANCE_ONLY, seed=seed))
            n=observe_nuisance_v14b(signature_for(point, LatentRegime.TARGET_ONLY, seed=seed))
            c=observe_nuisance_v14b(signature_for(point, LatentRegime.TARGET_COUPLED, seed=seed))
            target_only.append(n.nuisance_process_support >= threshold and n.nuisance_observation_support >= min_obs)
            target_coupled.append(c.nuisance_process_support >= threshold and c.nuisance_observation_support >= min_obs)
            supported=(o.nuisance_process_support >= threshold and o.nuisance_observation_support >= min_obs)
            nuisance.append(supported)
            coverage[key][0]+=int(supported); coverage[key][1]+=1

    fpr_to=float(np.mean(target_only)); fpr_tc=float(np.mean(target_coupled)); cov=float(np.mean(nuisance))
    checks={
      'heldout_target_only_fpr': fpr_to <= float(p['validation']['heldout_target_only_fpr_max']),
      'heldout_target_coupled_fpr': fpr_tc <= float(p['validation']['heldout_target_coupled_fpr_max']),
    }
    contradictions={}
    if not checks['heldout_target_only_fpr']: contradictions['false_nuisance_attribution_target_only']=1
    if not checks['heldout_target_coupled_fpr']: contradictions['false_nuisance_attribution_target_coupled']=1
    result={
      'schema':'insepi-v14b-nuisance-risk-calibration-result-v1',
      'alpha':alpha,
      'calibrated_threshold':threshold,
      'heldout_target_only_fpr':fpr_to,
      'heldout_target_coupled_fpr':fpr_tc,
      'heldout_nuisance_coverage':cov,
      'nuisance_coverage_by_pi5':{k:v[0]/v[1] for k,v in sorted(coverage.items())},
      'checks':checks,
      'contradiction_types_observed':contradictions,
      'new_contradiction_type_count':len(contradictions),
      'nuisance_decision_contract_freezable':all(checks.values()) and not contradictions,
      'target_observer_modified':False,
      'nuisance_feature_representation_modified':False,
      'claim_boundary':p['claim_boundary']
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--protocol',default=str(DEFAULT_PROTOCOL)); ap.add_argument('--output',default='v14b_nuisance_risk_output/result.json'); a=ap.parse_args()
    print(json.dumps(run(Path(a.protocol),Path(a.output)),indent=2,sort_keys=True))
