"""Frozen V10 real-pixel canonicalisation, perturbations, and panel assignment.

This module contains no observer code. Its scientific contract is fixed by
``benchmarks/v10_real_video_protocol.json``. Changes to these semantics require
a new validation generation rather than a silent V10 edit.
"""
from __future__ import annotations

import hashlib
from typing import Sequence

import numpy as np


CANONICAL_SHAPE = (96, 128)
NATIVE_SHAPE = (1080, 1920)
INTENSITY_TIERS = (0.45, 0.80, 1.15)
FAMILIES = (
    "shadow",
    "occlusion",
    "blur",
    "sensor_banding",
    "glare",
    "framing_drift",
)
PERTURBATION_SEED_DOMAIN = "interaction-sensing-v10-real-pixel-perturbation-v1"
PANEL_ASSIGNMENT_DOMAIN = "interaction-sensing-v10-panel-assignment-v1"


def _clip_uint8(frame: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(frame), 0, 255).astype(np.uint8)


def canonicalize_rgb24(rgb: np.ndarray) -> np.ndarray:
    """Convert one frozen 1920x1080 RGB24 frame to 96x128 uint8."""
    array = np.asarray(rgb)
    if array.shape != (1080, 1920, 3):
        raise ValueError(f"expected RGB24 shape (1080,1920,3), got {array.shape}")
    if array.dtype != np.uint8:
        raise ValueError(f"expected uint8 RGB24, got {array.dtype}")
    wide = array.astype(np.uint32, copy=False)
    gray = (
        77 * wide[:, :, 0]
        + 150 * wide[:, :, 1]
        + 29 * wide[:, :, 2]
        + 128
    ) // 256
    blocks = gray.reshape(72, 15, 128, 15)
    sums = blocks.sum(axis=(1, 3), dtype=np.uint32)
    down = ((sums + 112) // 225).astype(np.uint8)
    result = np.pad(down, ((12, 12), (0, 0)), mode="edge")
    if result.shape != CANONICAL_SHAPE or result.dtype != np.uint8:
        raise AssertionError("V10 canonicalisation violated output contract")
    return result


def perturbation_seed(
    video_sha256: str,
    current_native_frame_index: int,
    family: str,
    tier_index: int,
) -> int:
    if family not in FAMILIES:
        raise ValueError(f"unknown V10 family: {family}")
    if not 0 <= tier_index < len(INTENSITY_TIERS):
        raise ValueError(f"invalid V10 tier index: {tier_index}")
    text = (
        f"{PERTURBATION_SEED_DOMAIN}|{video_sha256}|"
        f"{int(current_native_frame_index)}|{family}|{int(tier_index)}"
    )
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def _smooth(frame: np.ndarray, amount: float, rounds: int) -> np.ndarray:
    """Exact V7 iterative blur formula."""
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


def _framing_drift(frame: np.ndarray, background: np.ndarray, strength: float) -> np.ndarray:
    """Exact V7 non-wrapping framing drift, with V10 native background as V7 base."""
    height, width = frame.shape
    dy = int(np.clip(round(4 * strength), 1, 7))
    dx = int(np.clip(round(-6 * strength), -9, -1))
    shifted = np.full_like(frame, float(np.median(background)))
    y_src = slice(0, height - dy)
    y_dst = slice(dy, height)
    if dx < 0:
        x_src = slice(-dx, width)
        x_dst = slice(0, width + dx)
    else:
        x_src = slice(0, width - dx)
        x_dst = slice(dx, width)
    shifted[y_dst, x_dst] = frame[y_src, x_src]
    return shifted


def apply_perturbation(
    frame: np.ndarray,
    background: np.ndarray,
    *,
    family: str,
    tier_index: int,
    seed: int,
) -> np.ndarray:
    """Apply one preregistered generic perturbation using frozen V7 formulas."""
    source = np.asarray(frame)
    base = np.asarray(background)
    if source.shape != CANONICAL_SHAPE or source.dtype != np.uint8:
        raise ValueError("V10 perturbations require a 96x128 uint8 current frame")
    if base.shape != CANONICAL_SHAPE or base.dtype != np.uint8:
        raise ValueError("V10 perturbations require a 96x128 uint8 native background")
    if family not in FAMILIES:
        raise ValueError(f"unknown V10 family: {family}")
    if not 0 <= tier_index < len(INTENSITY_TIERS):
        raise ValueError(f"invalid V10 tier index: {tier_index}")
    strength = float(INTENSITY_TIERS[tier_index])
    rng = np.random.default_rng(int(seed))
    height, width = source.shape
    yy, xx = np.mgrid[:height, :width]
    working = source.astype(float)

    if family == "shadow":
        center = width * rng.uniform(0.42, 0.64)
        working -= 39 * strength * np.exp(
            -((xx - center) ** 2) / (2 * (width * 0.20) ** 2)
        )

    elif family == "occlusion":
        patch_h = int(rng.integers(13, 20))
        patch_w = int(rng.integers(13, 20))
        cy, cx = height // 2, width // 2
        ys = slice(cy - patch_h // 2, cy - patch_h // 2 + patch_h)
        xs = slice(cx - patch_w // 2, cx - patch_w // 2 + patch_w)
        patch = 96 + rng.normal(0, 2.5, (patch_h, patch_w))
        amount = min(1.0, 0.78 * strength)
        working[ys, xs] = (1 - amount) * working[ys, xs] + amount * patch

    elif family == "blur":
        amount = min(1.0, 0.72 * strength)
        working = _smooth(working, amount, max(1, round(2 + 2 * strength)))

    elif family == "sensor_banding":
        phase = rng.uniform(-np.pi, np.pi)
        band = np.sin(yy * rng.uniform(0.40, 0.62) + phase)
        working += 20 * strength * band

    elif family == "glare":
        cy = int(rng.integers(height // 5, 4 * height // 5))
        cx = int(rng.integers(width // 5, 4 * width // 5))
        sigma = min(height, width) * rng.uniform(0.08, 0.14)
        glare = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2))
        working += 150 * strength * glare

    elif family == "framing_drift":
        working = _framing_drift(working, base.astype(float), strength)

    else:
        raise AssertionError("unreachable V10 family")

    return _clip_uint8(working)


def variant_registry() -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = [
        {"variant_index": 0, "label": "native", "family": None, "tier_index": None, "intensity": None}
    ]
    variant_index = 1
    for family in FAMILIES:
        for tier_index, intensity in enumerate(INTENSITY_TIERS):
            rows.append(
                {
                    "variant_index": variant_index,
                    "label": f"{family}:tier{tier_index}",
                    "family": family,
                    "tier_index": tier_index,
                    "intensity": intensity,
                }
            )
            variant_index += 1
    return tuple(rows)


def condition_frames(
    native: np.ndarray,
    background: np.ndarray,
    *,
    video_sha256: str,
    current_native_frame_index: int,
) -> np.ndarray:
    """Return native + 18 preregistered variants as [19,96,128] uint8."""
    variants = np.empty((19, *CANONICAL_SHAPE), dtype=np.uint8)
    variants[0] = native
    for row in variant_registry()[1:]:
        family = str(row["family"])
        tier_index = int(row["tier_index"])
        seed = perturbation_seed(
            video_sha256,
            current_native_frame_index,
            family,
            tier_index,
        )
        variants[int(row["variant_index"])] = apply_perturbation(
            native,
            background,
            family=family,
            tier_index=tier_index,
            seed=seed,
        )
    return variants


def panel_disturbed_indices(
    window_ids: Sequence[str],
    *,
    panel_id: str,
    disturbed_count: int = 182,
) -> tuple[int, ...]:
    if len(window_ids) != len(set(window_ids)):
        raise ValueError("V10 window_ids must be unique")
    if not 0 <= disturbed_count <= len(window_ids):
        raise ValueError("invalid V10 disturbed_count")
    ranked = sorted(
        range(len(window_ids)),
        key=lambda index: (
            hashlib.sha256(
                f"{PANEL_ASSIGNMENT_DOMAIN}|{panel_id}|{window_ids[index]}".encode("utf-8")
            ).digest(),
            index,
        ),
    )
    return tuple(sorted(ranked[:disturbed_count]))


def build_panel_registry(window_ids: Sequence[str]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for family in FAMILIES:
        for tier_index, intensity in enumerate(INTENSITY_TIERS):
            panel_id = f"{family}:tier{tier_index}"
            rows.append(
                {
                    "panel_id": panel_id,
                    "family": family,
                    "tier_index": tier_index,
                    "intensity": intensity,
                    "disturbed_base_indices": list(
                        panel_disturbed_indices(window_ids, panel_id=panel_id)
                    ),
                }
            )
    return tuple(rows)
