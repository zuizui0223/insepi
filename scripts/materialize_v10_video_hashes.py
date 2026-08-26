#!/usr/bin/env python3
"""Compute byte-level SHA-256 identities for the already-frozen V10 videos.

This script does not run either observer and does not select clips. The source
list must already be frozen in ``benchmarks/v10_real_video_source_lock.json``.
It streams only the locked nested test-video bundle from Figshare, verifies the
outer member's size/CRC, writes the decoded nested ZIP to temporary storage,
then hashes all seven locked MP4 members without writing individual videos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import tempfile
import zipfile
import zlib
from pathlib import Path

import index_v10_remote_zip as zipidx


CHUNK_BYTES = 32 * 1024 * 1024
MAX_COMPRESSED_BYTES = 600 * 1024 * 1024


def local_data_offset(parent: zipidx.RemoteRangeView, member: dict[str, object]) -> int:
    offset = int(member["local_header_offset"])
    header = parent.read(offset, offset + 29)
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != zipidx.LOCAL_SIG:
        raise RuntimeError("nested test-bundle local-header signature mismatch")
    flag_bits = int(fields[2])
    method = int(fields[3])
    filename_len = int(fields[9])
    extra_len = int(fields[10])
    if flag_bits != 0:
        raise RuntimeError(f"unexpected nested test-bundle flag bits: {flag_bits}")
    if method != int(member["compression_method"]):
        raise RuntimeError("nested test-bundle local/lock compression mismatch")
    return offset + 30 + filename_len + extra_len


def stream_nested_zip(
    parent: zipidx.RemoteRangeView,
    member: dict[str, object],
    output_path: Path,
) -> tuple[str, int, int]:
    compressed_size = int(member["compressed_size"])
    expected_size = int(member["uncompressed_size"])
    expected_crc = int(str(member["crc32_hex"]), 16)
    if compressed_size > MAX_COMPRESSED_BYTES:
        raise RuntimeError(
            f"locked nested test bundle exceeds byte-lock transfer cap: {compressed_size}"
        )
    if int(member["compression_method"]) != 8:
        raise RuntimeError("locked nested test bundle is no longer raw Deflate method 8")

    data_offset = local_data_offset(parent, member)
    inflater = zlib.decompressobj(-15)
    sha256 = hashlib.sha256()
    crc32 = 0
    produced = 0
    position = 0
    with output_path.open("wb") as handle:
        while position < compressed_size:
            length = min(CHUNK_BYTES, compressed_size - position)
            chunk = parent.read(
                data_offset + position,
                data_offset + position + length - 1,
            )
            position += length
            decoded = inflater.decompress(chunk)
            if decoded:
                handle.write(decoded)
                sha256.update(decoded)
                crc32 = zlib.crc32(decoded, crc32)
                produced += len(decoded)
        final = inflater.flush()
        if final:
            handle.write(final)
            sha256.update(final)
            crc32 = zlib.crc32(final, crc32)
            produced += len(final)

    crc32 &= 0xFFFFFFFF
    if not inflater.eof:
        raise RuntimeError("locked nested test-bundle Deflate stream did not reach EOF")
    if inflater.unused_data:
        raise RuntimeError("unexpected bytes after locked nested test-bundle Deflate stream")
    if produced != expected_size:
        raise RuntimeError(
            f"nested test-bundle size mismatch: got={produced} expected={expected_size}"
        )
    if crc32 != expected_crc:
        raise RuntimeError(
            f"nested test-bundle CRC mismatch: got={crc32:08x} expected={expected_crc:08x}"
        )
    if output_path.stat().st_size != expected_size:
        raise RuntimeError("temporary nested ZIP byte size differs from verified stream size")
    return sha256.hexdigest(), crc32, produced


def hash_zip_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    with zf.open(info, "r") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            count += len(chunk)
    if count != info.file_size:
        raise RuntimeError(f"member size changed while hashing: {info.filename}")
    return digest.hexdigest(), count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock",
        type=Path,
        default=Path("benchmarks/v10_real_video_source_lock.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".v10/v10_video_hash_receipt.json"),
    )
    args = parser.parse_args()

    lock_bytes = args.lock.read_bytes()
    lock = json.loads(lock_bytes)
    if lock.get("schema") != "interaction-sensing-v10-real-video-source-lock-v1":
        raise RuntimeError("unexpected V10 source-lock schema")
    selected = lock.get("videos")
    if not isinstance(selected, list) or len(selected) != 7:
        raise RuntimeError("V10 byte lock requires exactly seven pre-frozen video members")

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

    with tempfile.TemporaryDirectory(prefix="v10-byte-lock-") as temp_dir:
        nested_path = Path(temp_dir) / "Experiment_1-Test_Videos.zip"
        nested_sha256, nested_crc32, nested_size = stream_nested_zip(
            parent, nested, nested_path
        )

        with zipfile.ZipFile(nested_path, "r") as zf:
            infos = {info.filename: info for info in zf.infolist()}
            actual_videos = sorted(
                info.filename
                for info in zf.infolist()
                if info.filename.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".m4v"))
            )
            expected_names = [str(row["name"]) for row in selected]
            if actual_videos != sorted(expected_names):
                raise RuntimeError(
                    "nested ZIP video membership differs from pre-frozen seven-video source lock"
                )

            receipts: list[dict[str, object]] = []
            for row in selected:
                name = str(row["name"])
                info = infos.get(name)
                if info is None:
                    raise RuntimeError(f"locked video missing from nested ZIP: {name}")
                expected_crc = int(str(row["crc32_hex"]), 16)
                checks = {
                    "compression_method": (info.compress_type, int(row["compression_method"])),
                    "compressed_size": (info.compress_size, int(row["compressed_size"])),
                    "uncompressed_size": (info.file_size, int(row["uncompressed_size"])),
                    "crc32": (info.CRC, expected_crc),
                    "local_header_offset": (info.header_offset, int(row["local_header_offset"])),
                }
                mismatches = {
                    key: {"actual": actual, "expected": expected}
                    for key, (actual, expected) in checks.items()
                    if actual != expected
                }
                if mismatches:
                    raise RuntimeError(f"locked member metadata mismatch for {name}: {mismatches}")
                sha256, byte_count = hash_zip_member(zf, info)
                expected_sha = row.get("sha256")
                if expected_sha is not None and str(expected_sha) != sha256:
                    raise RuntimeError(
                        f"previously frozen SHA-256 mismatch for {name}: {sha256} != {expected_sha}"
                    )
                receipts.append(
                    {
                        "index": int(row["index"]),
                        "name": name,
                        "byte_count": byte_count,
                        "crc32_hex": f"{info.CRC:08x}",
                        "sha256": sha256,
                    }
                )

    receipt = {
        "schema": "interaction-sensing-v10-video-byte-receipt-v1",
        "source_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "source_repository_file": {
            "figshare_file_id": int(source["figshare_file_id"]),
            "name": str(source["name"]),
            "size_bytes": int(source["size_bytes"]),
            "computed_md5": str(source["computed_md5"]),
            "download_url": str(source["download_url"]),
        },
        "nested_test_bundle": {
            "name": str(nested["name"]),
            "byte_count": nested_size,
            "crc32_hex": f"{nested_crc32:08x}",
            "sha256": nested_sha256,
        },
        "selected_video_count": len(receipts),
        "videos": receipts,
        "transport": {
            "http_range_only_for_outer_archive": True,
            "outer_archive_bytes_requested": counter.bytes_requested,
            "outer_archive_range_request_count": counter.requests,
            "temporary_nested_zip_written": True,
            "temporary_nested_zip_deleted_after_verification": True,
            "individual_video_files_written": False,
        },
        "observer_execution": False,
        "v7_materialisation": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    print("V10_BYTE_RECEIPT_VIDEO_COUNT", len(receipts))
    print("V10_NESTED_ZIP_SHA256", nested_sha256)
    print("V10_OUTER_BYTES_REQUESTED", counter.bytes_requested)
    print("V10_INDIVIDUAL_VIDEO_FILES_WRITTEN false")
    print("V10_OBSERVER_EXECUTION false")
    for row in receipts:
        print("V10_VIDEO_SHA256", row["name"], row["byte_count"], row["sha256"])


if __name__ == "__main__":
    main()
