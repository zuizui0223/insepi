#!/usr/bin/env python3
"""Capture the exact V7 runtime before smoke tests, seed derivation, or pixels."""
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

SCHEMA = "pollipi-insepi-v7-runtime-environment-v1"
EXPECTED_PYTHON = (3, 11, 16)
EXPECTED_NUMPY = "2.4.6"
FORBIDDEN_PRECAPTURE_PATHS = (
    ".v7/run/v7_pixels.npz",
    ".v7/run/v7_pixels_manifest.json",
    ".v7/run/v7_materialisation_receipt.json",
    ".v7/run/pollipi_v7_trace.jsonl",
    ".v7/run/insepi_v7_trace.jsonl",
    ".v7/run/v7_report.json",
    ".v7/run/v7_execution_ledger.json",
)


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
        default=Path(".v7/run/v7_runtime_environment.json"),
    )
    parser.add_argument(
        "--pip-freeze-output",
        type=Path,
        default=Path(".v7/run/v7_pip_freeze.txt"),
    )
    args = parser.parse_args()

    actual_python = sys.version_info[:3]
    if actual_python != EXPECTED_PYTHON:
        raise RuntimeError(
            f"V7 Python runtime mismatch: {actual_python} != {EXPECTED_PYTHON}"
        )
    if np.__version__ != EXPECTED_NUMPY:
        raise RuntimeError(
            f"V7 NumPy runtime mismatch: {np.__version__} != {EXPECTED_NUMPY}"
        )

    present = [path for path in FORBIDDEN_PRECAPTURE_PATHS if Path(path).exists()]
    if present:
        raise RuntimeError(
            "V7 runtime must be captured before materialisation/observer output; "
            f"already present: {present}"
        )

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
        "master_seed_derived": False,
        "v7_pixels_materialised": False,
        "observer_output_inspected": False,
    }
    args.output.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print("V7_RUNTIME_ENVIRONMENT PASS")
    print("V7_RUNTIME_PYTHON", payload["python_version"])
    print("V7_RUNTIME_NUMPY", payload["numpy_version"])
    print("V7_RUNTIME_PIP_FREEZE_SHA256", payload["pip_freeze_sha256"])
    print("V7_MASTER_SEED_DERIVED false")
    print("V7_PIXELS_MATERIALISED false")
    print("V7_OBSERVER_OUTPUT_INSPECTED false")


if __name__ == "__main__":
    main()
