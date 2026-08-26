"""V2 observability trace estimated independently from the shared rendered pixels.

No scenario label is used to infer the observation state. Hidden truth is carried
only for post-hoc scoring. The estimator is deliberately transparent so later
versions can replace individual proxies without changing the benchmark contract.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from interaction_sensing.noise import NoiseFirstPolicy, NoiseObservation, NoiseSource
from interaction_sensing.simulation.portable_visual_v2 import SCENARIO_IDS, render_pair
from interaction_sensing.simulation.visual_benchmark import estimate_global_shift, shift_image

VISUAL_SCHEMA = "pollipi-insepi-visual-contradiction-v2"


@dataclass(frozen=True, slots=True)
class InsePiVisualResult:
    schema: str
    scenario_id: str
    true_visit: bool
    inferred_noise_source: str
    observability_state: str
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    global_change_fraction: float
    local_relative_motion: float
    background_motion: float
    illumination_change: float
    blur_loss: float
    capture_audit: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _reference_regions(shape: tuple[int, int]) -> tuple[tuple[slice, slice], ...]:
    h, w = shape
    rh, rw, margin = max(10, h // 6), max(14, w // 6), 5
    return (
        (slice(margin, margin + rh), slice(margin, margin + rw)),
        (slice(margin, margin + rh), slice(w - margin - rw, w - margin)),
        (slice(h - margin - rh, h - margin), slice(margin, margin + rw)),
        (slice(h - margin - rh, h - margin), slice(w - margin - rw, w - margin)),
    )


def _gradient_energy(image: np.ndarray) -> float:
    arr = image.astype(np.float32)
    gy = np.diff(arr, axis=0)
    gx = np.diff(arr, axis=1)
    return float(np.mean(np.abs(gx)) + np.mean(np.abs(gy)))


def infer_noise_observation(background: np.ndarray, frame: np.ndarray, frame_index: int) -> NoiseObservation:
    refs = _reference_regions(background.shape)
    shift_y, shift_x = estimate_global_shift(background, frame, refs, search_radius=6)
    aligned = shift_image(frame, -shift_y, -shift_x).astype(np.float32)
    base = background.astype(np.float32)
    signed = aligned - base
    residual = np.abs(signed)
    global_change = float(np.mean(residual >= 20.0))
    illumination = float(abs(np.median(signed)) / 64.0)

    h, w = background.shape
    local = residual[h // 2 - 12 : h // 2 + 12, w // 2 - 12 : w // 2 + 12]
    local_motion = float(np.mean(local) / 64.0)
    ref_values = [float(np.mean(residual[ys, xs]) / 64.0) for ys, xs in refs]
    background_motion = float(np.mean(ref_values))
    base_gradient = _gradient_energy(base)
    blur_loss = max(0.0, min(1.0, (base_gradient - _gradient_energy(aligned)) / max(base_gradient, 1e-6)))
    shift_mag = float((shift_y**2 + shift_x**2) ** 0.5)

    source = NoiseSource.STABLE_SCENE
    confidence = 0.15
    kwargs: dict[str, float] = {}
    if shift_mag >= 2.5:
        source = NoiseSource.GLOBAL_CAMERA_SHAKE
        confidence = min(1.0, shift_mag / 6.0)
        kwargs["global_motion_score"] = min(1.0, shift_mag / 6.0)
    elif blur_loss >= 0.30:
        source = NoiseSource.BLUR_OR_FOCUS_LOSS
        confidence = min(1.0, 0.45 + blur_loss)
        kwargs["blur_score"] = blur_loss
    elif illumination >= 0.18 and global_change >= 0.18:
        source = NoiseSource.SHADOW_TRANSIENT
        confidence = min(1.0, 0.45 + max(illumination, global_change))
        kwargs["illumination_change"] = min(1.0, illumination)
    elif background_motion >= 0.22 and global_change >= 0.20:
        source = NoiseSource.BACKGROUND_VEGETATION_MOTION
        confidence = min(1.0, 0.40 + max(background_motion, global_change))
        kwargs["coherent_foreground_motion_score"] = min(1.0, background_motion)
    elif global_change >= 0.10 and local_motion <= background_motion * 1.35:
        source = NoiseSource.MULTI_OBJECT_CLUTTER
        confidence = min(1.0, 0.35 + global_change)
        kwargs["clutter_score"] = min(1.0, global_change)
    elif local_motion < 0.10 and global_change < 0.03:
        source = NoiseSource.STABLE_SCENE
        confidence = 0.95
    elif local_motion >= 0.10 and background_motion < 0.12:
        source = NoiseSource.STABLE_SCENE
        confidence = 0.80
    else:
        source = NoiseSource.UNKNOWN
        confidence = 0.60

    return NoiseObservation(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source=source,
        confidence=confidence,
        frame_index=frame_index,
        local_relative_motion_score=min(1.0, local_motion),
        illumination_change=min(1.0, illumination) if "illumination_change" not in kwargs else kwargs.pop("illumination_change"),
        blur_score=min(1.0, blur_loss) if "blur_score" not in kwargs else kwargs.pop("blur_score"),
        metadata={
            "global_change_fraction": global_change,
            "background_motion": background_motion,
            "estimated_shift": [shift_y, shift_x],
        },
        **kwargs,
    )


def run_visual_contradiction_v2() -> list[InsePiVisualResult]:
    policy = NoiseFirstPolicy()
    rows: list[InsePiVisualResult] = []
    for frame_index, scenario_id in enumerate(SCENARIO_IDS):
        background, frame, truth = render_pair(scenario_id)
        observation = infer_noise_observation(background, frame, frame_index)
        decision = policy.decide(observation)
        md = observation.metadata
        rows.append(InsePiVisualResult(
            schema=VISUAL_SCHEMA,
            scenario_id=scenario_id,
            true_visit=truth,
            inferred_noise_source=observation.source.value,
            observability_state=decision.state.value,
            false_event_risk=decision.false_event_risk,
            missed_event_risk=decision.missed_event_risk,
            attribution_risk=decision.attribution_risk,
            global_change_fraction=float(md["global_change_fraction"]),
            local_relative_motion=float(observation.local_relative_motion_score or 0.0),
            background_motion=float(md["background_motion"]),
            illumination_change=float(observation.illumination_change or 0.0),
            blur_loss=float(observation.blur_score or 0.0),
            capture_audit=decision.capture_audit,
        ))
    return rows


def write_visual_trace_jsonl(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        for row in run_visual_contradiction_v2():
            handle.write(json.dumps(row.to_dict(), sort_keys=True) + "\n")
    return output
