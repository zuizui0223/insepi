"""Run commit-derived V5 pixels through the frozen InsePi observer."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from interaction_sensing.noise import NoiseFirstPolicy
from interaction_sensing.simulation.factorial_benchmark_v4 import (
    _apply_calibrated_local_audit,
    calibrate_occlusion_threshold,
    local_structure_loss,
)
from interaction_sensing.simulation.locked_world_v5 import (
    build_registry,
    render_condition,
)
from interaction_sensing.simulation.visual_contradiction_v2 import (
    infer_noise_observation,
)

SCHEMA = "pollipi-insepi-locked-v5"


@dataclass(frozen=True, slots=True)
class InsePiLockedV5Result:
    schema: str
    condition_id: str
    prevalence_regime: str
    true_visit: bool
    disturbance_family: str
    inferred_noise_source: str
    observability_state: str
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    capture_audit: bool
    local_structure_loss: float
    occlusion_threshold: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_locked_v5(
    pollipi_commit_sha: str,
    insepi_commit_sha: str,
) -> list[InsePiLockedV5Result]:
    policy = NoiseFirstPolicy()
    threshold = calibrate_occlusion_threshold()
    rows: list[InsePiLockedV5Result] = []
    for frame_index, condition in enumerate(build_registry(pollipi_commit_sha, insepi_commit_sha)):
        background, frame = render_condition(condition)
        observation = infer_noise_observation(background, frame, frame_index)
        structure_loss = local_structure_loss(background, frame, observation)
        observation = _apply_calibrated_local_audit(observation, structure_loss, threshold)
        decision = policy.decide(observation)
        rows.append(InsePiLockedV5Result(
            schema=SCHEMA,
            condition_id=condition.condition_id,
            prevalence_regime=condition.prevalence_regime,
            true_visit=condition.true_visit,
            disturbance_family=condition.disturbance_family,
            inferred_noise_source=observation.source.value,
            observability_state=decision.state.value,
            false_event_risk=decision.false_event_risk,
            missed_event_risk=decision.missed_event_risk,
            attribution_risk=decision.attribution_risk,
            capture_audit=decision.capture_audit,
            local_structure_loss=structure_loss,
            occlusion_threshold=threshold,
        ))
    return rows
