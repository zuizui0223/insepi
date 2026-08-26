#!/usr/bin/env python3
"""Generate a blinded V13 physical-block plan from a private 64-hex salt.

The salt and private truth ledger are field-operator material and must not be
placed in the observer environment.  The public observer plan contains opaque
block IDs, phase identities and deterministic clip keys, but no latent treatment
class or subtype.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "benchmarks" / "v13_physical_intervention_protocol.json"
DOMAIN = "interaction-sensing-v13-private-block-id-v1"
ACTIVE = ("event_restore", "observability_restore", "shared_restore")


def _require_salt(value: str) -> str:
    salt = value.strip().lower()
    if len(salt) != 64 or any(c not in "0123456789abcdef" for c in salt):
        raise ValueError("--salt must be exactly 64 hexadecimal characters")
    return salt


def _hash_text(*parts: object) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build(salt: str, output_dir: Path) -> dict[str, object]:
    salt = _require_salt(salt)
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    treatments = protocol["latent_physical_treatment_classes"]
    order_domain = protocol["randomisation"]["seed_domain"]
    qc_domain = protocol["physical_qc"]["assignment_domain"]

    private_rows: list[dict[str, object]] = []
    public_rows: list[dict[str, object]] = []
    qc_rows: list[dict[str, object]] = []

    split_specs = (
        ("development", 3, 3),
        ("heldout", 2, 3),
    )
    for split, day_count, scene_count in split_specs:
        for day in range(1, day_count + 1):
            day_id = f"{split[:3]}_day_{day:02d}"
            for scene in range(1, scene_count + 1):
                scene_id = f"{split[:3]}_scene_{scene:02d}"
                for treatment_class in sorted(treatments):
                    subtype_key = "development_subtype" if split == "development" else "heldout_subtype"
                    subtype = str(treatments[treatment_class][subtype_key])
                    for replicate in range(1, 4):
                        full_digest = _hash_text(
                            DOMAIN,
                            salt,
                            split,
                            day_id,
                            scene_id,
                            treatment_class,
                            replicate,
                        )
                        block_id = f"b{full_digest[:20]}"
                        ranked = sorted(
                            ACTIVE,
                            key=lambda name: _hash_text(order_domain, salt, block_id, name),
                        )
                        qc_selected = int(_hash_text(qc_domain, salt, block_id)[:2], 16) < 64
                        private_rows.append({
                            "block_id": block_id,
                            "split": split,
                            "day_id": day_id,
                            "scene_id": scene_id,
                            "treatment_class": treatment_class,
                            "treatment_subtype": subtype,
                            "replicate": replicate,
                            "active_order": ";".join(ranked),
                            "protected_qc": int(qc_selected),
                        })
                        qc_rows.append({
                            "block_id": block_id,
                            "split": split,
                            "protected_qc": int(qc_selected),
                        })
                        phases = ("placebo", *ranked)
                        for phase_order, phase_name in enumerate(phases):
                            public_rows.append({
                                "opaque_block_id": block_id,
                                "split": split,
                                "phase_name": phase_name,
                                "phase_order": phase_order,
                                "clip_key": f"{block_id}__p{phase_order}_{phase_name}.mp4",
                            })

    output_dir.mkdir(parents=True, exist_ok=True)
    private_path = output_dir / "v13_private_truth_ledger.csv"
    public_path = output_dir / "v13_observer_plan.csv"
    qc_path = output_dir / "v13_protected_qc_plan.csv"
    _write_csv(
        private_path,
        ["block_id", "split", "day_id", "scene_id", "treatment_class", "treatment_subtype", "replicate", "active_order", "protected_qc"],
        private_rows,
    )
    _write_csv(
        public_path,
        ["opaque_block_id", "split", "phase_name", "phase_order", "clip_key"],
        public_rows,
    )
    _write_csv(qc_path, ["block_id", "split", "protected_qc"], qc_rows)

    counts = {
        "private_blocks": len(private_rows),
        "observer_phase_rows": len(public_rows),
        "development_blocks": sum(row["split"] == "development" for row in private_rows),
        "heldout_blocks": sum(row["split"] == "heldout" for row in private_rows),
        "protected_qc_blocks": sum(int(row["protected_qc"]) for row in private_rows),
    }
    if counts["private_blocks"] != 180 or counts["development_blocks"] != 108 or counts["heldout_blocks"] != 72:
        raise AssertionError(counts)
    if counts["observer_phase_rows"] != 720:
        raise AssertionError(counts)

    commitment = {
        "schema": "interaction-sensing-v13-randomisation-commitment-v1",
        "status": "pre-field-plan-not-data",
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "private_truth_ledger_sha256": _sha256_file(private_path),
        "observer_plan_sha256": _sha256_file(public_path),
        "protected_qc_plan_sha256": _sha256_file(qc_path),
        "counts": counts,
        "private_material_warning": "Do not expose the salt or v13_private_truth_ledger.csv to observer execution or heldout diagnosis before predictions are frozen.",
    }
    commitment_path = output_dir / "v13_randomisation_commitment.json"
    commitment_path.write_text(json.dumps(commitment, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return commitment


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--salt", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    commitment = build(args.salt, args.output_dir)
    print(json.dumps(commitment, sort_keys=True))


if __name__ == "__main__":
    main()
