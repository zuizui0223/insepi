#!/usr/bin/env python3
"""Freeze the decoder executable identity for V10 without reading any video.

V10 scientific pixels may later be materialised only with this exact decoder
binary and the pre-registered command/filter semantics. This script installs or
selects no method code and accesses no V10 MP4 bytes.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import imageio_ffmpeg


PACKAGE_PIN = "imageio-ffmpeg==0.6.0"
FRAME_FILTER = "select='not(mod(n,60))'"
PIXEL_FORMAT = "rgb24"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    executable = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    if not executable.is_file():
        raise RuntimeError("imageio-ffmpeg did not provide an executable")
    version_line = subprocess.run(
        [str(executable), "-version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    receipt = {
        "schema": "interaction-sensing-v10-decoder-freeze-v1",
        "python_package_pin": PACKAGE_PIN,
        "executable_name": executable.name,
        "executable_sha256": sha256_file(executable),
        "ffmpeg_version_line": version_line,
        "frame_selection_semantics": {
            "input_frame_indices": "all decoded frame indices n satisfying n mod 60 == 0, beginning with n=0",
            "ffmpeg_filter": FRAME_FILTER,
            "output_pixel_format": PIXEL_FORMAT,
            "output_container": "rawvideo to stdout",
            "timestamp_resampling": false,
            "expected_native_input": "1920x1080 AVC MP4 at exactly 60 fps from the frozen V10 container metadata"
        },
        "canonical_ffmpeg_argv_template": [
            "<FROZEN_FFMPEG_EXECUTABLE>",
            "-v", "error",
            "-i", "<BYTE_FROZEN_MP4>",
            "-vf", FRAME_FILTER,
            "-fps_mode", "passthrough",
            "-f", "rawvideo",
            "-pix_fmt", PIXEL_FORMAT,
            "pipe:1"
        ],
        "video_bytes_accessed": false,
        "video_pixels_decoded": false,
        "observer_execution": false,
        "v7_materialisation": false
    }
    output = Path(".v10/v10_decoder_freeze.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V10_DECODER_PACKAGE", PACKAGE_PIN)
    print("V10_DECODER_EXECUTABLE", executable.name)
    print("V10_DECODER_SHA256", receipt["executable_sha256"])
    print("V10_DECODER_VERSION", version_line)
    print("V10_VIDEO_BYTES_ACCESSED false")
    print("V10_VIDEO_PIXELS_DECODED false")


if __name__ == "__main__":
    main()
