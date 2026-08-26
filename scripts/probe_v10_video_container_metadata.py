#!/usr/bin/env python3
"""Probe ISO-BMFF container metadata for the seven byte-frozen V10 MP4s.

The script temporarily materialises each already SHA-256-frozen MP4, parses MP4
box metadata using only the Python standard library, and deletes the temporary
file. No video frame is decoded to pixels, no observer is run, and no
performance result is generated.
"""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

import index_v10_remote_zip as zipidx
import materialize_v10_video_hashes as byte_lock


@dataclass(frozen=True)
class Box:
    type: str
    start: int
    header_size: int
    size: int

    @property
    def payload_start(self) -> int:
        return self.start + self.header_size

    @property
    def end(self) -> int:
        return self.start + self.size


def read_exact(handle: BinaryIO, offset: int, size: int) -> bytes:
    handle.seek(offset)
    payload = handle.read(size)
    if len(payload) != size:
        raise RuntimeError(f"short MP4 read at offset {offset}: wanted={size} got={len(payload)}")
    return payload


def iter_boxes(handle: BinaryIO, start: int, end: int) -> Iterator[Box]:
    position = start
    while position < end:
        if end - position < 8:
            raise RuntimeError(f"truncated MP4 box header at {position}")
        header = read_exact(handle, position, 8)
        size32, type_raw = struct.unpack(">I4s", header)
        box_type = type_raw.decode("latin1")
        if size32 == 1:
            if end - position < 16:
                raise RuntimeError(f"truncated extended MP4 box header at {position}")
            size = struct.unpack(">Q", read_exact(handle, position + 8, 8))[0]
            header_size = 16
        elif size32 == 0:
            size = end - position
            header_size = 8
        else:
            size = size32
            header_size = 8
        if size < header_size or position + size > end:
            raise RuntimeError(
                f"invalid MP4 box {box_type!r} at {position}: size={size} parent_end={end}"
            )
        yield Box(box_type, position, header_size, int(size))
        position += int(size)


def find_child(handle: BinaryIO, parent: Box, box_type: str) -> Box:
    matches = [
        box
        for box in iter_boxes(handle, parent.payload_start, parent.end)
        if box.type == box_type
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {box_type!r} in {parent.type!r}, got {len(matches)}"
        )
    return matches[0]


def top_box(handle: BinaryIO, file_size: int, box_type: str) -> Box:
    matches = [box for box in iter_boxes(handle, 0, file_size) if box.type == box_type]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one top-level {box_type!r}, got {len(matches)}")
    return matches[0]


def handler_type(handle: BinaryIO, mdia: Box) -> str:
    hdlr = find_child(handle, mdia, "hdlr")
    payload = read_exact(handle, hdlr.payload_start, min(12, hdlr.size - hdlr.header_size))
    if len(payload) < 12:
        raise RuntimeError("truncated hdlr payload")
    return payload[8:12].decode("latin1")


def parse_mdhd(handle: BinaryIO, mdia: Box) -> tuple[int, int]:
    mdhd = find_child(handle, mdia, "mdhd")
    payload = read_exact(handle, mdhd.payload_start, mdhd.size - mdhd.header_size)
    if len(payload) < 20:
        raise RuntimeError("truncated mdhd payload")
    version = payload[0]
    if version == 0:
        timescale = struct.unpack_from(">I", payload, 12)[0]
        duration = struct.unpack_from(">I", payload, 16)[0]
    elif version == 1:
        if len(payload) < 32:
            raise RuntimeError("truncated version-1 mdhd payload")
        timescale = struct.unpack_from(">I", payload, 20)[0]
        duration = struct.unpack_from(">Q", payload, 24)[0]
    else:
        raise RuntimeError(f"unsupported mdhd version: {version}")
    if timescale <= 0:
        raise RuntimeError("invalid MP4 media timescale")
    return int(timescale), int(duration)


def parse_tkhd_dimensions(handle: BinaryIO, trak: Box) -> tuple[float, float]:
    tkhd = find_child(handle, trak, "tkhd")
    payload_size = tkhd.size - tkhd.header_size
    if payload_size < 8:
        raise RuntimeError("truncated tkhd payload")
    raw = read_exact(handle, tkhd.end - 8, 8)
    width_fixed, height_fixed = struct.unpack(">II", raw)
    return width_fixed / 65536.0, height_fixed / 65536.0


def parse_stsz(handle: BinaryIO, stbl: Box) -> tuple[int, int]:
    stsz = find_child(handle, stbl, "stsz")
    payload = read_exact(handle, stsz.payload_start, min(12, stsz.size - stsz.header_size))
    if len(payload) < 12:
        raise RuntimeError("truncated stsz payload")
    sample_size = struct.unpack_from(">I", payload, 4)[0]
    sample_count = struct.unpack_from(">I", payload, 8)[0]
    return int(sample_size), int(sample_count)


def parse_stts(handle: BinaryIO, stbl: Box) -> tuple[int, int, list[dict[str, int]]]:
    stts = find_child(handle, stbl, "stts")
    payload = read_exact(handle, stts.payload_start, stts.size - stts.header_size)
    if len(payload) < 8:
        raise RuntimeError("truncated stts payload")
    entry_count = struct.unpack_from(">I", payload, 4)[0]
    expected = 8 + int(entry_count) * 8
    if len(payload) < expected:
        raise RuntimeError("truncated stts entries")
    total_samples = 0
    total_ticks = 0
    entries: list[dict[str, int]] = []
    offset = 8
    for _ in range(int(entry_count)):
        count, delta = struct.unpack_from(">II", payload, offset)
        offset += 8
        total_samples += int(count)
        total_ticks += int(count) * int(delta)
        entries.append({"sample_count": int(count), "sample_delta": int(delta)})
    return total_samples, total_ticks, entries


def parse_stsd_codec(handle: BinaryIO, stbl: Box) -> str:
    stsd = find_child(handle, stbl, "stsd")
    payload = read_exact(handle, stsd.payload_start, min(16, stsd.size - stsd.header_size))
    if len(payload) < 16:
        raise RuntimeError("truncated stsd payload")
    entry_count = struct.unpack_from(">I", payload, 4)[0]
    if entry_count < 1:
        raise RuntimeError("stsd has no sample descriptions")
    return payload[12:16].decode("latin1")


def parse_mp4_video_metadata(path: Path) -> dict[str, object]:
    file_size = path.stat().st_size
    with path.open("rb") as handle:
        moov = top_box(handle, file_size, "moov")
        traks = [box for box in iter_boxes(handle, moov.payload_start, moov.end) if box.type == "trak"]
        video_candidates: list[tuple[Box, Box]] = []
        for trak in traks:
            mdia = find_child(handle, trak, "mdia")
            if handler_type(handle, mdia) == "vide":
                video_candidates.append((trak, mdia))
        if len(video_candidates) != 1:
            raise RuntimeError(f"expected exactly one video track, got {len(video_candidates)}")
        trak, mdia = video_candidates[0]
        minf = find_child(handle, mdia, "minf")
        stbl = find_child(handle, minf, "stbl")
        timescale, mdhd_duration_ticks = parse_mdhd(handle, mdia)
        width, height = parse_tkhd_dimensions(handle, trak)
        sample_size, sample_count = parse_stsz(handle, stbl)
        stts_samples, stts_duration_ticks, stts_entries = parse_stts(handle, stbl)
        if stts_samples != sample_count:
            raise RuntimeError(
                f"stts/stsz sample-count mismatch: stts={stts_samples} stsz={sample_count}"
            )
        codec = parse_stsd_codec(handle, stbl)

    duration_seconds = stts_duration_ticks / timescale
    mdhd_duration_seconds = mdhd_duration_ticks / timescale
    average_fps = sample_count / duration_seconds if duration_seconds > 0 else None
    return {
        "container": "ISO-BMFF/MP4",
        "file_size": file_size,
        "video_track_count": 1,
        "codec_fourcc": codec,
        "width": width,
        "height": height,
        "timescale": timescale,
        "mdhd_duration_ticks": mdhd_duration_ticks,
        "mdhd_duration_seconds": mdhd_duration_seconds,
        "sample_size_constant": sample_size,
        "frame_sample_count": sample_count,
        "stts_duration_ticks": stts_duration_ticks,
        "duration_seconds": duration_seconds,
        "average_fps_from_stts": average_fps,
        "stts_entries": stts_entries,
    }


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


def main() -> None:
    lock_path = Path("benchmarks/v10_real_video_source_lock.json")
    lock_bytes = lock_path.read_bytes()
    lock = json.loads(lock_bytes)
    if lock.get("status") != "byte-identities-frozen; scientific-protocol-pending":
        raise RuntimeError("container probe requires the completed V10 byte lock")
    selected = lock.get("videos")
    if not isinstance(selected, list) or len(selected) != 7:
        raise RuntimeError("container probe requires exactly seven frozen videos")

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
                    raise RuntimeError(f"MP4 SHA-256 mismatch before metadata parse: {name}")
                metadata = parse_mp4_video_metadata(temp_mp4)
                receipts.append(
                    {
                        "index": int(row["index"]),
                        "name": name,
                        "sha256": sha256,
                        "metadata": metadata,
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
        "parser": "python-standard-library-iso-bmff-v1",
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
        meta = row["metadata"]
        print(
            "V10_CONTAINER_VIDEO",
            row["index"],
            meta["width"],
            meta["height"],
            meta["frame_sample_count"],
            meta["duration_seconds"],
            meta["average_fps_from_stts"],
            meta["codec_fourcc"],
        )


if __name__ == "__main__":
    main()
