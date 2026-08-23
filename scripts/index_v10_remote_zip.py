#!/usr/bin/env python3
"""Index remote/nested V10 ZIPs with HTTP Range requests only.

This script is provenance discovery, not scientific evaluation. It refuses full
archive downloads. It reads only ZIP metadata (EOCD/Zip64, central directories,
and local headers). If the target nested ZIP is stored without compression, the
nested ZIP is exposed as a virtual byte range and indexed in-place.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen


EOCD_SIG = b"PK\x05\x06"
ZIP64_LOCATOR_SIG = b"PK\x06\x07"
ZIP64_EOCD_SIG = b"PK\x06\x06"
CENTRAL_SIG = b"PK\x01\x02"
LOCAL_SIG = b"PK\x03\x04"
ZIP64_EXTRA_ID = 0x0001
MAX_CENTRAL_DIRECTORY_BYTES = 32 * 1024 * 1024
TAIL_BYTES = 256 * 1024
VIDEO_SUFFIXES = (".mp4", ".avi", ".mov", ".mkv", ".m4v")
ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".gz", ".7z")


def fetch_range(url: str, start: int, end: int) -> tuple[bytes, str]:
    request = Request(
        url,
        headers={
            "User-Agent": "interaction-sensing-v10-range-index/2",
            "Range": f"bytes={start}-{end}",
            "Accept-Encoding": "identity",
        },
    )
    with urlopen(request, timeout=120) as response:
        status = getattr(response, "status", None)
        content_range = response.headers.get("Content-Range", "")
        if status != 206 or not content_range:
            raise RuntimeError(
                f"server did not honor HTTP Range safely: status={status} Content-Range={content_range!r}"
            )
        payload = response.read()
    return payload, content_range


def parse_content_range(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value.strip())
    if not match:
        raise ValueError(f"unexpected Content-Range: {value!r}")
    return tuple(int(match.group(index)) for index in (1, 2, 3))


@dataclass
class RequestCounter:
    bytes_requested: int = 0
    requests: int = 0


@dataclass
class RemoteRangeView:
    url: str
    base_offset: int
    size: int
    root_size: int
    counter: RequestCounter
    label: str

    def read(self, start: int, end: int) -> bytes:
        if start < 0 or end < start or end >= self.size:
            raise ValueError(
                f"logical range outside {self.label}: start={start} end={end} size={self.size}"
            )
        absolute_start = self.base_offset + start
        absolute_end = self.base_offset + end
        payload, content_range = fetch_range(self.url, absolute_start, absolute_end)
        got_start, got_end, total = parse_content_range(content_range)
        if (got_start, got_end, total) != (absolute_start, absolute_end, self.root_size):
            raise RuntimeError(
                f"Content-Range mismatch for {self.label}: {content_range!r}"
            )
        if len(payload) != end - start + 1:
            raise RuntimeError(f"short ranged read for {self.label}")
        self.counter.bytes_requested += len(payload)
        self.counter.requests += 1
        return payload


def find_eocd(tail: bytes) -> int:
    position = tail.rfind(EOCD_SIG)
    if position < 0:
        raise RuntimeError("ZIP EOCD signature not found in ranged tail")
    if len(tail) - position < 22:
        raise RuntimeError("truncated ZIP EOCD")
    comment_len = struct.unpack_from("<H", tail, position + 20)[0]
    if position + 22 + comment_len > len(tail):
        raise RuntimeError("ZIP EOCD comment extends beyond ranged tail")
    return position


def central_directory_location(
    view: RemoteRangeView, tail: bytes, tail_start: int, eocd_pos: int
) -> tuple[int, int, int]:
    fields = struct.unpack_from("<4s4H2IH", tail, eocd_pos)
    _, _disk_no, _cd_disk, entries_disk, entries_total, cd_size32, cd_offset32, _comment_len = fields
    needs_zip64 = (
        entries_disk == 0xFFFF
        or entries_total == 0xFFFF
        or cd_size32 == 0xFFFFFFFF
        or cd_offset32 == 0xFFFFFFFF
    )
    if not needs_zip64:
        return int(cd_offset32), int(cd_size32), int(entries_total)

    locator_logical = tail_start + eocd_pos - 20
    if locator_logical < 0:
        raise RuntimeError("invalid Zip64 locator offset")
    local_pos = eocd_pos - 20
    if local_pos >= 0 and tail[local_pos : local_pos + 4] == ZIP64_LOCATOR_SIG:
        locator = tail[local_pos : local_pos + 20]
    else:
        locator = view.read(locator_logical, locator_logical + 19)
    sig, _zip64_disk, zip64_offset, _total_disks = struct.unpack("<4sIQI", locator)
    if sig != ZIP64_LOCATOR_SIG:
        raise RuntimeError("Zip64 locator signature mismatch")
    record = view.read(int(zip64_offset), int(zip64_offset) + 55)
    unpacked = struct.unpack_from("<4sQ2H2I4Q", record, 0)
    if unpacked[0] != ZIP64_EOCD_SIG:
        raise RuntimeError("Zip64 EOCD signature mismatch")
    return int(unpacked[9]), int(unpacked[8]), int(unpacked[7])


def parse_zip64_extra(
    extra: bytes,
    *,
    uncompressed32: int,
    compressed32: int,
    local_offset32: int,
    disk_start32: int,
) -> tuple[int, int, int, int]:
    uncompressed = int(uncompressed32)
    compressed = int(compressed32)
    local_offset = int(local_offset32)
    disk_start = int(disk_start32)
    cursor = 0
    zip64_payload: bytes | None = None
    while cursor + 4 <= len(extra):
        header_id, size = struct.unpack_from("<HH", extra, cursor)
        cursor += 4
        payload = extra[cursor : cursor + size]
        cursor += size
        if header_id == ZIP64_EXTRA_ID:
            zip64_payload = payload
            break
    if zip64_payload is None:
        if 0xFFFFFFFF in (uncompressed32, compressed32, local_offset32) or disk_start32 == 0xFFFF:
            raise RuntimeError("Zip64 sentinel present without Zip64 extra field")
        return uncompressed, compressed, local_offset, disk_start

    cursor = 0

    def take_q() -> int:
        nonlocal cursor
        if cursor + 8 > len(zip64_payload):
            raise RuntimeError("truncated Zip64 extra field")
        value = struct.unpack_from("<Q", zip64_payload, cursor)[0]
        cursor += 8
        return int(value)

    def take_i() -> int:
        nonlocal cursor
        if cursor + 4 > len(zip64_payload):
            raise RuntimeError("truncated Zip64 disk field")
        value = struct.unpack_from("<I", zip64_payload, cursor)[0]
        cursor += 4
        return int(value)

    if uncompressed32 == 0xFFFFFFFF:
        uncompressed = take_q()
    if compressed32 == 0xFFFFFFFF:
        compressed = take_q()
    if local_offset32 == 0xFFFFFFFF:
        local_offset = take_q()
    if disk_start32 == 0xFFFF:
        disk_start = take_i()
    return uncompressed, compressed, local_offset, disk_start


def parse_central_directory(data: bytes) -> list[dict[str, object]]:
    members: list[dict[str, object]] = []
    offset = 0
    while offset < len(data):
        if len(data) - offset < 46:
            raise RuntimeError(f"truncated central-directory entry at offset {offset}")
        fields = struct.unpack_from("<4s6H3I5H2I", data, offset)
        if fields[0] != CENTRAL_SIG:
            raise RuntimeError(f"central-directory signature mismatch at offset {offset}")
        flag_bits = int(fields[3])
        compression_method = int(fields[4])
        crc32 = int(fields[7])
        compressed32 = int(fields[8])
        uncompressed32 = int(fields[9])
        filename_len = int(fields[10])
        extra_len = int(fields[11])
        comment_len = int(fields[12])
        disk_start32 = int(fields[13])
        local_offset32 = int(fields[16])
        start = offset + 46
        filename_raw = data[start : start + filename_len]
        extra = data[start + filename_len : start + filename_len + extra_len]
        encoding = "utf-8" if flag_bits & 0x800 else "cp437"
        filename = filename_raw.decode(encoding, errors="replace")
        uncompressed, compressed, local_offset, disk_start = parse_zip64_extra(
            extra,
            uncompressed32=uncompressed32,
            compressed32=compressed32,
            local_offset32=local_offset32,
            disk_start32=disk_start32,
        )
        lower = filename.lower()
        members.append(
            {
                "name": filename,
                "compression_method": compression_method,
                "crc32": crc32,
                "compressed_size": compressed,
                "uncompressed_size": uncompressed,
                "local_header_offset": local_offset,
                "disk_start": disk_start,
                "flag_bits": flag_bits,
                "is_video": lower.endswith(VIDEO_SUFFIXES),
                "is_archive": lower.endswith(ARCHIVE_SUFFIXES),
            }
        )
        offset = start + filename_len + extra_len + comment_len
    return members


def index_zip(view: RemoteRangeView) -> dict[str, object]:
    tail_start = max(0, view.size - TAIL_BYTES)
    tail = view.read(tail_start, view.size - 1)
    eocd_pos = find_eocd(tail)
    cd_offset, cd_size, expected_entries = central_directory_location(
        view, tail, tail_start, eocd_pos
    )
    if cd_size <= 0 or cd_size > MAX_CENTRAL_DIRECTORY_BYTES:
        raise RuntimeError(
            f"central directory size outside safe range-only bound for {view.label}: {cd_size}"
        )
    central = view.read(cd_offset, cd_offset + cd_size - 1)
    members = parse_central_directory(central)
    if len(members) != expected_entries:
        raise RuntimeError(
            f"member-count mismatch for {view.label}: parsed={len(members)} expected={expected_entries}"
        )
    videos = [row for row in members if row["is_video"]]
    archives = [row for row in members if row["is_archive"]]
    return {
        "label": view.label,
        "size_bytes": view.size,
        "central_directory_offset": cd_offset,
        "central_directory_size": cd_size,
        "member_count": len(members),
        "video_count": len(videos),
        "archive_count": len(archives),
        "members": members,
        "videos": videos,
        "archives": archives,
    }


def stored_member_view(parent: RemoteRangeView, member: dict[str, object]) -> RemoteRangeView:
    if int(member["disk_start"]) != 0:
        raise RuntimeError("multi-disk ZIP members are unsupported")
    if int(member["compression_method"]) != 0:
        raise RuntimeError(
            f"nested archive is not stored: method={member['compression_method']}"
        )
    if int(member["compressed_size"]) != int(member["uncompressed_size"]):
        raise RuntimeError("stored nested archive has unequal compressed/uncompressed sizes")
    local_offset = int(member["local_header_offset"])
    header = parent.read(local_offset, local_offset + 29)
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != LOCAL_SIG:
        raise RuntimeError("local-header signature mismatch")
    local_method = int(fields[3])
    filename_len = int(fields[9])
    extra_len = int(fields[10])
    if local_method != int(member["compression_method"]):
        raise RuntimeError("local/central compression-method mismatch")
    data_offset = local_offset + 30 + filename_len + extra_len
    size = int(member["compressed_size"])
    if data_offset + size > parent.size:
        raise RuntimeError("nested stored member extends beyond parent ZIP")
    return RemoteRangeView(
        url=parent.url,
        base_offset=parent.base_offset + data_offset,
        size=size,
        root_size=parent.root_size,
        counter=parent.counter,
        label=str(member["name"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-resolution", type=Path, default=Path(".v10/source-resolution.json")
    )
    parser.add_argument("--archive-name", default="Honeybee_videos.zip")
    parser.add_argument("--nested-name", default="Honeybee_videos/Scaevola.zip")
    parser.add_argument(
        "--output", type=Path, default=Path(".v10/honeybee-videos-index.json")
    )
    args = parser.parse_args()

    source = json.loads(args.source_resolution.read_text(encoding="utf-8"))
    matches = [row for row in source["files"] if row["name"] == args.archive_name]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {args.archive_name!r}, found {len(matches)}"
        )
    archive = matches[0]
    counter = RequestCounter()
    outer = RemoteRangeView(
        url=str(archive["download_url"]),
        base_offset=0,
        size=int(archive["size_bytes"]),
        root_size=int(archive["size_bytes"]),
        counter=counter,
        label=str(archive["name"]),
    )
    outer_index = index_zip(outer)
    nested_matches = [row for row in outer_index["members"] if row["name"] == args.nested_name]
    if len(nested_matches) != 1:
        nested_state = f"target-member-count-{len(nested_matches)}"
        nested_index = None
    else:
        target = nested_matches[0]
        if int(target["compression_method"]) != 0:
            nested_state = f"nested-compressed-method-{target['compression_method']}"
            nested_index = None
        else:
            nested_view = stored_member_view(outer, target)
            nested_index = index_zip(nested_view)
            nested_state = "nested-range-indexed"

    bee_tests: list[dict[str, object]] = []
    if nested_index is not None:
        bee_tests = [
            row
            for row in nested_index["videos"]
            if Path(str(row["name"])).name.lower().startswith("bee_test_")
        ]

    result = {
        "schema": "interaction-sensing-v10-remote-zip-index-v2",
        "archive": {
            "figshare_file_id": archive["id"],
            "name": archive["name"],
            "size_bytes": archive["size_bytes"],
            "computed_md5": archive["computed_md5"],
            "download_url": archive["download_url"],
        },
        "http_range_only": True,
        "member_payload_downloaded": False,
        "bytes_requested_for_index": counter.bytes_requested,
        "range_request_count": counter.requests,
        "fraction_of_outer_archive_requested": counter.bytes_requested / outer.size,
        "outer_zip": outer_index,
        "nested_target": args.nested_name,
        "nested_state": nested_state,
        "nested_zip": nested_index,
        "bee_test_count": len(bee_tests),
        "bee_test_videos": bee_tests,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    print("V10_REMOTE_ZIP_RANGE_ONLY true")
    print("V10_OUTER_ZIP_SIZE", outer.size)
    print("V10_INDEX_BYTES", counter.bytes_requested)
    print("V10_RANGE_REQUESTS", counter.requests)
    print("V10_OUTER_MEMBERS", outer_index["member_count"])
    for row in outer_index["members"]:
        print(
            "V10_OUTER_MEMBER",
            row["name"],
            "method=" + str(row["compression_method"]),
            "compressed=" + str(row["compressed_size"]),
            "uncompressed=" + str(row["uncompressed_size"]),
            "offset=" + str(row["local_header_offset"]),
        )
    print("V10_NESTED_STATE", nested_state)
    if nested_index is not None:
        print("V10_NESTED_MEMBERS", nested_index["member_count"])
        print("V10_NESTED_VIDEOS", nested_index["video_count"])
    print("V10_BEE_TEST_COUNT", len(bee_tests))
    for row in bee_tests:
        print(
            "V10_BEE_TEST_MEMBER",
            row["name"],
            "method=" + str(row["compression_method"]),
            "compressed=" + str(row["compressed_size"]),
            "uncompressed=" + str(row["uncompressed_size"]),
            "offset=" + str(row["local_header_offset"]),
        )


if __name__ == "__main__":
    main()
