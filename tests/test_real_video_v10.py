from __future__ import annotations

import numpy as np

from interaction_sensing.simulation.real_video_v10 import (
    FAMILIES,
    INTENSITY_TIERS,
    apply_perturbation,
    build_panel_registry,
    canonicalize_rgb24,
    condition_frames,
    perturbation_seed,
    variant_registry,
)


def clip_uint8(frame: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(frame), 0, 255).astype(np.uint8)


def ref_smooth(frame: np.ndarray, amount: float, rounds: int) -> np.ndarray:
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


def reference_v7_transfer(
    frame: np.ndarray,
    background: np.ndarray,
    *,
    family: str,
    tier_index: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    height, width = frame.shape
    yy, xx = np.mgrid[:height, :width]
    working = frame.astype(float)
    base = background.astype(float)
    strength = INTENSITY_TIERS[tier_index]

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
        working = ref_smooth(working, amount, max(1, round(2 + 2 * strength)))
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
        dy = int(np.clip(round(4 * strength), 1, 7))
        dx = int(np.clip(round(-6 * strength), -9, -1))
        shifted = np.full_like(working, float(np.median(base)))
        y_src = slice(0, height - dy)
        y_dst = slice(dy, height)
        if dx < 0:
            x_src = slice(-dx, width)
            x_dst = slice(0, width + dx)
        else:
            x_src = slice(0, width - dx)
            x_dst = slice(dx, width)
        shifted[y_dst, x_dst] = working[y_src, x_src]
        working = shifted
    else:
        raise AssertionError(family)
    return clip_uint8(working)


def test_canonicalize_rgb24_exact_shape_dtype_and_solid_value() -> None:
    rgb = np.empty((1080, 1920, 3), dtype=np.uint8)
    rgb[..., 0] = 40
    rgb[..., 1] = 100
    rgb[..., 2] = 180
    expected_gray = (77 * 40 + 150 * 100 + 29 * 180 + 128) // 256
    out = canonicalize_rgb24(rgb)
    assert out.shape == (96, 128)
    assert out.dtype == np.uint8
    assert np.all(out == expected_gray)
    assert np.array_equal(out[:12], out[12:13].repeat(12, axis=0))
    assert np.array_equal(out[-12:], out[-13:-12].repeat(12, axis=0))


def test_variant_registry_is_exactly_native_plus_six_by_three() -> None:
    rows = variant_registry()
    assert len(rows) == 19
    assert rows[0]["label"] == "native"
    assert [row["family"] for row in rows[1::3]] == list(FAMILIES)
    assert {row["tier_index"] for row in rows[1:]} == {0, 1, 2}


def test_all_eighteen_perturbations_match_frozen_v7_formulas() -> None:
    yy, xx = np.mgrid[:96, :128]
    frame = ((3 * yy + 5 * xx + 17) % 256).astype(np.uint8)
    background = ((7 * yy + 2 * xx + 91) % 256).astype(np.uint8)
    video_sha = "ab" * 32
    for family in FAMILIES:
        for tier_index in range(3):
            seed = perturbation_seed(video_sha, 600, family, tier_index)
            actual = apply_perturbation(
                frame,
                background,
                family=family,
                tier_index=tier_index,
                seed=seed,
            )
            expected = reference_v7_transfer(
                frame,
                background,
                family=family,
                tier_index=tier_index,
                seed=seed,
            )
            assert np.array_equal(actual, expected), (family, tier_index)


def test_condition_frames_are_deterministic_and_leave_native_unchanged() -> None:
    rng = np.random.default_rng(22)
    frame = rng.integers(0, 256, size=(96, 128), dtype=np.uint8)
    background = rng.integers(0, 256, size=(96, 128), dtype=np.uint8)
    first = condition_frames(
        frame,
        background,
        video_sha256="cd" * 32,
        current_native_frame_index=120,
    )
    second = condition_frames(
        frame,
        background,
        video_sha256="cd" * 32,
        current_native_frame_index=120,
    )
    assert first.shape == (19, 96, 128)
    assert first.dtype == np.uint8
    assert np.array_equal(first[0], frame)
    assert np.array_equal(first, second)


def test_panel_registry_is_balanced_deterministic_and_complete() -> None:
    window_ids = [f"v1-f{60 * (index + 1)}" for index in range(364)]
    first = build_panel_registry(window_ids)
    second = build_panel_registry(window_ids)
    assert first == second
    assert len(first) == 18
    assert [row["panel_id"] for row in first] == [
        f"{family}:tier{tier}"
        for family in FAMILIES
        for tier in range(3)
    ]
    for row in first:
        indices = row["disturbed_base_indices"]
        assert len(indices) == 182
        assert len(set(indices)) == 182
        assert min(indices) >= 0
        assert max(indices) < 364
