#!/usr/bin/env python3
"""Build the V14b pre-field programming closeout from locked JSON evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from interaction_sensing.prefield_programming_closeout import (
    build_v14b_prefield_programming_closeout,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORLD_PROTOCOL = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"
DEFAULT_TERNARY_PROTOCOL = (
    ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_protocol.json"
)
DEFAULT_LOCKED_SUMMARY = (
    ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_result.json"
)
DEFAULT_FIGURE_DATA = ROOT / "benchmarks/v14b_frozen_ternary_phase_figure_data.json"


def _read_json(path: Path) -> dict[str, object]:
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TypeError(f"JSON root must be an object: {path}")
    return document


def run(
    *,
    world_protocol_path: Path,
    ternary_protocol_path: Path,
    locked_summary_path: Path,
    figure_data_path: Path,
    output_path: Path,
) -> dict[str, object]:
    result = build_v14b_prefield_programming_closeout(
        world_protocol=_read_json(world_protocol_path),
        ternary_protocol=_read_json(ternary_protocol_path),
        locked_summary=_read_json(locked_summary_path),
        figure_data=_read_json(figure_data_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--world-protocol", type=Path, default=DEFAULT_WORLD_PROTOCOL)
    parser.add_argument(
        "--ternary-protocol",
        type=Path,
        default=DEFAULT_TERNARY_PROTOCOL,
    )
    parser.add_argument("--locked-summary", type=Path, default=DEFAULT_LOCKED_SUMMARY)
    parser.add_argument("--figure-data", type=Path, default=DEFAULT_FIGURE_DATA)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(
        world_protocol_path=args.world_protocol,
        ternary_protocol_path=args.ternary_protocol,
        locked_summary_path=args.locked_summary,
        figure_data_path=args.figure_data,
        output_path=args.output,
    )
    print(
        json.dumps(
            {
                "schema": result["schema"],
                "status": result["status"],
                "source_identity": result["source_identity"],
                "claim_ceiling": result["claim_ceiling"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
