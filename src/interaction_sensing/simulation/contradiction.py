"""Policy-level contradiction benchmark for parallel InsePi/PolliPi development.

The scenario IDs mirror PolliPi's contradiction trace, but the implementation
is intentionally independent.  InsePi does not ask whether a local biological
candidate should be promoted.  It asks whether the observation condition can
support a biological claim and which error mechanism is plausible.

The two repositories exchange only portable JSONL traces.  This keeps their
assumptions different enough that disagreement remains observable rather than
being trained away by a shared implementation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable

from interaction_sensing.noise import NoiseFirstPolicy, NoiseObservation, NoiseSource


CONTRADICTION_SCHEMA = "pollipi-insepi-contradiction-v1"


@dataclass(frozen=True, slots=True)
class ContrastScenario:
    scenario_id: str
    true_visit: bool
    noise_source: NoiseSource
    noise_confidence: float
    event_visibility: float


@dataclass(frozen=True, slots=True)
class InsePiContrastResult:
    schema: str
    scenario_id: str
    true_visit: bool
    noise_source: str
    noise_confidence: float
    event_visibility: float
    observability_state: str
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    capture_audit: bool
    record_high_resolution_context: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


# This is a latent-world contract, not a detector target list.  The same IDs and
# latent values are represented independently in PolliPi.
CONTRAST_SCENARIOS: tuple[ContrastScenario, ...] = (
    ContrastScenario("quiet_absence", False, NoiseSource.STABLE_SCENE, 1.00, 0.00),
    ContrastScenario("clean_visit", True, NoiseSource.STABLE_SCENE, 1.00, 1.00),
    ContrastScenario("wind_absence", False, NoiseSource.BACKGROUND_VEGETATION_MOTION, 0.95, 0.00),
    ContrastScenario("wind_visit", True, NoiseSource.BACKGROUND_VEGETATION_MOTION, 0.95, 0.65),
    ContrastScenario("shake_absence", False, NoiseSource.GLOBAL_CAMERA_SHAKE, 0.95, 0.00),
    ContrastScenario("shake_visit", True, NoiseSource.GLOBAL_CAMERA_SHAKE, 0.95, 0.55),
    ContrastScenario("shadow_absence", False, NoiseSource.SHADOW_TRANSIENT, 0.95, 0.00),
    ContrastScenario("shadow_visit", True, NoiseSource.SHADOW_TRANSIENT, 0.95, 0.60),
    ContrastScenario("occluded_visit", True, NoiseSource.OCCLUSION, 0.95, 0.18),
    ContrastScenario("blurred_visit", True, NoiseSource.BLUR_OR_FOCUS_LOSS, 0.95, 0.22),
    ContrastScenario("clutter_visit", True, NoiseSource.MULTI_OBJECT_CLUTTER, 0.95, 0.70),
    ContrastScenario("unknown_visit", True, NoiseSource.UNKNOWN, 0.80, 0.55),
)


def observation_for_scenario(scenario: ContrastScenario, frame_index: int) -> NoiseObservation:
    """Create the noise-first observation supplied to the existing risk policy."""

    confidence = scenario.noise_confidence
    source = scenario.noise_source
    kwargs: dict[str, float] = {}
    if source is NoiseSource.GLOBAL_CAMERA_SHAKE:
        kwargs["global_motion_score"] = confidence
    elif source in {NoiseSource.CO_MOVING_FOREGROUND, NoiseSource.BACKGROUND_VEGETATION_MOTION}:
        kwargs["coherent_foreground_motion_score"] = confidence
    elif source in {NoiseSource.ILLUMINATION_TRANSIENT, NoiseSource.SHADOW_TRANSIENT}:
        kwargs["illumination_change"] = confidence
    elif source is NoiseSource.OCCLUSION:
        kwargs["occlusion_score"] = confidence
    elif source in {NoiseSource.BLUR_OR_FOCUS_LOSS, NoiseSource.LENS_CONTAMINATION}:
        kwargs["blur_score"] = confidence
    elif source is NoiseSource.MULTI_OBJECT_CLUTTER:
        kwargs["clutter_score"] = confidence

    return NoiseObservation(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source=source,
        confidence=confidence,
        frame_index=frame_index,
        local_relative_motion_score=scenario.event_visibility if scenario.true_visit else 0.0,
        metadata={
            "schema": CONTRADICTION_SCHEMA,
            "scenario_id": scenario.scenario_id,
            "true_visit": scenario.true_visit,
        },
        **kwargs,
    )


def run_contradiction_scenarios(
    scenarios: Iterable[ContrastScenario] = CONTRAST_SCENARIOS,
    *,
    policy: NoiseFirstPolicy | None = None,
) -> list[InsePiContrastResult]:
    """Run the stable latent scenario contract through InsePi unchanged."""

    active_policy = policy or NoiseFirstPolicy()
    rows: list[InsePiContrastResult] = []
    for frame_index, scenario in enumerate(scenarios):
        observation = observation_for_scenario(scenario, frame_index)
        decision = active_policy.decide(observation)
        rows.append(
            InsePiContrastResult(
                schema=CONTRADICTION_SCHEMA,
                scenario_id=scenario.scenario_id,
                true_visit=scenario.true_visit,
                noise_source=scenario.noise_source.value,
                noise_confidence=scenario.noise_confidence,
                event_visibility=scenario.event_visibility,
                observability_state=decision.state.value,
                false_event_risk=decision.false_event_risk,
                missed_event_risk=decision.missed_event_risk,
                attribution_risk=decision.attribution_risk,
                capture_audit=decision.capture_audit,
                record_high_resolution_context=decision.record_high_resolution_context,
            )
        )
    return rows


def write_contradiction_trace_jsonl(path: str | Path) -> Path:
    """Write a portable trace that can be joined with the PolliPi trace."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in run_contradiction_scenarios():
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
    return output
