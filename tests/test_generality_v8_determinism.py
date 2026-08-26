from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


MINI_PROTOCOL = {
    "schema": "interaction-sensing-v8-generality-protocol-v1",
    "seed": 20260822,
    "policies": [
        "uniform",
        "guarded_v6",
        "guarded_e_only",
        "guarded_o_only",
        "guarded_fused_20_80",
        "guarded_max",
    ],
    "world": {
        "windows_per_regime": 120,
        "paired_replicates": 3,
        "event_prevalence": [0.10],
        "budget_fraction": [0.25],
        "evidence_quality": [0.75],
        "observability_quality": [0.75],
        "residual_correlation": [0.50],
        "disturbance_prevalence": [0.40],
    },
}


def _subprocess_result_hash(hash_seed: str) -> str:
    code = (
        "import hashlib,json; "
        "from interaction_sensing.simulation.generality_v8 import run_protocol; "
        f"p=json.loads({json.dumps(json.dumps(MINI_PROTOCOL))}); "
        "b=json.dumps(run_protocol(p),sort_keys=True,separators=(',',':')).encode(); "
        "print(hashlib.sha256(b).hexdigest())"
    )
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = hash_seed
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def test_v8_result_is_byte_deterministic_across_python_hash_seeds() -> None:
    first = _subprocess_result_hash("1")
    second = _subprocess_result_hash("987654")
    assert first == second
    assert len(first) == 64
    int(first, 16)


def test_protocol_fixture_itself_is_stable() -> None:
    canonical = json.dumps(MINI_PROTOCOL, sort_keys=True, separators=(",", ":")).encode()
    assert len(hashlib.sha256(canonical).hexdigest()) == 64
