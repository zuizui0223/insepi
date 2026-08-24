#!/usr/bin/env python3
"""Compute one deterministic digest over V13 scientific/execution-critical bytes.

The workflow and this helper are deliberately excluded from the digest so CI
or verification plumbing can be repaired without changing scientific semantics.
Any change to a listed path requires a new pre-field execution freeze/generation
once physical acquisition has started.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_PATHS = (
    "benchmarks/v13_observer_measurement_freeze.json",
    "benchmarks/v13_physical_intervention_protocol.json",
    "benchmarks/v13_physical_phase_contract.json",
    "scripts/v13_build_randomisation.py",
    "scripts/v13_commit_prediction.py",
    "scripts/v13_evaluate_locked.py",
    "scripts/v13_make_capture_templates.py",
    "scripts/v13_make_qc_template.py",
    "scripts/v13_materialize_pixels.py",
    "scripts/v13_predict_blinded.py",
    "scripts/v13_run_insepi_frozen.py",
    "scripts/v13_run_pollipi_frozen.py",
    "scripts/v13_split_private_truth.py",
    "scripts/v13_summarize_observer_traces.py",
    "scripts/v13_validate_capture_logs.py",
    "scripts/v13_validate_field_bundle.py",
    "src/interaction_sensing/causal_diagnostics.py",
    "src/interaction_sensing/physical_artifact_v13.py",
    "src/interaction_sensing/physical_evaluation_v13.py",
    "src/interaction_sensing/physical_measurement_v13.py",
    "src/interaction_sensing/simulation/real_video_v10.py"
)


def execution_digest(root: Path = ROOT) -> str:
    digest = hashlib.sha256()
    for relative in CRITICAL_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(path)
        payload = path.read_bytes()
        name = relative.encode("utf-8")
        digest.update(len(name).to_bytes(8, "big"))
        digest.update(name)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expect")
    args = parser.parse_args()
    actual = execution_digest(args.root)
    print("V13_EXECUTION_DIGEST_SHA256", actual)
    print("V13_EXECUTION_DIGEST_PATH_COUNT", len(CRITICAL_PATHS))
    if args.expect is not None and actual != args.expect:
        raise SystemExit(f"V13 execution digest mismatch: {actual} != {args.expect}")


if __name__ == "__main__":
    main()
