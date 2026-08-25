from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("imageio_ffmpeg")

ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    path = ROOT / "scripts/v13_materialize_pixels.py"
    spec = importlib.util.spec_from_file_location("v13_materialize_pixels_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


materializer = _load_module()


def test_v13_stream_metadata_accepts_only_native_1920x1080_30fps() -> None:
    materializer.validate_stream_metadata(
        {"source_size": (1920, 1080), "fps": 30.0},
        "ok.mp4",
    )
    with pytest.raises(RuntimeError, match="1920x1080"):
        materializer.validate_stream_metadata(
            {"source_size": (1280, 720), "fps": 30.0},
            "wrong-size.mp4",
        )
    with pytest.raises(RuntimeError, match="30 fps"):
        materializer.validate_stream_metadata(
            {"source_size": (1920, 1080), "fps": 25.0},
            "wrong-fps.mp4",
        )


def test_v13_decoder_freeze_matches_measurement_contract() -> None:
    assert materializer.IMAGEIO_FFMPEG_VERSION == "0.6.0"
    assert materializer.FFMPEG_SHA256 == "e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99"
    assert materializer.EXPECTED_FPS == 30.0
    assert materializer.EXPECTED_PHASE_FRAMES == 300
    assert materializer.SAMPLE_NATIVE_FRAME_INDICES == (75, 105, 135, 165, 195, 225, 255, 285)
