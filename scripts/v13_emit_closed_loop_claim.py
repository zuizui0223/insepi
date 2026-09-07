#!/usr/bin/env python3
"""Emit the predeclared cross-repository interpretation of a frozen V13 report.

This script does not evaluate V13 and does not inspect raw truth. It accepts only
the locked post-unseal V13 report and maps its A/B/C/D claim level to the wording
frozen in docs/V13_CLOSED_LOOP_INTERPRETATION_CONTRACT.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SCHEMA = "interaction-sensing-v13-physical-evaluation-v1"

MAPPING = {
    "A": {
        "label": "material_physical_distinct_channel_advantage",
        "umbrella_claim": (
            "In a blinded controlled physical observation system, retaining distinct "
            "observer channels and sequentially revealing predeclared diagnostic "
            "interventions produced materially finer held-out distinctions among physical "
            "failure classes across new days and scenes."
        ),
        "v3_physical_strict_refinement": True,
        "mrod_like_physical_prospective_refinement": True,
        "unified_physical_loop_closure": True,
        "boundary_exact_rank_reduction": False,
    },
    "B": {
        "label": "conditional_physical_causal_identification",
        "umbrella_claim": (
            "In a blinded controlled physical observation system, predeclared diagnostic "
            "interventions conditionally resolved physical failure classes across new days "
            "and scenes; a material advantage of the distinct-channel representation was "
            "not established."
        ),
        "v3_physical_strict_refinement": False,
        "mrod_like_physical_prospective_refinement": True,
        "unified_physical_loop_closure": True,
        "boundary_exact_rank_reduction": False,
    },
    "C": {
        "label": "mixed_physical_intervention_transfer",
        "umbrella_claim": (
            "Physical transfer of the synthetic diagnostic structure was mixed across the "
            "frozen V13 held-out design."
        ),
        "v3_physical_strict_refinement": False,
        "mrod_like_physical_prospective_refinement": False,
        "unified_physical_loop_closure": False,
        "boundary_exact_rank_reduction": False,
    },
    "D": {
        "label": "physical_intervention_identification_not_established",
        "umbrella_claim": (
            "The frozen V13 experiment did not establish physical intervention-based "
            "identification of the predeclared failure classes."
        ),
        "v3_physical_strict_refinement": False,
        "mrod_like_physical_prospective_refinement": False,
        "unified_physical_loop_closure": False,
        "boundary_exact_rank_reduction": False,
    },
}

FORBIDDEN_GENERALISATIONS = [
    "natural pollinator detection accuracy",
    "ecological prevalence or visit-rate validity",
    "universal V3 reference benefit",
    "universal MROD optimality",
    "exact Boundary rank reduction without a separately predeclared analysis",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def map_report(report: dict[str, object], report_sha256: str) -> dict[str, object]:
    if report.get("schema") != EXPECTED_SCHEMA:
        raise ValueError("wrong V13 physical evaluation schema")
    claim = report.get("claim")
    if not isinstance(claim, dict):
        raise ValueError("V13 report lacks claim object")
    level = claim.get("level")
    label = claim.get("label")
    if level not in MAPPING:
        raise ValueError(f"unknown V13 claim level: {level!r}")
    frozen = MAPPING[level]
    if label != frozen["label"]:
        raise ValueError(
            f"V13 claim label/level mismatch: {level!r} with {label!r}; "
            f"expected {frozen['label']!r}"
        )

    return {
        "schema": "interaction-sensing-v13-closed-loop-claim-v1",
        "source_v13_report_sha256": report_sha256,
        "source_v13_claim_level": level,
        "source_v13_claim_label": label,
        "umbrella_claim": frozen["umbrella_claim"],
        "cross_repository_updates": {
            "v3_physical_strict_refinement": frozen["v3_physical_strict_refinement"],
            "mrod_like_physical_prospective_refinement": frozen[
                "mrod_like_physical_prospective_refinement"
            ],
            "unified_physical_loop_closure": frozen["unified_physical_loop_closure"],
            "boundary_exact_rank_reduction": frozen["boundary_exact_rank_reduction"],
        },
        "forbidden_generalisations": FORBIDDEN_GENERALISATIONS,
        "interpretation_contract": "docs/V13_CLOSED_LOOP_INTERPRETATION_CONTRACT.md",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    output = map_report(report, sha256_file(args.report))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("V13_CLOSED_LOOP_CLAIM", output["source_v13_claim_level"])
    print("V13_CLOSED_LOOP_CLAIM_SHA256", sha256_file(args.output))


if __name__ == "__main__":
    main()
