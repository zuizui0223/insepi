#!/usr/bin/env python3
"""Capture the pinned V10 observer runtime before canonical pixels are read.

The same pre-pixel step also verifies that the supplied prerequisite evidence is
the complete frozen V7 generation. V7 PASS and FAIL are both accepted; a wrong
or incomplete V7 generation blocks V10 before canonical V10 pixels are read.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys

import numpy as np

from v10_verify_v7_prerequisite import verify as verify_v7_prerequisite

SCHEMA = "interaction-sensing-v10-runtime-environment-v1"
EXPECTED_PYTHON = (3, 11, 16)
EXPECTED_NUMPY = "2.4.6"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".v10/runtime/runtime_environment.json"),
    )
    parser.add_argument(
        "--pip-freeze-output",
        type=Path,
        default=Path(".v10/runtime/pip_freeze.txt"),
    )
    parser.add_argument(
        "--v7-prereq-root",
        type=Path,
        default=Path(".v10/v7-prereq"),
    )
    args = parser.parse_args()

    actual_python = sys.version_info[:3]
    if actual_python != EXPECTED_PYTHON:
        raise RuntimeError(
            f"V10 Python runtime mismatch: {actual_python} != {EXPECTED_PYTHON}"
        )
    if np.__version__ != EXPECTED_NUMPY:
        raise RuntimeError(
            f"V10 NumPy runtime mismatch: {np.__version__} != {EXPECTED_NUMPY}"
        )

    # This occurs after the prior V7 artifact is downloaded but before observer
    # smoke and before the canonical V10 pixel artifact is downloaded.
    v7_verified = verify_v7_prerequisite(args.v7_prereq_root)

    completed = subprocess.run(
        [sys.executable, "-m", "pip", "freeze", "--all"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())
    freeze_bytes = ("\n".join(lines) + "\n").encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.pip_freeze_output.parent.mkdir(parents=True, exist_ok=True)
    args.pip_freeze_output.write_bytes(freeze_bytes)

    payload = {
        "schema": SCHEMA,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": str(Path(sys.executable).resolve()),
        "numpy_version": np.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "system": platform.system(),
        "release": platform.release(),
        "interaction_sensing_distribution_version": _distribution_version("interaction-sensing"),
        "pollipi_analysis_distribution_version": _distribution_version("pollipi-analysis"),
        "pip_version": _distribution_version("pip"),
        "setuptools_version": _distribution_version("setuptools"),
        "pip_freeze_sha256": _sha256(freeze_bytes),
        "pip_freeze_line_count": len(lines),
        "v7_prerequisite_verified": True,
        "v7_prerequisite_ledger_sha256": str(v7_verified["ledger_sha256"]),
        "v7_prerequisite_claim_level": str(v7_verified["claim_level"]),
        "v7_prerequisite_gate_passed": bool(v7_verified["gate_passed"]),
        "v7_prerequisite_world_fingerprint": str(v7_verified["world_fingerprint"]),
        "v7_prerequisite_pixel_artifact_sha256": str(v7_verified["pixel_artifact_sha256"]),
        "observer_output_inspected": False,
        "canonical_v10_pixels_read": False,
    }
    args.output.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print("V10_RUNTIME_ENVIRONMENT PASS")
    print("V10_RUNTIME_PYTHON", payload["python_version"])
    print("V10_RUNTIME_NUMPY", payload["numpy_version"])
    print("V10_RUNTIME_PIP_FREEZE_SHA256", payload["pip_freeze_sha256"])
    print("V10_V7_PREREQUISITE_VERIFIED true")
    print("V10_V7_PREREQUISITE_LEDGER_SHA256", payload["v7_prerequisite_ledger_sha256"])
    print("V10_RUNTIME_CANONICAL_PIXELS_READ false")


if __name__ == "__main__":
    main()
