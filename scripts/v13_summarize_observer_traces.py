#!/usr/bin/env python3
"""Convert V13 exact-observer sample traces to safe phase/block responses."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Mapping

from interaction_sensing.physical_artifact_v13 import load_pixel_artifact, sha256_file
from interaction_sensing.physical_measurement_v13 import (
    PhaseSummary,
    build_block_responses,
    phase_summary,
)

POLLIPI_COMMIT = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
INSEPI_COMMIT = "980813bab996909020140fad5bd83b055eb3db9c"
POLLIPI_SCHEMA = "pollipi-insepi-v13-pollipi-phase-trace-v1"
INSEPI_SCHEMA = "pollipi-insepi-v13-insepi-phase-trace-v1"

POLLIPI_RESULT_KEYS = {
    "record_type", "schema", "block_index", "opaque_block_id", "split",
    "phase_index", "phase_order", "phase_name", "sample_index",
    "pollipi_state", "pollipi_reason", "global_synchrony",
    "active_cell_proportion", "estimated_global_shift",
}
INSEPI_RESULT_KEYS = {
    "record_type", "schema", "block_index", "opaque_block_id", "split",
    "phase_index", "phase_order", "phase_name", "sample_index",
    "inferred_noise_source", "observability_state", "false_event_risk",
    "missed_event_risk", "attribution_risk", "local_structure_loss",
    "occlusion_threshold",
}


def _read_trace(path: Path, schema: str, source_commit: str, result_keys: set[str]):
    payloads = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if len(payloads) != 5761:
        raise RuntimeError(f"V13 trace must contain provenance + 5760 results: {path}")
    provenance = payloads[0]
    if provenance.get("record_type") != "provenance" or provenance.get("schema") != schema:
        raise RuntimeError(f"V13 trace provenance schema mismatch: {path}")
    if provenance.get("source_commit") != source_commit:
        raise RuntimeError(f"V13 trace observer commit mismatch: {path}")
    if provenance.get("truth_metadata_received") is not False:
        raise RuntimeError(f"V13 observer trace reports truth metadata exposure: {path}")
    rows = payloads[1:]
    for index, row in enumerate(rows):
        if set(row) != result_keys:
            raise RuntimeError(f"V13 trace result key set changed at row {index}: {path}")
        if row.get("record_type") != "result" or row.get("schema") != schema:
            raise RuntimeError(f"V13 trace result schema mismatch at row {index}: {path}")
    return provenance, rows


def _expected_sample_rows(artifact):
    for phase in artifact.registry:
        for sample_index in range(8):
            yield {
                "block_index": int(phase["block_index"]),
                "opaque_block_id": str(phase["opaque_block_id"]),
                "split": str(phase["split"]),
                "phase_index": int(phase["phase_index"]),
                "phase_order": int(phase["phase_order"]),
                "phase_name": str(phase["phase_name"]),
                "sample_index": sample_index,
            }


def _validate_order(rows, artifact, label: str) -> None:
    safe_keys = (
        "block_index", "opaque_block_id", "split", "phase_index",
        "phase_order", "phase_name", "sample_index",
    )
    for index, (row, expected) in enumerate(zip(rows, _expected_sample_rows(artifact), strict=True)):
        actual = {key: row[key] for key in safe_keys}
        if actual != expected:
            raise RuntimeError(f"V13 {label} trace order/metadata mismatch at result {index}: {actual} != {expected}")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summarize(artifact_dir: Path, pollipi_trace: Path, insepi_trace: Path, output_dir: Path) -> Mapping[str, object]:
    artifact = load_pixel_artifact(artifact_dir)
    pixel_receipt_sha = sha256_file(artifact_dir / "v13_pixel_receipt.json")
    p_prov, p_rows = _read_trace(pollipi_trace, POLLIPI_SCHEMA, POLLIPI_COMMIT, POLLIPI_RESULT_KEYS)
    i_prov, i_rows = _read_trace(insepi_trace, INSEPI_SCHEMA, INSEPI_COMMIT, INSEPI_RESULT_KEYS)
    for provenance, label in ((p_prov, "PolliPi"), (i_prov, "InsePi")):
        if provenance.get("pixel_receipt_sha256") != pixel_receipt_sha:
            raise RuntimeError(f"V13 {label} trace used a different pixel receipt")
        if provenance.get("frames_raw_sha256") != artifact.receipt["array_contract"]["frames_raw_sha256"]:
            raise RuntimeError(f"V13 {label} frames raw hash mismatch")
        if provenance.get("backgrounds_raw_sha256") != artifact.receipt["array_contract"]["backgrounds_raw_sha256"]:
            raise RuntimeError(f"V13 {label} backgrounds raw hash mismatch")
    _validate_order(p_rows, artifact, "PolliPi")
    _validate_order(i_rows, artifact, "InsePi")

    phase_rows: list[dict[str, object]] = []
    block_summaries: dict[str, dict[str, PhaseSummary]] = {}
    block_split: dict[str, str] = {}
    for phase_index, phase in enumerate(artifact.registry):
        start = phase_index * 8
        stop = start + 8
        summary = phase_summary(p_rows[start:stop], i_rows[start:stop])
        block_id = str(phase["opaque_block_id"])
        phase_name = str(phase["phase_name"])
        block_summaries.setdefault(block_id, {})[phase_name] = summary
        block_split[block_id] = str(phase["split"])
        phase_rows.append({
            "block_id": block_id,
            "split": str(phase["split"]),
            "phase_name": phase_name,
            "phase_order": int(phase["phase_order"]),
            "evidence_median": summary.evidence,
            "observability_median": summary.observability,
            "sample_count": summary.sample_count,
        })

    response_rows: list[dict[str, object]] = []
    for block_id in sorted(block_summaries):
        response = build_block_responses(block_summaries[block_id])
        response_rows.append({
            "block_id": block_id,
            "split": block_split[block_id],
            "event_restore_delta_evidence": response["event_restore"][0],
            "event_restore_delta_observability": response["event_restore"][1],
            "observability_restore_delta_evidence": response["observability_restore"][0],
            "observability_restore_delta_observability": response["observability_restore"][1],
            "shared_restore_delta_evidence": response["shared_restore"][0],
            "shared_restore_delta_observability": response["shared_restore"][1],
        })
    if len(response_rows) != 180:
        raise RuntimeError(f"V13 response table must contain 180 blocks, got {len(response_rows)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    phase_path = output_dir / "v13_phase_summaries.csv"
    response_path = output_dir / "v13_safe_block_responses.csv"
    receipt_path = output_dir / "v13_response_receipt.json"
    _write_csv(
        phase_path,
        ["block_id", "split", "phase_name", "phase_order", "evidence_median", "observability_median", "sample_count"],
        phase_rows,
    )
    _write_csv(
        response_path,
        [
            "block_id", "split",
            "event_restore_delta_evidence", "event_restore_delta_observability",
            "observability_restore_delta_evidence", "observability_restore_delta_observability",
            "shared_restore_delta_evidence", "shared_restore_delta_observability",
        ],
        response_rows,
    )
    receipt = {
        "schema": "interaction-sensing-v13-safe-response-table-v1",
        "truth_metadata_present": False,
        "pixel_receipt_sha256": pixel_receipt_sha,
        "pollipi_trace_sha256": sha256_file(pollipi_trace),
        "insepi_trace_sha256": sha256_file(insepi_trace),
        "phase_summaries_sha256": sha256_file(phase_path),
        "safe_block_responses_sha256": sha256_file(response_path),
        "block_count": 180,
        "phase_count": 720,
        "sample_result_count_per_observer": 5760,
    }
    receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--pollipi-trace", type=Path, required=True)
    parser.add_argument("--insepi-trace", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    receipt = summarize(args.artifact_dir, args.pollipi_trace, args.insepi_trace, args.output_dir)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
