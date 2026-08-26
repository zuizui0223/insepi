#!/usr/bin/env python3
"""Validate or execute the prefrozen V15a cross-state expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from interaction_sensing.cross_state_observability_v15a import (
    build_v15a_cross_state_result,
    validate_v15a_protocol,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "benchmarks/v15a_cross_state_observability_protocol.json"
DEFAULT_LOCKED_SUMMARY = (
    ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_result.json"
)
DEFAULT_V15_CONTRACT = ROOT / "benchmarks/v15_observability_estimator_contract.json"
DEFAULT_V14B_CLOSEOUT = ROOT / "benchmarks/v14b_prefield_programming_closeout.json"


def _read_json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return document


def sources(
    *,
    protocol_path: Path,
    locked_summary_path: Path,
    v15_contract_path: Path,
    v14b_closeout_path: Path,
) -> dict[str, dict[str, object]]:
    return {
        "protocol": _read_json(protocol_path),
        "locked_summary": _read_json(locked_summary_path),
        "v15_observability_contract": _read_json(v15_contract_path),
        "v14b_closeout": _read_json(v14b_closeout_path),
    }


def run(
    *,
    protocol_path: Path,
    locked_summary_path: Path,
    v15_contract_path: Path,
    v14b_closeout_path: Path,
    prefreeze_commit: str,
    output_path: Path,
) -> dict[str, object]:
    if output_path.exists():
        raise FileExistsError(
            f"refusing to overwrite retained first result: {output_path}"
        )
    inputs = sources(
        protocol_path=protocol_path,
        locked_summary_path=locked_summary_path,
        v15_contract_path=v15_contract_path,
        v14b_closeout_path=v14b_closeout_path,
    )
    result = build_v15a_cross_state_result(
        **inputs,
        prefreeze_commit=prefreeze_commit,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--locked-summary", type=Path, default=DEFAULT_LOCKED_SUMMARY)
    parser.add_argument("--v15-contract", type=Path, default=DEFAULT_V15_CONTRACT)
    parser.add_argument("--v14b-closeout", type=Path, default=DEFAULT_V14B_CLOSEOUT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--prefreeze-commit")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    inputs = sources(
        protocol_path=args.protocol,
        locked_summary_path=args.locked_summary,
        v15_contract_path=args.v15_contract,
        v14b_closeout_path=args.v14b_closeout,
    )
    if args.validate_only:
        validate_v15a_protocol(**inputs)
        print("V15A_CROSS_STATE_PROTOCOL PASS")
        return
    if args.prefreeze_commit is None or args.output is None:
        parser.error("execution requires --prefreeze-commit and --output")
    result = run(
        protocol_path=args.protocol,
        locked_summary_path=args.locked_summary,
        v15_contract_path=args.v15_contract,
        v14b_closeout_path=args.v14b_closeout,
        prefreeze_commit=args.prefreeze_commit,
        output_path=args.output,
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "status": result["status"],
                "provenance": result["provenance"],
                "expanded_global": result["measurement"]["expanded_global"],
                "claim_ceiling": result["claim_ceiling"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
