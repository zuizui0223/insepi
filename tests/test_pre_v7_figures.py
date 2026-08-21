from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_pre_v7_figure_builder_is_deterministic_and_v7_safe(tmp_path: Path) -> None:
    output = tmp_path / "figures"
    command = [
        sys.executable,
        "scripts/build_pre_v7_figures.py",
        "--evidence",
        "manuscript/figures/pre_v7_evidence.json",
        "--output-dir",
        str(output),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    first = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    subprocess.run(command, check=True, capture_output=True, text=True)
    second = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    assert first == second
    assert first["schema"] == "insepi-method-paper-pre-v7-figure-manifest-v1"
    assert first["v7_materialised"] is False
    assert len(first["outputs"]) == 8

    for record in first["outputs"].values():
        path = Path(record["path"])
        assert path.exists()
        assert len(record["sha256"]) == 64
        if path.suffix == ".svg":
            content = path.read_text(encoding="utf-8")
            assert content.startswith("<svg")
            assert "[[V7_LOCKED_RESULT]]" not in content


def test_pre_v7_evidence_keeps_v7_unexecuted_and_v5_falsification_visible() -> None:
    evidence = json.loads(Path("manuscript/figures/pre_v7_evidence.json").read_text(encoding="utf-8"))
    ledger = {row["generation"]: row for row in evidence["generation_ledger"]}
    assert ledger["V5"]["status"] == "locked fail"
    assert ledger["V7"]["status"] == "unexecuted"

    surface = evidence["v5_locked_surface"]["full_gate_pass"]
    assert sum(int(value) for row in surface for value in row) == 1
    assert surface[1][1] is True


def test_frozen_v6_candidate_is_the_e50_portfolio() -> None:
    evidence = json.loads(Path("manuscript/figures/pre_v7_evidence.json").read_text(encoding="utf-8"))
    candidates = {row["name"]: row for row in evidence["v6_focused_candidates"]}
    frozen = candidates["E50_P10_I40"]
    assert frozen["passed"] is True
    assert frozen["exploration"] == 0.50
    assert frozen["pollipi"] == 0.10
    assert frozen["insepi"] == 0.40
    assert frozen["disagreement"] == 0.0
    assert frozen["worst_joint_ratio"] == 1.00846
    assert frozen["max_tv"] == 0.21919
