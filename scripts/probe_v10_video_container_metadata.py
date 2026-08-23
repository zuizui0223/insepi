#!/usr/bin/env python3
"""Probe container metadata for the seven byte-frozen V10 MP4s.

The script temporarily materialises each already SHA-256-frozen MP4 only to run
``ffprobe`` on container/stream metadata. No video frame is decoded to pixels,
no observer is run, and no performance result is generated. Temporary MP4s are
deleted before the receipt is written.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import index_v10_remote_zip as zipidx
import materialize_v10_video_hashes as byte_lock


FFPROBE_ENTRIES = (
    "stream=index,codec_name,codec_type,width,height,pix_fmt,r_frame_rate,avg_frame_rate,"
    "time_base,start_time,duration,nb_frames:format=format_name,duration,size"
)


def copy_member_with_sha(zf: zipfile.ZipFile, info: zipfile.ZipInfo, destination: Path) -> str:
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
    if count != info.file_size or destination.stat().st_size != info.file_size:
        raise RuntimeError(f"temporary MP4 size mismatch: {info.filename}")
    return digest.hexdigest()


def run_ffprobe(path: Path) -> dict[str, object]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        FFPROBE_ENTRIES,
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    obj = json.loads(result.stdout)
    if not isinstance(obj, dict):
        raise RuntimeError("ffprobe did not return a JSON object")
    streams = obj.get("streams")
    if not isinstance(streams, list):
        raise RuntimeError("ffprobe result has no streams list")
    video_streams = [row for row in streams if isinstance(row, dict) and row.get("codec_type") == "video"]
    if len(video_streams) != 1:
        raise RuntimeError(f"expected exactly one video stream, got {len(video_streams)}")
    return {"video_stream": video_streams[0], "format": obj.get("format", {})}


def main() -> None:
    lock_path = Path("benchmarks/v10_real_video_source_lock.json")
    lock_bytes = lock_path.read_bytes()
    lock = json.loads(lock_bytes)
    if lock.get("status") != "byte-identities-frozen; scientific-protocol-pending":
        raise RuntimeError("container probe requires the completed V10 byte lock")
    selected = lock.get("videos")
    if not isinstance(selected, list) or len(selected) != 7:
        raise RuntimeError("container probe requires exactly seven frozen videos")
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is required for metadata-only V10 container probing")

    source = lock["derivation_chain"]["repository_file"]
    nested = lock["derivation_chain"]["nested_test_bundle"]
    counter = zipidx.RequestCounter()
    parent = zipidx.RemoteRangeView(
        url=str(source["download_url"]),
        base_offset=0,
        size=int(source["size_bytes"]),
        root_size=int(source["size_bytes"]),
        counter=counter,
        label=str(source["name"]),
    )

    receipts: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="v10-container-probe-") as temp_dir:
        temp_root = Path(temp_dir)
        nested_path = temp_root / "Experiment_1-Test_Videos.zip"
        nested_sha, nested_crc, nested_size = byte_lock.stream_nested_zip(
            parent, nested, nested_path
        )
        if nested_sha != str(nested["sha256"]):
            raise RuntimeError("nested test-bundle SHA-256 differs from frozen source lock")

        with zipfile.ZipFile(nested_path, "r") as zf:
            infos = {info.filename: info for info in zf.infolist()}
            for row in selected:
                name = str(row["name"])
                info = infos.get(name)
                if info is None:
                    raise RuntimeError(f"frozen MP4 missing: {name}")
                temp_mp4 = temp_root / f"video-{int(row['index'])}.mp4"
                sha256 = copy_member_with_sha(zf, info, temp_mp4)
                if sha256 != str(row["sha256"]):
                    raise RuntimeError(f"MP4 SHA-256 mismatch before ffprobe: {name}")
                probe = run_ffprobe(temp_mp4)
                receipts.append(
                    {
                        "index": int(row["index"]),
                        "name": name,
                        "sha256": sha256,
                        "byte_count": info.file_size,
                        **probe,
                    }
                )
                temp_mp4.unlink()

    receipt = {
        "schema": "interaction-sensing-v10-container-metadata-v1",
        "source_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "nested_test_bundle": {
            "sha256": nested_sha,
            "crc32_hex": f"{nested_crc:08x}",
            "byte_count": nested_size,
        },
        "video_count": len(receipts),
        "videos": receipts,
        "transport": {
            "outer_archive_range_bytes_requested": counter.bytes_requested,
            "outer_archive_range_request_count": counter.requests,
            "temporary_mp4_files_deleted": True,
        },
        "video_pixels_decoded": False,
        "observer_execution": False,
        "v7_materialisation": False,
    }
    output = Path(".v10/v10_container_metadata.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print("V10_CONTAINER_METADATA_VIDEO_COUNT", len(receipts))
    print("V10_VIDEO_PIXELS_DECODED false")
    print("V10_OBSERVER_EXECUTION false")
    for row in receipts:
        stream = row["video_stream"]
        print(
            "V10_CONTAINER_VIDEO",
            row["index"],
            stream.get("width"),
            stream.get("height"),
            stream.get("r_frame_rate"),
            stream.get("avg_frame_rate"),
            stream.get("nb_frames"),
            stream.get("duration"),
        )


if __name__ == "__main__":
    main()
