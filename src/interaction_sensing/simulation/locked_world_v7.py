"""Seed-locked V7 visual world generator.

This module freezes the *generator contract* without materialising the final V7
world.  No default seed exists.  A 64-hex master seed must be supplied explicitly
by the locked-validation preflight after all method commits are reproducibly
reachable.

Unit tests may use dummy all-test identifiers.  Such dummy worlds are not V7
validation evidence and must never be written to the validation ledger.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Final

import numpy as np

SCHEMA: Final = "pollipi-insepi-v7-world-v1"
SIZE: Final = (96, 128)
INTENSITY_TIERS: Final = (0.45, 0.80, 1.15)
REPLICATES: Final = 2

# Fifteen pre-registered families x three intensity tiers x two replicate slots x
# two latent visit states = 180 conditions.  Three operators (sensor_banding,
# glare, framing_drift) were not present in V4 and act as explicit OOD stressors.
FAMILY_TEMPLATES: Final = (
    "clean",
    "wind",
    "shake",
    "shadow",
    "occlusion",
    "blur",
    "clutter",
    "lens",
    "sensor_banding",
    "glare",
    "framing_drift",
    "wind+shadow",
    "shake+clutter",
    "occlusion+blur",
    "glare+occlusion",
)


@dataclass(frozen=True, slots=True)
class V7Condition:
    condition_id: str
    family: str
    tier: int
    replicate: int
    seed: int
    true_visit: bool
    event_visibility: float
    intensity: float


def _require_master_seed(master_seed_hex: str) -> str:
    value = master_seed_hex.strip().lower()
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("V7 master seed must be exactly 64 lowercase/uppercase hex characters")
    return value


def _derived_seed(master_seed_hex: str, *parts: object) -> int:
    master = _require_master_seed(master_seed_hex)
    payload = "|".join((SCHEMA, master, *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def build_registry(master_seed_hex: str) -> tuple[V7Condition, ...]:
    """Build exactly 180 latent conditions from a locked master seed."""

    master = _require_master_seed(master_seed_hex)
    rows: list[V7Condition] = []
    for family in FAMILY_TEMPLATES:
        for tier, intensity in enumerate(INTENSITY_TIERS):
            # Lower signal at stronger disturbance.  Clean tiers intentionally
            # become a signal-strength control rather than duplicate conditions.
            visibility = max(0.45, 1.0 - 0.18 * tier)
            for replicate in range(REPLICATES):
                for true_visit in (False, True):
                    seed = _derived_seed(master, family, tier, replicate, int(true_visit))
                    rows.append(V7Condition(
                        condition_id=(
                            f"v7-{family.replace('+', '_')}-t{tier}-r{replicate}-v{int(true_visit)}"
                        ),
                        family=family,
                        tier=tier,
                        replicate=replicate,
                        seed=seed,
                        true_visit=true_visit,
                        event_visibility=visibility,
                        intensity=float(intensity),
                    ))
    if len(rows) != 180:
        raise AssertionError(f"V7 registry cardinality changed: {len(rows)}")
    return tuple(rows)


def _smooth(frame: np.ndarray, amount: float, rounds: int) -> np.ndarray:
    result = frame
    for _ in range(rounds):
        smoothed = (
            result
            + np.roll(result, 1, 0)
            + np.roll(result, -1, 0)
            + np.roll(result, 1, 1)
            + np.roll(result, -1, 1)
        ) / 5
        result = (1 - amount) * result + amount * smoothed
    return result


def render_condition(
    condition: V7Condition,
    *,
    size: tuple[int, int] = SIZE,
) -> tuple[np.ndarray, np.ndarray]:
    """Render one deterministic background/frame pair for a supplied condition."""

    rng = np.random.default_rng(condition.seed)
    height, width = size
    yy, xx = np.mgrid[:height, :width]
    base = (
        94
        + 16 * np.sin(xx * 0.095 + 0.2)
        + 13 * np.cos(yy * 0.155 - 0.1)
        + 7 * np.sin((1.2 * xx + yy) * 0.055)
        + 3 * np.cos((xx - 0.7 * yy) * 0.09)
        + rng.normal(0, 2.2, size=(height, width))
    )
    frame = base.copy()
    strength = condition.intensity

    if condition.true_visit:
        cy = height // 2 + int(rng.integers(-3, 4))
        cx = width // 2 + int(rng.integers(-4, 5))
        frame += (76 * condition.event_visibility) * np.exp(
            -((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * 5.2**2)
        )

    family = set(condition.family.split("+"))
    if "wind" in family:
        phase = rng.uniform(-np.pi, np.pi)
        frame += 25 * strength * (np.sin(xx * 0.19 + yy * 0.035 + phase) > 0)
    if "shadow" in family:
        center = width * rng.uniform(0.42, 0.64)
        frame -= 39 * strength * np.exp(
            -((xx - center) ** 2) / (2 * (width * 0.20) ** 2)
        )
    if "clutter" in family:
        for _ in range(5):
            cy = int(rng.integers(12, height - 12))
            cx = int(rng.integers(12, width - 12))
            radius = float(rng.uniform(5.0, 9.0))
            frame += 45 * strength * np.exp(
                -((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2)
            )
    if "occlusion" in family:
        patch_h = int(rng.integers(13, 20))
        patch_w = int(rng.integers(13, 20))
        cy, cx = height // 2, width // 2
        ys = slice(cy - patch_h // 2, cy - patch_h // 2 + patch_h)
        xs = slice(cx - patch_w // 2, cx - patch_w // 2 + patch_w)
        patch = 96 + rng.normal(0, 2.5, (patch_h, patch_w))
        amount = min(1.0, 0.78 * strength)
        frame[ys, xs] = (1 - amount) * frame[ys, xs] + amount * patch
    if "blur" in family:
        amount = min(1.0, 0.72 * strength)
        frame = _smooth(frame, amount, max(1, round(2 + 2 * strength)))
    if "lens" in family:
        cy = int(height * rng.uniform(0.28, 0.42))
        cx = int(width * rng.uniform(0.28, 0.48))
        sigma = min(height, width) * rng.uniform(0.12, 0.18)
        mask = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2))
        amount = min(1.0, 0.72 * strength)
        frame = (1 - amount * mask) * frame + amount * mask * rng.uniform(132, 155)
    if "sensor_banding" in family:
        phase = rng.uniform(-np.pi, np.pi)
        band = np.sin(yy * rng.uniform(0.40, 0.62) + phase)
        frame += 20 * strength * band
    if "glare" in family:
        cy = int(rng.integers(height // 5, 4 * height // 5))
        cx = int(rng.integers(width // 5, 4 * width // 5))
        sigma = min(height, width) * rng.uniform(0.08, 0.14)
        glare = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2))
        frame += 150 * strength * glare
    if "framing_drift" in family:
        dy = int(np.clip(round(4 * strength), 1, 7))
        dx = int(np.clip(round(-6 * strength), -9, -1))
        shifted = np.full_like(frame, float(np.median(base)))
        y_src = slice(0, height - dy)
        y_dst = slice(dy, height)
        if dx < 0:
            x_src = slice(-dx, width)
            x_dst = slice(0, width + dx)
        else:
            x_src = slice(0, width - dx)
            x_dst = slice(dx, width)
        shifted[y_dst, x_dst] = frame[y_src, x_src]
        frame = shifted
    if "shake" in family:
        dy = int(np.clip(round(3 * strength), -6, 6))
        dx = int(np.clip(round(5 * strength), -8, 8))
        frame = np.roll(np.roll(frame, dy, 0), dx, 1)

    return (
        np.clip(np.rint(base), 0, 255).astype(np.uint8),
        np.clip(np.rint(frame), 0, 255).astype(np.uint8),
    )


def spec_fingerprint() -> str:
    """Hash the seed-independent generator contract, not any final V7 world."""

    contract = {
        "schema": SCHEMA,
        "size": SIZE,
        "intensity_tiers": INTENSITY_TIERS,
        "replicates": REPLICATES,
        "families": FAMILY_TEMPLATES,
        "condition_count": 180,
    }
    return hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def suite_fingerprint(master_seed_hex: str) -> str:
    """Materialise the final pixel fingerprint only after seed unlock."""

    digest = hashlib.sha256()
    for condition in build_registry(master_seed_hex):
        background, frame = render_condition(condition)
        digest.update(json.dumps(asdict(condition), sort_keys=True, separators=(",", ":")).encode("utf-8"))
        digest.update(background.tobytes())
        digest.update(frame.tobytes())
    return digest.hexdigest()
