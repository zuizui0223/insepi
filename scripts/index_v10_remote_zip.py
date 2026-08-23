#!/usr/bin/env python3
"""Index a remote Figshare ZIP using HTTP Range requests only.

The script is provenance discovery for V10. It refuses a server response that
would stream the full archive and only reads the EOCD/Zip64 records plus the
central directory. It does not download member payload bytes.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path
from urllib.request import Request, urlopen


EOCD_SIG = b"PK\x05\x06"
ZIP64_LOCATOR_SIG = b"PK\x06\x07"
ZIP64_EOCD_SIG = b"PK\x06\x06"
CENTRAL_SIG = b"PK\x01\x02"
MAX_CENTRAL_DIRECTORY_BYTES = 32 * 1024 * 1024
TAIL_BYTES = 256 * 1024


def fetch_range(url: str, start: int | None = None, end: int | None = None, *, suffix: int | None = None) -> tuple[bytes, str]:
    if suffix is not None:
        range_value = f"bytes=-{suffix}"
    else:
        if start is None:
            raise ValueError("start is required for non-suffix range")
        range_value = f"bytes={start}-{'' if end is None else end}"
    request = Request(
        url,
        headers={
            "User-Agent": "interaction-sensing-v10-range-index/1",
            "Range": range_value,
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


def central_directory_location(url: str, tail: bytes, tail_start: int, eocd_pos: int) -> tuple[int, int, int, int]:
    fields = struct.unpack_from("<4s4H2IH", tail, eocd_pos)
    _, _disk_no, _cd_disk, entries_disk, entries_total, cd_size32, cd_offset32, _comment_len = fields
    needs_zip64 = (
        entries_disk == 0xFFFF
        or entries_total == 0xFFFF
        or cd_size32 == 0xFFFFFFFF
        or cd_offset32 == 0xFFFFFFFF
    )
    if not needs_zip64:
        return int(cd_offset32), int(cd_size32), int(entries_total), 0

    locator_absolute = tail_start + eocd_pos - 20
    if locator_absolute < 0:
        raise RuntimeError("invalid Zip64 locator offset")
    locator: bytes
    local_pos = eocd_pos - 20
    extra_requested = 0
    if local_pos >= 0 and tail[local_pos : local_pos + 4] == ZIP64_LOCATOR_SIG:
        locator = tail[local_pos : local_pos + 20]
    else:
        locator, _ = fetch_range(url, locator_absolute, locator_absolute + 19)
        extra_requested += len(locator)
    sig, _zip64_disk, zip64_offset, _total_disks = struct.unpack("<4sIQI", locator)
    if sig != ZIP64_LOCATOR_SIG:
        raise RuntimeError("Zip64 locator signature mismatch")
    record, _ = fetch_range(url, int(zip64_offset), int(zip64_offset) + 55)
    extra_requested += len(record)
    if len(record) < 56:
        raise RuntimeError("truncated Zip64 EOCD record")
    unpacked = struct.unpack_from("<4sQ2H2I4Q", record, 0)
    sig64 = unpacked[0]
    if sig64 != ZIP64_EOCD_SIG:
        raise RuntimeError("Zip64 EOCD signature mismatch")
    entries_total64 = int(unpacked[7])
    cd_size64 = int(unpacked[8])
    cd_offset64 = int(unpacked[9])
    return cd_offset64, cd_size64, entries_total64, extra_requested


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
        compressed_size = int(fields[8])
        uncompressed_size = int(fields[9])
        filename_len = int(fields[10])
        extra_len = int(fields[11])
        comment_len = int(fields[12])
        local_header_offset = int(fields[16])
        start = offset + 46
        filename_raw = data[start : start + filename_len]
        encoding = "utf-8" if flag_bits & 0x800 else "cp437"
        filename = filename_raw.decode(encoding, errors="replace")
        members.append(
            {
                "name": filename,
                "compressed_size_32": compressed_size,
                "uncompressed_size_32": uncompressed_size,
                "local_header_offset_32": local_header_offset,
                "flag_bits": flag_bits,
                "is_video": filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".m4v")),
            }
        )
        offset = start + filename_len + extra_len + comment_len
    return members


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-resolution", type=Path, default=Path(".v10/source-resolution.json"))
    parser.add_argument("--archive-name", default="Honeybee_videos.zip")
    parser.add_argument("--output", type=Path, default=Path(".v10/honeybee-videos-index.json"))
    args = parser.parse_args()

    source = json.loads(args.source_resolution.read_text(encoding="utf-8"))
    matches = [row for row in source["files"] if row["name"] == args.archive_name]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {args.archive_name!r}, found {len(matches)}")
    archive = matches[0]
    url = str(archive["download_url"])
    expected_size = int(archive["size_bytes"])

    tail, content_range = fetch_range(url, suffix=TAIL_BYTES)
    tail_start, tail_end, total_size = parse_content_range(content_range)
    if total_size != expected_size:
        raise RuntimeError(f"Figshare size mismatch: API={expected_size} ranged={total_size}")
    if tail_end != total_size - 1:
        raise RuntimeError("suffix range did not end at archive EOF")
    eocd_pos = find_eocd(tail)
    cd_offset, cd_size, expected_entries, extra_requested = central_directory_location(
        url, tail, tail_start, eocd_pos
    )
    if cd_size <= 0 or cd_size > MAX_CENTRAL_DIRECTORY_BYTES:
        raise RuntimeError(f"central directory size outside safe range-only bound: {cd_size}")
    central, central_range = fetch_range(url, cd_offset, cd_offset + cd_size - 1)
    cd_start, cd_end, cd_total = parse_content_range(central_range)
    if (cd_start, cd_end, cd_total) != (cd_offset, cd_offset + cd_size - 1, total_size):
        raise RuntimeError("central-directory Content-Range mismatch")
    members = parse_central_directory(central)
    if len(members) != expected_entries:
        raise RuntimeError(f"member-count mismatch: parsed={len(members)} expected={expected_entries}")
    videos = [row for row in members if row["is_video"]]
    bee_tests = [
        row for row in videos
        if Path(str(row["name"])).name.lower().startswith("bee_test_")
    ]
    bytes_requested = len(tail) + extra_requested + len(central)
    index = {
        "schema": "interaction-sensing-v10-remote-zip-index-v1",
        "archive": {
            "figshare_file_id": archive["id"],
            "name": archive["name"],
            "size_bytes": expected_size,
            "computed_md5": archive["computed_md5"],
            "download_url": url,
        },
        "http_range_only": True,
        "archive_payload_downloaded": False,
        "bytes_requested_for_index": bytes_requested,
        "fraction_of_archive_requested": bytes_requested / total_size,
        "central_directory_offset": cd_offset,
        "central_directory_size": cd_size,
        "member_count": len(members),
        "video_count": len(videos),
        "bee_test_count": len(bee_tests),
        "members": members,
        "videos": videos,
        "bee_test_videos": bee_tests,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    print("V10_REMOTE_ZIP_RANGE_ONLY true")
    print("V10_REMOTE_ZIP_SIZE", total_size)
    print("V10_REMOTE_ZIP_INDEX_BYTES", bytes_requested)
    print("V10_REMOTE_ZIP_MEMBERS", len(members))
    print("V10_REMOTE_ZIP_VIDEOS", len(videos))
    print("V10_REMOTE_ZIP_BEE_TESTS", len(bee_tests))
    for row in bee_tests:
        print("V10_BEE_TEST_MEMBER", row["name"], row["compressed_size_32"], row["uncompressed_size_32"])


if __name__ == "__main__":
    main()
