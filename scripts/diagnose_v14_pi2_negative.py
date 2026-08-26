#!/usr/bin/env python3
"""Diagnose the negative registered V14a Pi2 prediction from frozen outputs."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from interaction_sensing.development.pi2_negative_diagnosis import diagnose_pi2_negative


def run(surface_path: Path, protocol_path: Path, output_path: Path) -> dict[str, object]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    with surface_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    diagnosis = diagnose_pi2_negative(rows, protocol).to_dict()
    payload: dict[str, object] = {
        "schema": "insepi-v14a-p3-negative-diagnosis-v1",
        "status": "post-result-diagnostic-does-not-alter-v14a",
        "source_surface": str(surface_path),
        "source_protocol": str(protocol_path),
        "diagnosis": diagnosis,
        "claim_boundary": (
            "negative-result diagnosis only; no threshold tuning, no relabelling of V14a, "
            "no field transition claim"
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--surface", required=True)
    parser.add_argument(
        "--protocol",
        default="benchmarks/v14_dimensionless_world_protocol.json",
    )
    parser.add_argument(
        "--output",
        default=".v14/pi2_negative_diagnosis.json",
    )
    args = parser.parse_args()
    payload = run(Path(args.surface), Path(args.protocol), Path(args.output))
    diagnosis = payload["diagnosis"]
    print("P3_REGISTERED_SUPPORTED", str(diagnosis["registered_prediction_supported"]).lower())
    print("P3_DIAGNOSIS", diagnosis["diagnosis"])
    print("P3_NEXT_GENERATION_REQUIRED", str(diagnosis["next_generation_required"]).lower())


if __name__ == "__main__":
    main()
