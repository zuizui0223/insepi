"""Run V4 pixels through InsePi's independent observability front end."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import Counter

from interaction_sensing.noise import NoiseFirstPolicy
from interaction_sensing.simulation.factorial_world_v4 import build_registry, render_condition
from interaction_sensing.simulation.visual_contradiction_v2 import infer_noise_observation

SCHEMA = "pollipi-insepi-factorial-v4"


@dataclass(frozen=True, slots=True)
class InsePiFactorialResult:
    schema: str
    condition_id: str
    split: str
    true_visit: bool
    disturbance_family: str
    inferred_noise_source: str
    observability_state: str
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    capture_audit: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def disturbance_family(condition) -> str:
    active = [
        name for name in ("wind", "shake", "shadow", "occlusion", "blur", "clutter", "lens")
        if getattr(condition, name) > 0
    ]
    return "+".join(active) if active else "clean"


def run_factorial_v4(split: str | None = None) -> list[InsePiFactorialResult]:
    policy = NoiseFirstPolicy()
    rows: list[InsePiFactorialResult] = []
    for frame_index, condition in enumerate(build_registry()):
        if split is not None and condition.split != split:
            continue
        background, frame = render_condition(condition)
        observation = infer_noise_observation(background, frame, frame_index)
        decision = policy.decide(observation)
        rows.append(InsePiFactorialResult(
            schema=SCHEMA,
            condition_id=condition.condition_id,
            split=condition.split,
            true_visit=condition.true_visit,
            disturbance_family=disturbance_family(condition),
            inferred_noise_source=observation.source.value,
            observability_state=decision.state.value,
            false_event_risk=decision.false_event_risk,
            missed_event_risk=decision.missed_event_risk,
            attribution_risk=decision.attribution_risk,
            capture_audit=decision.capture_audit,
        ))
    return rows


def summarize_factorial_v4(rows: list[InsePiFactorialResult]) -> dict[str, object]:
    by_split_state = Counter((row.split, row.observability_state) for row in rows)
    calibration_disturbed = [row for row in rows if row.split == "calibration" and row.disturbance_family != "clean"]
    test_disturbed = [row for row in rows if row.split == "test" and row.disturbance_family != "clean"]
    risky = {"audit_priority", "unobservable", "confounded"}
    return {
        "n": len(rows),
        "by_split_state": {f"{split}:{state}": count for (split, state), count in sorted(by_split_state.items())},
        "calibration_disturbance_risk_recall": sum(row.observability_state in risky for row in calibration_disturbed) / len(calibration_disturbed) if calibration_disturbed else 0.0,
        "test_disturbance_risk_recall": sum(row.observability_state in risky for row in test_disturbed) / len(test_disturbed) if test_disturbed else 0.0,
    }
