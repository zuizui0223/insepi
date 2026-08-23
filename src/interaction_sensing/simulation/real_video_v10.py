"""Frozen V10 real-pixel canonicalisation, perturbations, and panel assignment.

This module contains no observer code. Its scientific contract is fixed by
``benchmarks/v10_real_video_protocol.json``. Changes to these semantics require
a new validation generation rather than a silent V10 edit.
"""
from __future__ import annotations

import hashlib
from typing import Mapping, Sequence

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
    """Convert one frozen 1920x1080 RGB24 frame to 96x128 uint8.

    The transform is exact integer grayscale, non-overlapping 15x15 block mean,
    then 12-row edge padding above/below. No crop or interpolating resize occurs.
    """
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


def _smooth(frame: np.ndarray, *, rounds: int) -> np.ndarray:
    out = frame.astype(float)
    for _ in range(rounds):
        out = (
            out
            + np.roll(out, 1, axis=0)
            + np.roll(out, -1, axis=0)
            + np.roll(out, 1, axis=1)
            + np.roll(out, -1, axis=1)
        ) / 5.0
    return out


def _shift_frame(frame: np.ndarray, *, dy: int, dx: int) -> np.ndarray:
    height, width = frame.shape
    out = np.full_like(frame, np.median(frame))
    y_src0 = max(0, -dy)
    y_src1 = min(height, height - dy)
    x_src0 = max(0, -dx)
    x_src1 = min(width, width - dx)
    y_dst0 = max(0, dy)
    y_dst1 = y_dst0 + (y_src1 - y_src0)
    x_dst0 = max(0, dx)
    x_dst1 = x_dst0 + (x_src1 - x_src0)
    out[y_dst0:y_dst1, x_dst0:x_dst1] = frame[y_src0:y_src1, x_src0:x_src1]
    return out


def apply_perturbation(
    frame: np.ndarray,
    *,
    family: str,
    tier_index: int,
    seed: int,
) -> np.ndarray:
    """Apply one preregistered V7-derived generic perturbation."""
    source = np.asarray(frame)
    if source.shape != CANONICAL_SHAPE or source.dtype != np.uint8:
        raise ValueError("V10 perturbations require a 96x128 uint8 canonical frame")
    if family not in FAMILIES:
        raise ValueError(f"unknown V10 family: {family}")
    if not 0 <= tier_index < len(INTENSITY_TIERS):
        raise ValueError(f"invalid V10 tier index: {tier_index}")
    strength = float(INTENSITY_TIERS[tier_index])
    rng = np.random.default_rng(int(seed))
    height, width = source.shape

    if family == "shadow":
        _yy, xx = np.mgrid[:height, :width]
        center = rng.uniform(width * 0.42, width * 0.64)
        sigma = width * 0.15
        shadow = np.exp(-((xx - center) ** 2) / (2.0 * sigma**2))
        return _clip_uint8(source.astype(float) - 39.0 * strength * shadow)

    if family == "occlusion":
        out = source.copy().astype(float)
        patch_h = int(rng.integers(13, 20))
        patch_w = int(rng.integers(13, 20))
        center_y = height // 2
        center_x = width // 2
        y0 = max(0, center_y - patch_h // 2)
        y1 = min(height, y0 + patch_h)
        x0 = max(0, center_x - patch_w // 2)
        x1 = min(width, x0 + patch_w)
        amount = min(1.0, 0.78 * strength)
        patch = 96.0 + rng.normal(0.0, 2.5, size=(y1 - y0, x1 - x0))
        out[y0:y1, x0:x1] = (1.0 - amount) * out[y0:y1, x0:x1] + amount * patch
        return _clip_uint8(out)

    if family == "blur":
        amount = min(1.0, 0.72 * strength)
        rounds = max(1, int(round(2 + 2 * strength)))
        smooth = _smooth(source, rounds=rounds)
        return _clip_uint8((1.0 - amount) * source.astype(float) + amount * smooth)

    if family == "sensor_banding":
        yy = np.mgrid[:height, :width][0]
        phase = rng.uniform(-np.pi, np.pi)
        freq = rng.uniform(0.40, 0.62)
        banding = 20.0 * strength * np.sin(yy * freq + phase)
        return _clip_uint8(source.astype(float) + banding)

    if family == "glare":
        yy, xx = np.mgrid[:height, :width]
        center_x = rng.uniform(width * 0.2, width * 0.8)
        center_y = rng.uniform(height * 0.2, height * 0.8)
        sigma = rng.uniform(0.08, 0.14) * min(height, width)
        glare = np.exp(
            -((xx - center_x) ** 2 + (yy - center_y) ** 2) / (2.0 * sigma**2)
        )
        return _clip_uint8(source.astype(float) + 150.0 * strength * glare)

    if family == "framing_drift":
        dy = int(np.clip(round(4 * strength), 1, 7))
        dx = int(np.clip(round(-6 * strength), -9, -1))
        return _shift_frame(source, dy=dy, dx=dx)

    raise AssertionError("unreachable V10 family")


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
