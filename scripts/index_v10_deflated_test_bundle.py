#!/usr/bin/env python3
"""Stream-index the small deflated V10 test-video bundle without saving videos.

The target member is Experiment_1-Test_Videos.zip inside Experiment_Data.zip.
Only that compressed member (~464 MB) is transferred. It is raw-DEFLATE decoded
in memory chunks; all decompressed payload is discarded except a bounded tail
containing the nested ZIP central directory. No video member is written to disk.
"""
from __future__ import annotations

import argparse
import json
import struct
import zlib
from pathlib import Path

import index_v10_remote_zip as zipidx


TARGET_ARCHIVE = "Experiment_Data.zip"
TARGET_MEMBER = "Experiment_Data/Experiment_1/Experiment_1-Test_Videos.zip"
MAX_COMPRESSED_BYTES = 600 * 1024 * 1024
CHUNK_BYTES = 8 * 1024 * 1024
TAIL_KEEP_BYTES = 16 * 1024 * 1024


def local_data_offset(parent: zipidx.RemoteRangeView, member: dict[str, object]) -> int:
    offset = int(member["local_header_offset"])
    header = parent.read(offset, offset + 29)
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != zipidx.LOCAL_SIG:
        raise RuntimeError("local-header signature mismatch")
    local_flag = int(fields[2])
    local_method = int(fields[3])
    filename_len = int(fields[9])
    extra_len = int(fields[10])
    if local_flag != int(member["flag_bits"]):
        raise RuntimeError("local/central flag mismatch")
    if local_method != int(member["compression_method"]):
        raise RuntimeError("local/central compression-method mismatch")
    return offset + 30 + filename_len + extra_len


def append_tail(tail: bytearray, data: bytes) -> None:
    if not data:
        return
    if len(data) >= TAIL_KEEP_BYTES:
        tail[:] = data[-TAIL_KEEP_BYTES:]
        return
    tail.extend(data)
    if len(tail) > TAIL_KEEP_BYTES:
        del tail[: len(tail) - TAIL_KEEP_BYTES]


def nested_central_from_tail(tail: bytes, total_size: int) -> tuple[bytes, int, int, int]:
    tail_start = total_size - len(tail)
    eocd_pos = zipidx.find_eocd(tail)
    fields = struct.unpack_from("<4s4H2IH", tail, eocd_pos)
    _, _disk_no, _cd_disk, entries_disk, entries_total, cd_size32, cd_offset32, _comment = fields
    needs_zip64 = (
        entries_disk == 0xFFFF
        or entries_total == 0xFFFF
        or cd_size32 == 0xFFFFFFFF
        or cd_offset32 == 0xFFFFFFFF
    )
    if needs_zip64:
        locator_pos = eocd_pos - 20
        if locator_pos < 0 or tail[locator_pos : locator_pos + 4] != zipidx.ZIP64_LOCATOR_SIG:
            raise RuntimeError("Zip64 locator is not retained in nested tail")
        _sig, _disk, zip64_offset, _disks = struct.unpack_from("<4sIQI", tail, locator_pos)
        record_pos = int(zip64_offset) - tail_start
        if record_pos < 0 or record_pos + 56 > len(tail):
            raise RuntimeError("Zip64 EOCD is outside retained nested tail")
        record = struct.unpack_from("<4sQ2H2I4Q", tail, record_pos)
        if record[0] != zipidx.ZIP64_EOCD_SIG:
            raise RuntimeError("nested Zip64 EOCD signature mismatch")
        entries_total = int(record[7])
        cd_size = int(record[8])
        cd_offset = int(record[9])
    else:
        cd_size = int(cd_size32)
        cd_offset = int(cd_offset32)
        entries_total = int(entries_total)

    start = cd_offset - tail_start
    end = start + cd_size
    if start < 0 or end > len(tail):
        raise RuntimeError(
            f"nested central directory not retained: cd={cd_offset}:{cd_offset + cd_size} tail={tail_start}:{total_size}"
        )
    return tail[start:end], cd_offset, cd_size, entries_total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-resolution", type=Path, default=Path(".v10/source-resolution.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path(".v10/experiment-test-videos-index.json")
    )
    args = parser.parse_args()

    source = json.loads(args.source_resolution.read_text(encoding="utf-8"))
    archives = [row for row in source["files"] if row["name"] == TARGET_ARCHIVE]
    if len(archives) != 1:
        raise RuntimeError(f"expected exactly one {TARGET_ARCHIVE!r}")
    archive = archives[0]
    counter = zipidx.RequestCounter()
    parent = zipidx.RemoteRangeView(
        url=str(archive["download_url"]),
        base_offset=0,
        size=int(archive["size_bytes"]),
        root_size=int(archive["size_bytes"]),
        counter=counter,
        label=TARGET_ARCHIVE,
    )
    parent_index = zipidx.index_zip(parent)
    targets = [row for row in parent_index["members"] if row["name"] == TARGET_MEMBER]
    if len(targets) != 1:
        raise RuntimeError(f"expected exactly one target nested ZIP, found {len(targets)}")
    member = targets[0]
    compressed_size = int(member["compressed_size"])
    uncompressed_size = int(member["uncompressed_size"])
    if int(member["compression_method"]) != 8:
        raise RuntimeError(f"expected raw Deflate method 8, got {member['compression_method']}")
    if int(member["flag_bits"]) & 0x1:
        raise RuntimeError("encrypted nested ZIP member is unsupported")
    if compressed_size > MAX_COMPRESSED_BYTES:
        raise RuntimeError(
            f"target compressed member exceeds preregistered source-resolution cap: {compressed_size}"
        )

    data_offset = local_data_offset(parent, member)
    inflater = zlib.decompressobj(-15)
    tail = bytearray()
    crc = 0
    produced = 0
    position = 0
    while position < compressed_size:
        length = min(CHUNK_BYTES, compressed_size - position)
        chunk = parent.read(data_offset + position, data_offset + position + length - 1)
        position += length
        decoded = inflater.decompress(chunk)
        produced += len(decoded)
        crc = zlib.crc32(decoded, crc)
        append_tail(tail, decoded)
    final = inflater.flush()
    produced += len(final)
    crc = zlib.crc32(final, crc)
    append_tail(tail, final)
    crc &= 0xFFFFFFFF
    if not inflater.eof:
        raise RuntimeError("raw Deflate stream did not reach EOF")
    if produced != uncompressed_size:
        raise RuntimeError(f"uncompressed-size mismatch: produced={produced} expected={uncompressed_size}")
    if crc != int(member["crc32"]):
        raise RuntimeError(f"CRC32 mismatch: produced={crc:08x} expected={int(member['crc32']):08x}")

    central, cd_offset, cd_size, expected_entries = nested_central_from_tail(
        bytes(tail), produced
    )
    members = zipidx.parse_central_directory(central)
    if len(members) != expected_entries:
        raise RuntimeError(
            f"nested member-count mismatch: parsed={len(members)} expected={expected_entries}"
        )
    videos = [row for row in members if row["is_video"]]
    bee_tests = [
        row for row in videos
        if Path(str(row["name"])).name.lower().startswith("bee_test_")
    ]

    result = {
        "schema": "interaction-sensing-v10-deflated-test-bundle-index-v1",
        "source_archive": {
            "figshare_file_id": archive["id"],
            "name": archive["name"],
            "size_bytes": archive["size_bytes"],
            "computed_md5": archive["computed_md5"],
            "download_url": archive["download_url"],
        },
        "nested_member": member,
        "streaming_resolution": {
            "compressed_payload_bytes_streamed": compressed_size,
            "uncompressed_bytes_processed": produced,
            "crc32_verified": True,
            "decompressed_member_payload_written": False,
            "retained_tail_bytes": len(tail),
            "total_http_range_bytes": counter.bytes_requested,
            "range_request_count": counter.requests,
        },
        "nested_zip": {
            "central_directory_offset": cd_offset,
            "central_directory_size": cd_size,
            "member_count": len(members),
            "video_count": len(videos),
            "members": members,
            "videos": videos,
        },
        "bee_test_count": len(bee_tests),
        "bee_test_videos": bee_tests,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    print("V10_TEST_BUNDLE_STREAMED true")
    print("V10_TEST_BUNDLE_COMPRESSED_BYTES", compressed_size)
    print("V10_TEST_BUNDLE_CRC32_VERIFIED true")
    print("V10_TEST_BUNDLE_MEMBERS", len(members))
    print("V10_TEST_BUNDLE_VIDEOS", len(videos))
    print("V10_TEST_BUNDLE_BEE_TESTS", len(bee_tests))
    for row in videos:
        print(
            "V10_TEST_VIDEO",
            row["name"],
            "method=" + str(row["compression_method"]),
            "compressed=" + str(row["compressed_size"]),
            "uncompressed=" + str(row["uncompressed_size"]),
        )


if __name__ == "__main__":
    main()
