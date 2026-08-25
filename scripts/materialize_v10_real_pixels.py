#!/usr/bin/env python3
"""Materialise the preregistered V10 real-pixel artifact without observers.

The scientific protocol, seven source-video SHA-256 values, decoder executable,
frame cadence, canonicalisation, perturbation registry, panel assignment and
claim ceiling must already be frozen. This script produces pixels and provenance
only. It never imports or executes PolliPi/InsePi observer logic and deliberately
prints no image-content summary or preview statistic.
"""
from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO

import imageio_ffmpeg
import numpy as np

import index_v10_remote_zip as zipidx
import materialize_v10_video_hashes as byte_lock
from interaction_sensing.simulation.real_video_v10 import (
    CANONICAL_SHAPE,
    build_panel_registry,
    canonicalize_rgb24,
    condition_frames,
    variant_registry,
)


NUMPY_PIN = "2.4.6"
RAW_RGB_FRAME_BYTES = 1920 * 1080 * 3
PROTOCOL_SHA256 = "c84947c998f69d4c8f2d056e79c7f91c6c6736b938236c17386618ac5a924e03"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def copy_member_with_sha(
    zf: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    destination: Path,
    expected_sha256: str,
) -> None:
    digest = hashlib.sha256()
    count = 0
    with zf.open(info, "r") as source, destination.open("wb") as target:
        while True:
            chunk = source.read(8 * 1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
            digest.update(chunk)
            count += len(chunk)
    if count != info.file_size:
        raise RuntimeError(f"temporary MP4 size mismatch: {info.filename}")
    actual = digest.hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(
            f"temporary MP4 SHA-256 mismatch: {info.filename} {actual} != {expected_sha256}"
        )


def read_exact_stream(stream: BinaryIO, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    payload = b"".join(chunks)
    if len(payload) != size:
        raise RuntimeError(f"short FFmpeg rawvideo frame: wanted={size} got={len(payload)}")
    return payload


def decode_canonical_every_second(
    mp4_path: Path,
    *,
    ffmpeg_executable: Path,
    expected_sampled_frames: int,
    frozen_filter: str,
) -> list[np.ndarray]:
    command = [
        str(ffmpeg_executable),
        "-v",
        "error",
        "-i",
        str(mp4_path),
        "-vf",
        frozen_filter,
        "-fps_mode",
        "passthrough",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "pipe:1",
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdout is not None
    assert process.stderr is not None
    canonical: list[np.ndarray] = []
    try:
        for _ in range(expected_sampled_frames):
            raw = read_exact_stream(process.stdout, RAW_RGB_FRAME_BYTES)
            rgb = np.frombuffer(raw, dtype=np.uint8).reshape(1080, 1920, 3)
            canonical.append(canonicalize_rgb24(rgb))
        extra = process.stdout.read(1)
        stderr = process.stderr.read().decode("utf-8", errors="replace")
        return_code = process.wait()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    if return_code != 0:
        raise RuntimeError(f"frozen FFmpeg decode failed: {stderr}")
    if extra:
        raise RuntimeError("frozen FFmpeg emitted more sampled frames than preregistered")
    if len(canonical) != expected_sampled_frames:
        raise AssertionError("sampled-frame cardinality changed")
    return canonical


def deterministic_npy_bytes(array: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    np.save(buffer, np.ascontiguousarray(array), allow_pickle=False)
    return buffer.getvalue()


def write_deterministic_npz(path: Path, arrays: dict[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for name in sorted(arrays):
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o600 << 16
            zf.writestr(info, deterministic_npy_bytes(arrays[name]))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    protocol_path = root / "benchmarks/v10_real_video_protocol.json"
    freeze_path = root / "benchmarks/v10_real_video_protocol_freeze.json"
    source_lock_path = root / "benchmarks/v10_real_video_source_lock.json"
    decoder_lock_path = root / "benchmarks/v10_decoder_freeze.json"

    protocol_bytes = protocol_path.read_bytes()
    protocol_hash = sha256_bytes(protocol_bytes)
    protocol = json.loads(protocol_bytes)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    source_lock_bytes = source_lock_path.read_bytes()
    source_lock = json.loads(source_lock_bytes)
    decoder_lock = json.loads(decoder_lock_path.read_text(encoding="utf-8"))

    if protocol_hash != PROTOCOL_SHA256 or protocol_hash != freeze["protocol_sha256"]:
        raise RuntimeError("V10 protocol bytes differ from pre-result freeze")
    if source_lock.get("status") != "byte-identities-frozen; scientific-protocol-pending":
        raise RuntimeError("V10 source byte identities are not in the expected frozen state")
    if np.__version__ != NUMPY_PIN:
        raise RuntimeError(f"V10 NumPy version mismatch: {np.__version__} != {NUMPY_PIN}")

    ffmpeg_executable = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
    if sha256_file(ffmpeg_executable) != decoder_lock["executable_sha256"]:
        raise RuntimeError("FFmpeg executable does not match the frozen V10 decoder identity")

    source = source_lock["derivation_chain"]["repository_file"]
    nested = source_lock["derivation_chain"]["nested_test_bundle"]
    selected_videos = source_lock["videos"]
    expected_windows = protocol["base_windows"]["per_video_window_count"]
    if len(selected_videos) != 7 or expected_windows != [58, 48, 59, 46, 57, 70, 26]:
        raise RuntimeError("V10 source/window registry differs from preregistration")

    backgrounds = np.empty((364, *CANONICAL_SHAPE), dtype=np.uint8)
    frames = np.empty((364, 19, *CANONICAL_SHAPE), dtype=np.uint8)
    base_registry: list[dict[str, object]] = []
    write_index = 0

    counter = zipidx.RequestCounter()
    parent = zipidx.RemoteRangeView(
        url=str(source["download_url"]),
        base_offset=0,
        size=int(source["size_bytes"]),
        root_size=int(source["size_bytes"]),
        counter=counter,
        label=str(source["name"]),
    )

    with tempfile.TemporaryDirectory(prefix="v10-pixel-materialise-") as temp_dir:
        temp_root = Path(temp_dir)
        nested_path = temp_root / "Experiment_1-Test_Videos.zip"
        nested_sha, nested_crc, nested_size = byte_lock.stream_nested_zip(
            parent, nested, nested_path
        )
        if nested_sha != nested["sha256"]:
            raise RuntimeError("nested test-bundle SHA-256 changed before V10 pixel materialisation")

        with zipfile.ZipFile(nested_path, "r") as zf:
            infos = {info.filename: info for info in zf.infolist()}
            for video_pos, row in enumerate(selected_videos):
                video_index = int(row["index"])
                name = str(row["name"])
                info = infos.get(name)
                if info is None:
                    raise RuntimeError(f"byte-frozen V10 video missing: {name}")
                temp_mp4 = temp_root / f"v10-video-{video_index}.mp4"
                copy_member_with_sha(zf, info, temp_mp4, str(row["sha256"]))
                sampled = decode_canonical_every_second(
                    temp_mp4,
                    ffmpeg_executable=ffmpeg_executable,
                    expected_sampled_frames=int(expected_windows[video_pos]) + 1,
                    frozen_filter=str(protocol["decoder"]["filter"]),
                )
                temp_mp4.unlink()

                for local_window in range(1, len(sampled)):
                    current_frame_index = local_window * 60
                    background_frame_index = current_frame_index - 60
                    background = sampled[local_window - 1]
                    native = sampled[local_window]
                    window_id = f"v{video_index}-f{current_frame_index}"
                    backgrounds[write_index] = background
                    frames[write_index] = condition_frames(
                        native,
                        background,
                        video_sha256=str(row["sha256"]),
                        current_native_frame_index=current_frame_index,
                    )
                    base_registry.append(
                        {
                            "base_index": write_index,
                            "window_id": window_id,
                            "video_index": video_index,
                            "video_sha256": str(row["sha256"]),
                            "background_native_frame_index": background_frame_index,
                            "current_native_frame_index": current_frame_index,
                            "background_time_seconds": background_frame_index / 60,
                            "current_time_seconds": current_frame_index / 60,
                            "within_video_window_index": local_window - 1,
                            "within_video_window_count": int(expected_windows[video_pos]),
                            "temporal_quartile": min(
                                3,
                                (4 * (local_window - 1)) // int(expected_windows[video_pos]),
                            ),
                        }
                    )
                    write_index += 1

    if write_index != 364 or len(base_registry) != 364:
        raise RuntimeError(f"V10 base-window count changed: {write_index}")
    variants = list(variant_registry())
    if len(variants) != 19:
        raise RuntimeError("V10 variant registry count changed")
    condition_registry = [
        {
            "condition_index": base["base_index"] * 19 + variant["variant_index"],
            "condition_id": f"{base['window_id']}|{variant['label']}",
            "base_index": base["base_index"],
            "variant_index": variant["variant_index"],
            "family": variant["family"],
            "tier_index": variant["tier_index"],
            "intensity": variant["intensity"],
            "known_disturbed": variant["variant_index"] != 0,
        }
        for base in base_registry
        for variant in variants
    ]
    if len(condition_registry) != 6916:
        raise RuntimeError("V10 condition registry count changed")
    panel_registry = list(build_panel_registry([str(row["window_id"]) for row in base_registry]))
    if len(panel_registry) != 18 or any(len(row["disturbed_base_indices"]) != 182 for row in panel_registry):
        raise RuntimeError("V10 allocation-panel registry changed")

    out_dir = root / ".v10/pixels"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_path = out_dir / "v10_base_windows.json"
    variants_path = out_dir / "v10_variant_registry.json"
    conditions_path = out_dir / "v10_condition_registry.json"
    panels_path = out_dir / "v10_panel_registry.json"
    npz_path = out_dir / "v10_real_pixel_artifact.npz"

    base_path.write_bytes(json_bytes(base_registry))
    variants_path.write_bytes(json_bytes(variants))
    conditions_path.write_bytes(json_bytes(condition_registry))
    panels_path.write_bytes(json_bytes(panel_registry))
    write_deterministic_npz(
        npz_path,
        {"backgrounds": backgrounds, "frames": frames},
    )

    receipt = {
        "schema": "interaction-sensing-v10-real-pixel-artifact-v1",
        "protocol_sha256": protocol_hash,
        "protocol_freeze_path": str(freeze_path.relative_to(root)),
        "source_lock_sha256": sha256_bytes(source_lock_bytes),
        "decoder_executable_sha256": decoder_lock["executable_sha256"],
        "numpy_version": np.__version__,
        "nested_test_bundle": {
            "sha256": nested_sha,
            "crc32_hex": f"{nested_crc:08x}",
            "byte_count": nested_size,
        },
        "base_window_count": 364,
        "variant_count": 19,
        "condition_count": 6916,
        "panel_count": 18,
        "array_contract": {
            "backgrounds_shape": list(backgrounds.shape),
            "frames_shape": list(frames.shape),
            "dtype": "uint8",
            "backgrounds_raw_sha256": sha256_bytes(backgrounds.tobytes(order="C")),
            "frames_raw_sha256": sha256_bytes(frames.tobytes(order="C")),
        },
        "files": {
            "pixel_npz_sha256": sha256_file(npz_path),
            "base_registry_sha256": sha256_file(base_path),
            "variant_registry_sha256": sha256_file(variants_path),
            "condition_registry_sha256": sha256_file(conditions_path),
            "panel_registry_sha256": sha256_file(panels_path),
        },
        "transport": {
            "outer_archive_range_bytes_requested": counter.bytes_requested,
            "outer_archive_range_request_count": counter.requests,
            "individual_source_mp4_files_deleted": True,
        },
        "human_visual_selection": False,
        "observer_execution": False,
        "v7_materialisation": False,
    }
    receipt_path = out_dir / "v10_real_pixel_receipt.json"
    receipt_path.write_bytes(json_bytes(receipt))

    print("V10_PIXEL_PROTOCOL_SHA256", protocol_hash)
    print("V10_PIXEL_BASE_WINDOWS", receipt["base_window_count"])
    print("V10_PIXEL_VARIANTS", receipt["variant_count"])
    print("V10_PIXEL_CONDITIONS", receipt["condition_count"])
    print("V10_PIXEL_PANELS", receipt["panel_count"])
    print("V10_PIXEL_ARTIFACT_SHA256", receipt["files"]["pixel_npz_sha256"])
    print("V10_PIXEL_BACKGROUND_RAW_SHA256", receipt["array_contract"]["backgrounds_raw_sha256"])
    print("V10_PIXEL_FRAMES_RAW_SHA256", receipt["array_contract"]["frames_raw_sha256"])
    print("V10_HUMAN_VISUAL_SELECTION false")
    print("V10_OBSERVER_EXECUTION false")
    print("V10_V7_MATERIALISATION false")


if __name__ == "__main__":
    main()
