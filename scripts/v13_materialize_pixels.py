#!/usr/bin/env python3
"""Materialise truth-free V13 canonical pixels from observer-safe phase clips."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from interaction_sensing.physical_artifact_v13 import materialise_pixel_artifact, sha256_file
from interaction_sensing.physical_measurement_v13 import SAMPLE_NATIVE_FRAME_INDICES

FFMPEG_SHA256 = "e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99"
WIDTH = 1920
HEIGHT = 1080
CHANNELS = 3
FRAME_BYTES = WIDTH * HEIGHT * CHANNELS
EXPECTED_PHASE_FRAMES = 300


def _select_filter(indices: tuple[int, ...]) -> str:
    return "select=" + "+".join(f"eq(n\\,{index})" for index in indices)


def _run_rawvideo(ffmpeg: Path, clip: Path, indices: tuple[int, ...]) -> bytes:
    completed = subprocess.run(
        [
            str(ffmpeg),
            "-v", "error",
            "-i", str(clip),
            "-vf", _select_filter(indices),
            "-fps_mode", "passthrough",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "pipe:1",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def decoder_identity(ffmpeg: Path) -> dict[str, object]:
    if not ffmpeg.is_file():
        raise FileNotFoundError(ffmpeg)
    digest = sha256_file(ffmpeg)
    if digest != FFMPEG_SHA256:
        raise RuntimeError(f"V13 ffmpeg executable mismatch: {digest} != {FFMPEG_SHA256}")
    version = subprocess.run(
        [str(ffmpeg), "-version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    return {
        "ffmpeg_sha256": digest,
        "ffmpeg_version_line": version,
        "native_shape": [HEIGHT, WIDTH, CHANNELS],
        "required_phase_frame_count": EXPECTED_PHASE_FRAMES,
        "sample_native_frame_indices": list(SAMPLE_NATIVE_FRAME_INDICES),
        "timestamp_resampling": False,
    }


def make_phase_loader(ffmpeg: Path, clips_dir: Path):
    def load(clip_key: str):
        clip = clips_dir / clip_key
        if not clip.is_file():
            raise FileNotFoundError(clip)
        # Exact cardinality probe: native frame n=299 must exist and n=300 must
        # not exist.  At 1920x1080 RGB24 this must yield exactly one raw frame.
        probe = _run_rawvideo(ffmpeg, clip, (EXPECTED_PHASE_FRAMES - 1, EXPECTED_PHASE_FRAMES))
        if len(probe) != FRAME_BYTES:
            raise RuntimeError(
                f"V13 clip is not exactly 300 native 1920x1080 frames: {clip_key}; "
                f"probe bytes={len(probe)} expected={FRAME_BYTES}"
            )
        raw = _run_rawvideo(ffmpeg, clip, SAMPLE_NATIVE_FRAME_INDICES)
        expected = len(SAMPLE_NATIVE_FRAME_INDICES) * FRAME_BYTES
        if len(raw) != expected:
            raise RuntimeError(
                f"V13 sampled rawvideo byte count mismatch for {clip_key}: {len(raw)} != {expected}"
            )
        frames = np.frombuffer(raw, dtype=np.uint8).reshape(
            len(SAMPLE_NATIVE_FRAME_INDICES), HEIGHT, WIDTH, CHANNELS
        )
        return tuple(np.array(frame, copy=True) for frame in frames), sha256_file(clip)
    return load


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--observer-plan", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--clips-dir", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    commitment = json.loads(args.commitment.read_text(encoding="utf-8"))
    if commitment.get("schema") != "interaction-sensing-v13-randomisation-commitment-v1":
        raise SystemExit("wrong V13 randomisation commitment schema")
    plan_sha = sha256_file(args.observer_plan)
    if plan_sha != commitment.get("observer_plan_sha256"):
        raise SystemExit(
            f"observer-plan commitment mismatch: {plan_sha} != {commitment.get('observer_plan_sha256')}"
        )

    identity = decoder_identity(args.ffmpeg)
    receipt = materialise_pixel_artifact(
        args.observer_plan,
        args.output_dir,
        phase_loader=make_phase_loader(args.ffmpeg, args.clips_dir),
        decoder_identity=identity,
    )
    print("V13_PIXEL_ARTIFACT PASS")
    print("V13_FRAMES_RAW_SHA256", receipt["array_contract"]["frames_raw_sha256"])
    print("V13_BACKGROUNDS_RAW_SHA256", receipt["array_contract"]["backgrounds_raw_sha256"])
    print("V13_FRAMES_FILE_SHA256", receipt["files"]["frames_npy_sha256"])
    print("V13_BACKGROUNDS_FILE_SHA256", receipt["files"]["backgrounds_npy_sha256"])


if __name__ == "__main__":
    main()
