#!/usr/bin/env python3
"""Build a V14a2 prefreeze receipt after dedicated pre-sweep tests pass."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "protocol": ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json",
    "generator": ROOT / "src/interaction_sensing/simulation/dimensionless_observability_v14a2.py",
    "sweep_helpers": ROOT / "src/interaction_sensing/simulation/v14a2_sweep.py",
    "runner": ROOT / "scripts/run_v14a2_spatiotemporal_sweep.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def build() -> dict[str, object]:
    return {
        "schema": "insepi-v14a2-spatiotemporal-prefreeze-receipt-v1",
        "status": "candidate-generated-after-prefreeze-tests",
        "design_commit": git_head(),
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
        },
        "scientific_file_sha256": {name: sha256(path) for name, path in FILES.items()},
        "unlocked_for_first_scientific_sweep": True,
        "claim_boundary": "receipt only; no scientific sweep or result generated",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".v14a2/prefreeze_receipt_candidate.json")
    args = parser.parse_args()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
