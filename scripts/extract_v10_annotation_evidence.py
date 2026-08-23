#!/usr/bin/env python3
"""Extract small annotation/result artifacts for V10 provenance audit.

This script does not access video pixels or run either observer. It uses HTTP
Range reads into the byte-frozen Experiment_Data.zip and extracts small
pre-existing artifacts needed to distinguish Experiment 1 algorithm outputs and
aggregate summaries from an explicitly named human observation record supplied
for Experiment 2.
"""
from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path

import index_v10_remote_zip as zipidx


TARGETS = (
    "Experiment_Data/Experiment_1/Experiment1-Results.xlsx",
    "Experiment_Data/Experiment_1/Experiment_1-HyDaT_Results/Experiment_1-CSV_HyDaT.zip",
    "Experiment_Data/Experiment_1/Experiment_1-YOLO_Results/Experiment_1-CSV_YOLO.zip",
    "Experiment_Data/Experiment_2/Experiment_2 - Observations_Record.xlsx",
)
MAX_MEMBER_BYTES = 4 * 1024 * 1024


def local_data_offset(parent: zipidx.RemoteRangeView, member: dict[str, object]) -> int:
    offset = int(member["local_header_offset"])
    header = parent.read(offset, offset + 29)
    fields = struct.unpack("<4s5H3I2H", header)
    if fields[0] != zipidx.LOCAL_SIG:
        raise RuntimeError(f"local header mismatch for {member['name']}")
    flag_bits = int(fields[2])
    method = int(fields[3])
    filename_len = int(fields[9])
    extra_len = int(fields[10])
    if flag_bits & 0x1:
        raise RuntimeError(f"encrypted member unsupported: {member['name']}")
    if method != int(member["compression_method"]):
        raise RuntimeError(f"local/central compression mismatch: {member['name']}")
    return offset + 30 + filename_len + extra_len


def extract_member(parent: zipidx.RemoteRangeView, member: dict[str, object]) -> bytes:
    compressed_size = int(member["compressed_size"])
    uncompressed_size = int(member["uncompressed_size"])
    if compressed_size > MAX_MEMBER_BYTES or uncompressed_size > MAX_MEMBER_BYTES:
        raise RuntimeError(f"annotation-audit member exceeds small-file cap: {member['name']}")
    offset = local_data_offset(parent, member)
    payload = parent.read(offset, offset + compressed_size - 1) if compressed_size else b""
    method = int(member["compression_method"])
    if method == 0:
        decoded = payload
    elif method == 8:
        decoded = zlib.decompress(payload, -15)
    else:
        raise RuntimeError(f"unsupported compression method {method}: {member['name']}")
    if len(decoded) != uncompressed_size:
        raise RuntimeError(f"size mismatch for {member['name']}")
    crc = zlib.crc32(decoded) & 0xFFFFFFFF
    if crc != int(member["crc32"]):
        raise RuntimeError(f"CRC mismatch for {member['name']}")
    return decoded


def main() -> None:
    lock_path = Path("benchmarks/v10_real_video_source_lock.json")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "byte-identities-frozen; scientific-protocol-pending":
        raise RuntimeError("V10 annotation audit requires completed video byte lock")
    source = lock["derivation_chain"]["repository_file"]
    counter = zipidx.RequestCounter()
    parent = zipidx.RemoteRangeView(
        url=str(source["download_url"]),
        base_offset=0,
        size=int(source["size_bytes"]),
        root_size=int(source["size_bytes"]),
        counter=counter,
        label=str(source["name"]),
    )
    index = zipidx.index_zip(parent)
    by_name = {str(row["name"]): row for row in index["members"]}

    out_dir = Path(".v10/annotation-audit")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for name in TARGETS:
        member = by_name.get(name)
        if member is None:
            raise RuntimeError(f"required annotation-audit member missing: {name}")
        decoded = extract_member(parent, member)
        output = out_dir / Path(name).name
        output.write_bytes(decoded)
        rows.append(
            {
                "source_name": name,
                "output_name": output.name,
                "byte_count": len(decoded),
                "crc32_hex": f"{zlib.crc32(decoded) & 0xFFFFFFFF:08x}",
                "sha256": hashlib.sha256(decoded).hexdigest(),
                "compression_method": int(member["compression_method"]),
                "compressed_size": int(member["compressed_size"]),
                "local_header_offset": int(member["local_header_offset"]),
            }
        )

    manifest = {
        "schema": "interaction-sensing-v10-annotation-audit-extraction-v1",
        "source_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        "source_repository_file": {
            "figshare_file_id": int(source["figshare_file_id"]),
            "name": str(source["name"]),
            "computed_md5": str(source["computed_md5"]),
        },
        "extracted_files": rows,
        "outer_archive_range_bytes_requested": counter.bytes_requested,
        "video_pixels_accessed": False,
        "observer_execution": False,
        "v7_materialisation": False,
        "interpretation": "Extraction only. Experiment 1 HyDaT/YOLO files remain algorithm outputs unless independent human-reference provenance is established; the explicitly named Experiment 2 observation record is extracted only as a provenance-format comparator and is not a label source for the seven Experiment 1 videos.",
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print("V10_ANNOTATION_AUDIT_FILES", len(rows))
    print("V10_ANNOTATION_AUDIT_RANGE_BYTES", counter.bytes_requested)
    print("V10_VIDEO_PIXELS_ACCESSED false")
    print("V10_OBSERVER_EXECUTION false")
    for row in rows:
        print("V10_ANNOTATION_FILE", row["output_name"], row["byte_count"], row["sha256"])


if __name__ == "__main__":
    main()
