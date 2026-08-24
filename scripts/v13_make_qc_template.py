#!/usr/bin/env python3
"""Generate a treatment-truth-free annotation sheet for protected V13 QC blocks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-plan", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    commitment = json.loads(args.commitment.read_text(encoding="utf-8"))
    if sha256_file(args.qc_plan) != commitment.get("protected_qc_plan_sha256"):
        raise SystemExit("V13 QC plan differs from pre-field commitment")
    with args.qc_plan.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    selected = [row for row in rows if row["protected_qc"] == "1"]
    fields = [
        "block_id", "split",
        "local_event_reference_present_as_planned",
        "nuisance_treatment_present_as_planned",
        "shared_optical_treatment_present_as_planned",
        "gross_protocol_violation",
        "annotator_code", "notes",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in sorted(selected, key=lambda value: value["block_id"]):
            writer.writerow({
                "block_id": row["block_id"],
                "split": row["split"],
                "local_event_reference_present_as_planned": "",
                "nuisance_treatment_present_as_planned": "",
                "shared_optical_treatment_present_as_planned": "",
                "gross_protocol_violation": "",
                "annotator_code": "",
                "notes": "",
            })
    print("V13_QC_TEMPLATE PASS", len(selected), sha256_file(args.output))


if __name__ == "__main__":
    main()
