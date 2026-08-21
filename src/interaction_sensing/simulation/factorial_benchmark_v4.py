"""Run V4 pixels through InsePi's independently calibrated observability front end.

Only the calibration split may set the local-structure threshold below. Test/OOD
labels are never used by the estimator. V4 is now a development holdout because
its results have been inspected during feature development; a later V5 benchmark
will provide the untouched final validation for the methods-paper claim.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass

import numpy as np

from interaction_sensing.noise import NoiseFirstPolicy, NoiseSource
from interaction_sensing.simulation.factorial_world_v4 import build_registry, render_condition
from interaction_sensing.simulation.visual_benchmark import shift_image
from interaction_sensing.simulation.visual_contradiction_v2 import infer_noise_observation

SCHEMA = "pollipi-insepi-factorial-v4"
RISKY_STATES = {"audit_priority", "unobservable", "confounded"}


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
    local_structure_loss: float
    occlusion_threshold: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def disturbance_family(condition) -> str:
    active = [
        name for name in ("wind", "shake", "shadow", "occlusion", "blur", "clutter", "lens")
        if getattr(condition, name) > 0
    ]
    return "+".join(active) if active else "clean"


def _gradient_signature(patch: np.ndarray) -> np.ndarray:
    """Return a high-frequency local-structure signature.

    Using gradients makes the audit less sensitive to smooth biological intensity
    changes (e.g. a visitor-shaped Gaussian pulse) while remaining sensitive to
    replacement of the underlying scene structure by occlusion or lens effects.
    """

    arr = patch.astype(np.float32)
    gx = np.diff(arr, axis=1).reshape(-1)
    gy = np.diff(arr, axis=0).reshape(-1)
    return np.concatenate((gx, gy))


def local_structure_loss(background: np.ndarray, frame: np.ndarray, observation) -> float:
    """Measure loss of local high-frequency scene identity after alignment."""

    shift_y, shift_x = observation.metadata.get("estimated_shift", [0, 0])
    aligned = shift_image(frame, -int(shift_y), -int(shift_x)).astype(np.float32)
    base = background.astype(np.float32)
    h, w = base.shape
    ys = slice(h // 2 - 10, h // 2 + 10)
    xs = slice(w // 2 - 10, w // 2 + 10)
    a = _gradient_signature(base[ys, xs])
    b = _gradient_signature(aligned[ys, xs])
    a = a - float(a.mean())
    b = b - float(b.mean())
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-9:
        return 1.0
    corr = float(np.dot(a, b) / denom)
    return float(np.clip(1.0 - corr, 0.0, 1.0))


def calibrate_occlusion_threshold() -> float:
    """Fit one transparent threshold using calibration worlds only.

    The threshold maximises balanced accuracy for the observation-disturbance
    label ``occlusion``. True-visit labels are not used. Test intensities, mixed
    worlds and the lens OOD family remain outside calibration.
    """

    labelled: list[tuple[float, bool]] = []
    for frame_index, condition in enumerate(build_registry()):
        if condition.split != "calibration":
            continue
        background, frame = render_condition(condition)
        observation = infer_noise_observation(background, frame, frame_index)
        score = local_structure_loss(background, frame, observation)
        labelled.append((score, condition.occlusion > 0.0))

    candidates = sorted({score for score, _ in labelled})
    if not candidates:
        raise ValueError("calibration registry is empty")
    candidates = [0.0] + [0.5 * (left + right) for left, right in zip(candidates[:-1], candidates[1:])] + [1.0]

    best_threshold = 1.0
    best_balanced = -1.0
    for threshold in candidates:
        tp = sum(score >= threshold and positive for score, positive in labelled)
        fn = sum(score < threshold and positive for score, positive in labelled)
        tn = sum(score < threshold and not positive for score, positive in labelled)
        fp = sum(score >= threshold and not positive for score, positive in labelled)
        sensitivity = tp / (tp + fn) if tp + fn else 1.0
        specificity = tn / (tn + fp) if tn + fp else 1.0
        balanced = 0.5 * (sensitivity + specificity)
        if balanced > best_balanced + 1e-12 or (
            abs(balanced - best_balanced) <= 1e-12 and threshold > best_threshold
        ):
            best_balanced = balanced
            best_threshold = threshold
    return float(best_threshold)


def _apply_calibrated_local_audit(observation, structure_loss: float, threshold: float):
    """Promote otherwise-clean windows when calibration predicts occlusion risk."""

    if observation.source is NoiseSource.STABLE_SCENE and structure_loss >= threshold:
        margin = max(0.0, structure_loss - threshold)
        observation.source = NoiseSource.OCCLUSION
        observation.confidence = min(1.0, 0.70 + 1.5 * margin)
        observation.occlusion_score = observation.confidence
        observation.metadata["calibrated_local_structure_audit"] = True
    observation.metadata["local_structure_loss"] = structure_loss
    observation.metadata["occlusion_threshold"] = threshold
    return observation


def run_factorial_v4(split: str | None = None) -> list[InsePiFactorialResult]:
    policy = NoiseFirstPolicy()
    threshold = calibrate_occlusion_threshold()
    rows: list[InsePiFactorialResult] = []
    for frame_index, condition in enumerate(build_registry()):
        if split is not None and condition.split != split:
            continue
        background, frame = render_condition(condition)
        observation = infer_noise_observation(background, frame, frame_index)
        structure_loss = local_structure_loss(background, frame, observation)
        observation = _apply_calibrated_local_audit(observation, structure_loss, threshold)
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
            local_structure_loss=structure_loss,
            occlusion_threshold=threshold,
        ))
    return rows


def summarize_factorial_v4(rows: list[InsePiFactorialResult]) -> dict[str, object]:
    by_split_state = Counter((row.split, row.observability_state) for row in rows)
    calibration_disturbed = [row for row in rows if row.split == "calibration" and row.disturbance_family != "clean"]
    test_disturbed = [row for row in rows if row.split == "test" and row.disturbance_family != "clean"]
    test_clean = [row for row in rows if row.split == "test" and row.disturbance_family == "clean"]
    return {
        "n": len(rows),
        "occlusion_threshold": rows[0].occlusion_threshold if rows else None,
        "by_split_state": {f"{split}:{state}": count for (split, state), count in sorted(by_split_state.items())},
        "calibration_disturbance_risk_recall": sum(row.observability_state in RISKY_STATES for row in calibration_disturbed) / len(calibration_disturbed) if calibration_disturbed else 0.0,
        "test_disturbance_risk_recall": sum(row.observability_state in RISKY_STATES for row in test_disturbed) / len(test_disturbed) if test_disturbed else 0.0,
        "test_clean_false_risk_rate": sum(row.observability_state in RISKY_STATES for row in test_clean) / len(test_clean) if test_clean else 0.0,
    }
