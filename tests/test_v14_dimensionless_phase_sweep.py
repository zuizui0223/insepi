from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "v14_dimensionless_phase_surface.csv",
    "v14_dimensionless_phase_summary.json",
    "v14_dimensionless_phase_receipt.json",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(script: str, out: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            script,
            "--output-dir",
            str(out),
            "--limit-coordinates",
            "2",
            "--replicates",
            "2",
        ],
        cwd=ROOT,
        check=True,
    )


def test_v14_small_phase_rehearsal_is_deterministic(tmp_path: Path) -> None:
    outputs = []
    for label in ("a", "b"):
        out = tmp_path / label
        _run("scripts/run_v14_dimensionless_phase_sweep.py", out)
        outputs.append(out)

    for name in FILES:
        assert _sha(outputs[0] / name) == _sha(outputs[1] / name)

    summary = json.loads((outputs[0] / "v14_dimensionless_phase_summary.json").read_text())
    assert summary["canonical"] is False
    assert summary["coordinate_count"] == 2
    assert summary["regime_count"] == 5
    assert summary["replicates_per_coordinate_regime"] == 2
    assert summary["world_count"] == 20
    assert summary["surface_row_count"] == 10
    assert set(summary["prediction_checks_descriptive_not_gates"]) == {
        "P1_short_window_more_information_absence",
        "P2_low_pi3_weaker_direct_route",
        "P3_pi2_near_one_more_ambiguity_when_other_separation_weak",
        "P4_high_pi4_more_indirect_rescue_at_low_pi3",
    }


def test_cached_wrapper_is_scientifically_byte_identical(tmp_path: Path) -> None:
    uncached = tmp_path / "uncached"
    cached = tmp_path / "cached"
    _run("scripts/run_v14_dimensionless_phase_sweep.py", uncached)
    _run("scripts/run_v14_dimensionless_phase_sweep_cached.py", cached)
    for name in FILES:
        assert _sha(uncached / name) == _sha(cached / name)


def test_protocol_predictions_are_descriptive_not_ci_gates() -> None:
    script = (ROOT / "scripts/run_v14_dimensionless_phase_sweep.py").read_text()
    assert "prediction_checks_descriptive_not_gates" in script
    assert "raise" not in script.split("prediction_checks_descriptive_not_gates", 1)[1].split("def main", 1)[0]
