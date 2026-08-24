#!/usr/bin/env python3
"""Validate a V13 physical field bundle without running either observer."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

EXPECTED_PRIVATE_COLUMNS = [
    "block_id", "split", "day_id", "scene_id", "treatment_class",
    "treatment_subtype", "replicate", "active_order", "protected_qc",
]
EXPECTED_PUBLIC_COLUMNS = ["opaque_block_id", "split", "phase_name", "phase_order", "clip_key"]
FORBIDDEN_PUBLIC_TOKENS = (
    "treatment_class", "treatment_subtype", "event_side", "nuisance_side",
    "shared_optical", "no_fault", "contrast_attenuation", "fan_driven",
    "occlusion", "glare", "diffusion",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return list(reader.fieldnames or []), rows


def validate(
    commitment_path: Path,
    private_truth_path: Path,
    observer_plan_path: Path,
    qc_plan_path: Path,
    *,
    clips_dir: Path | None = None,
    output_receipt: Path | None = None,
) -> dict[str, object]:
    commitment = json.loads(commitment_path.read_text(encoding="utf-8"))
    if commitment.get("schema") != "interaction-sensing-v13-randomisation-commitment-v1":
        raise RuntimeError("wrong V13 commitment schema")
    expected_hashes = {
        private_truth_path: commitment["private_truth_ledger_sha256"],
        observer_plan_path: commitment["observer_plan_sha256"],
        qc_plan_path: commitment["protected_qc_plan_sha256"],
    }
    for path, expected in expected_hashes.items():
        actual = _sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"V13 committed file hash mismatch: {path.name}: {actual} != {expected}")

    private_header, private_rows = _read_csv(private_truth_path)
    public_header, public_rows = _read_csv(observer_plan_path)
    qc_header, qc_rows = _read_csv(qc_plan_path)
    if private_header != EXPECTED_PRIVATE_COLUMNS:
        raise RuntimeError(f"private truth columns changed: {private_header}")
    if public_header != EXPECTED_PUBLIC_COLUMNS:
        raise RuntimeError(f"observer plan columns changed: {public_header}")
    if qc_header != ["block_id", "split", "protected_qc"]:
        raise RuntimeError(f"QC plan columns changed: {qc_header}")

    public_text = observer_plan_path.read_text(encoding="utf-8").lower()
    leaked = [token for token in FORBIDDEN_PUBLIC_TOKENS if token in public_text]
    if leaked:
        raise RuntimeError(f"truth leakage in observer plan: {leaked}")

    if len(private_rows) != 180 or len(public_rows) != 720 or len(qc_rows) != 180:
        raise RuntimeError("V13 cardinality mismatch")
    private_by_id = {row["block_id"]: row for row in private_rows}
    if len(private_by_id) != 180:
        raise RuntimeError("duplicate private block id")
    qc_by_id = {row["block_id"]: row for row in qc_rows}
    if set(qc_by_id) != set(private_by_id):
        raise RuntimeError("QC plan block ids differ from private truth ledger")

    public_by_id: dict[str, list[dict[str, str]]] = {}
    for row in public_rows:
        public_by_id.setdefault(row["opaque_block_id"], []).append(row)
    if set(public_by_id) != set(private_by_id):
        raise RuntimeError("public/private block id sets differ")

    for block_id, phases in public_by_id.items():
        phases = sorted(phases, key=lambda row: int(row["phase_order"]))
        if [int(row["phase_order"]) for row in phases] != [0, 1, 2, 3]:
            raise RuntimeError(f"phase order changed for {block_id}")
        if phases[0]["phase_name"] != "placebo":
            raise RuntimeError(f"placebo is not first for {block_id}")
        active = [row["phase_name"] for row in phases[1:]]
        expected_active = private_by_id[block_id]["active_order"].split(";")
        if active != expected_active:
            raise RuntimeError(f"active phase order differs from private ledger for {block_id}")
        if set(active) != {"event_restore", "observability_restore", "shared_restore"}:
            raise RuntimeError(f"active intervention set changed for {block_id}")
        if any(row["split"] != private_by_id[block_id]["split"] for row in phases):
            raise RuntimeError(f"split mismatch for {block_id}")
        if qc_by_id[block_id]["protected_qc"] != private_by_id[block_id]["protected_qc"]:
            raise RuntimeError(f"QC assignment mismatch for {block_id}")

    clip_hashes: dict[str, str] = {}
    if clips_dir is not None:
        for row in public_rows:
            path = clips_dir / row["clip_key"]
            if not path.is_file():
                raise FileNotFoundError(path)
            clip_hashes[row["clip_key"]] = _sha256_file(path)

    receipt = {
        "schema": "interaction-sensing-v13-field-bundle-validation-v1",
        "status": "validated-pre-observer-bundle" if clips_dir is not None else "validated-randomisation-plan",
        "commitment_sha256": _sha256_file(commitment_path),
        "private_truth_ledger_sha256": _sha256_file(private_truth_path),
        "observer_plan_sha256": _sha256_file(observer_plan_path),
        "protected_qc_plan_sha256": _sha256_file(qc_plan_path),
        "block_count": len(private_rows),
        "phase_row_count": len(public_rows),
        "development_block_count": sum(row["split"] == "development" for row in private_rows),
        "heldout_block_count": sum(row["split"] == "heldout" for row in private_rows),
        "protected_qc_block_count": sum(int(row["protected_qc"]) for row in private_rows),
        "clip_count": len(clip_hashes),
        "clip_sha256": clip_hashes,
        "truth_leakage_detected": False,
    }
    if output_receipt is not None:
        output_receipt.parent.mkdir(parents=True, exist_ok=True)
        output_receipt.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--private-truth", type=Path, required=True)
    parser.add_argument("--observer-plan", type=Path, required=True)
    parser.add_argument("--qc-plan", type=Path, required=True)
    parser.add_argument("--clips-dir", type=Path)
    parser.add_argument("--output-receipt", type=Path)
    args = parser.parse_args()
    receipt = validate(
        args.commitment,
        args.private_truth,
        args.observer_plan,
        args.qc_plan,
        clips_dir=args.clips_dir,
        output_receipt=args.output_receipt,
    )
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
