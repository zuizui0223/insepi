#!/usr/bin/env python3
"""Semantics-preserving fast runner for the frozen V14b ternary phase surface.

The final decision consumes only (1) whether direct target evidence is nonzero,
(2) local scene response, and (3) the frozen nuisance observer outputs.  Direct
actor amplitude never enters the nuisance scene, and Pi4 is irrelevant in
non-coupled regimes.  We therefore cache observation-equivalent scene signatures
without changing any frozen observer, threshold, seed, coordinate, or decision.
"""
from __future__ import annotations

import argparse, itertools, json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from interaction_sensing.nuisance_observer_v14b import NuisanceObservationV14b, observe_nuisance_v14b
from interaction_sensing.target_observer_v14b import TargetObservationV14b, TargetRouteState
from interaction_sensing.ternary_decision_v14b import decide_v14b, TernaryState, UndeterminedReason
from interaction_sensing.simulation.dimensionless_observability_v14 import LatentRegime
from interaction_sensing.simulation.dimensionless_observability_v14a2 import SpatiotemporalPoint, signature_for, truth

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_protocol.json"
WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"


def _points(world: dict[str, Any]) -> list[SpatiotemporalPoint]:
    g = world["coarse_sweep"]
    vals = [g["pi1_values"], g["pi2_values"], g["pi3_values"], g["pi4_values"], g["pi5_values"], g["pi6_values"]]
    return [SpatiotemporalPoint(*(float(v) for v in x)) for x in itertools.product(*vals)]


def _target_from_scene(local: float, direct_present: bool) -> TargetObservationV14b:
    if direct_present and local > 0.0:
        state = TargetRouteState.DIRECT_WITH_LOCAL_RESPONSE
    elif direct_present:
        state = TargetRouteState.DIRECT_SUPPORTED
    elif local > 0.0:
        state = TargetRouteState.INDIRECT_UNATTRIBUTED
    else:
        state = TargetRouteState.NONE
    return TargetObservationV14b(
        direct_signal_fraction=1.0 if direct_present else 0.0,
        local_response_fraction=float(local),
        route_state=state,
        target_supported=direct_present,
        unresolved_indirect_only=(not direct_present and local > 0.0),
    )


@lru_cache(maxsize=None)
def _scene_observation(
    pi1: float, pi2: float, pi4: float, pi5: float, pi6: float,
    scene_kind: str, seed: int,
) -> tuple[float, NuisanceObservationV14b]:
    """Return observation-equivalent local response and nuisance observation.

    `scene_kind` strips dimensions that provably cannot affect the frozen final
    decision:
    - nuisance: exogenous nuisance only (also scene-equivalent to T+N superposed
      when direct actor amplitude is removed);
    - coupled: target-driven local response only;
    - nuisance_coupled: exogenous nuisance plus target-driven response.
    Pi3 is always zero here because it is a separate direct-actor channel.
    """
    if scene_kind == "nuisance":
        regime = LatentRegime.NUISANCE_ONLY
        pi4_eff = 0.0
    elif scene_kind == "coupled":
        regime = LatentRegime.TARGET_COUPLED
        pi4_eff = pi4
        pi5 = 1.0  # no exogenous nuisance exists, so Pi5 cannot affect the scene
        seed = 0   # deterministic without exogenous nuisance
    elif scene_kind == "nuisance_coupled":
        regime = LatentRegime.TARGET_NUISANCE_COUPLED
        pi4_eff = pi4
    else:
        raise ValueError(scene_kind)
    point = SpatiotemporalPoint(pi1, pi2, 0.0, pi4_eff, pi5, pi6)
    sig = signature_for(point, regime, seed=seed)
    return float(sig.local_excess_motion_fraction), observe_nuisance_v14b(sig)


def _fast_decision(point: SpatiotemporalPoint, regime: LatentRegime, seed: int, threshold: float, min_obs: float):
    t_truth, n_truth, coupling_truth = truth(regime)
    direct_present = bool(t_truth and point.pi3 > 0.0)

    if regime is LatentRegime.BASELINE:
        local = 0.0
        nobs = NuisanceObservationV14b(0.0, 0.0, 0.0, 0.0)
    elif regime is LatentRegime.TARGET_ONLY:
        local = 0.0
        nobs = NuisanceObservationV14b(0.0, 0.0, 0.0, 0.0)
    elif regime in (LatentRegime.NUISANCE_ONLY, LatentRegime.TARGET_NUISANCE_SUPERPOSED):
        local, nobs = _scene_observation(point.pi1, point.pi2, 0.0, point.pi5, point.pi6, "nuisance", seed)
    elif regime is LatentRegime.TARGET_COUPLED:
        local, nobs = _scene_observation(point.pi1, point.pi2, point.pi4, 1.0, point.pi6, "coupled", 0)
    elif regime is LatentRegime.TARGET_NUISANCE_COUPLED:
        local, nobs = _scene_observation(point.pi1, point.pi2, point.pi4, point.pi5, point.pi6, "nuisance_coupled", seed)
    else:
        raise ValueError(regime)

    tobs = _target_from_scene(local, direct_present)
    return decide_v14b(tobs, nobs, nuisance_threshold=threshold, minimum_nuisance_observation_support=min_obs)


def run(protocol_path: Path, output_path: Path) -> dict[str, Any]:
    p = json.loads(protocol_path.read_text(encoding="utf-8"))
    world = json.loads(WORLD_PROTOCOL.read_text(encoding="utf-8"))
    threshold = float(p["frozen_nuisance_threshold"])
    min_obs = float(p["minimum_nuisance_observation_support"])
    seeds = [int(x) for x in p["measurement_seeds"]]
    regimes = [LatentRegime(x) for x in p["latent_regimes"]]
    points = _points(world)

    rows: list[dict[str, Any]] = []
    global_counts = Counter(); global_n = global_fp = global_fn = global_target_false = global_target_true = 0
    for point in points:
        for regime in regimes:
            counts = Counter(); fp = fn = target_false = target_true = 0
            t_truth, _, _ = truth(regime)
            for seed in seeds:
                d = _fast_decision(point, regime, seed, threshold, min_obs)
                counts[d.state.value] += 1
                if d.reason is UndeterminedReason.INFORMATION_ABSENT: counts["u_info"] += 1
                elif d.reason is UndeterminedReason.OVERLAP_OR_ATTRIBUTION: counts["u_overlap"] += 1
                forced_positive = d.state is TernaryState.TARGET
                if t_truth:
                    target_true += 1; fn += int(not forced_positive)
                else:
                    target_false += 1; fp += int(forced_positive)
            n = len(seeds)
            row = {
                "pi1":point.pi1,"pi2":point.pi2,"pi3":point.pi3,"pi4":point.pi4,"pi5":point.pi5,"pi6":point.pi6,
                "latent_regime":regime.value,
                "baseline_rate":counts["baseline"]/n,"target_rate":counts["target"]/n,"nuisance_rate":counts["nuisance"]/n,
                "undetermined_total_rate":counts["undetermined"]/n,
                "undetermined_information_absent_rate":counts["u_info"]/n,
                "undetermined_overlap_or_attribution_rate":counts["u_overlap"]/n,
                "forced_binary_false_positive_rate":(fp/target_false) if target_false else 0.0,
                "forced_binary_false_negative_rate":(fn/target_true) if target_true else 0.0,
            }
            row["visit_presence_partial_identification_width"] = row["baseline_rate"] + row["undetermined_total_rate"]
            rows.append(row); global_counts.update(counts); global_n += n
            global_fp += fp; global_fn += fn; global_target_false += target_false; global_target_true += target_true

    result = {
        "schema":"insepi-v14b-frozen-ternary-phase-surface-result-v1",
        "coordinate_count":len(points),"row_count":len(rows),"world_count":global_n,
        "rates":{"baseline":global_counts["baseline"]/global_n,"target":global_counts["target"]/global_n,
                 "nuisance":global_counts["nuisance"]/global_n,"undetermined":global_counts["undetermined"]/global_n,
                 "u_information_absent":global_counts["u_info"]/global_n,"u_overlap_or_attribution":global_counts["u_overlap"]/global_n},
        "forced_binary_false_positive_rate":global_fp/global_target_false,
        "forced_binary_false_negative_rate":global_fn/global_target_true,
        "mean_partial_identification_width":sum(r["visit_presence_partial_identification_width"] for r in rows)/len(rows),
        "observer_retuned":False,"claim_boundary":p["claim_boundary"],"rows":rows,
    }
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--protocol",default=str(DEFAULT_PROTOCOL)); ap.add_argument("--output",default="v14b_ternary_output/phase_surface.json")
    a=ap.parse_args(); r=run(Path(a.protocol),Path(a.output)); print(json.dumps({k:v for k,v in r.items() if k!="rows"},indent=2,sort_keys=True))

if __name__=="__main__": main()
