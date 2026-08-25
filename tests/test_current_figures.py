from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript" / "figures" / "current"


def _hashes() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(OUT.glob("fig*.*"))
        if path.suffix in {".svg", ".csv"}
    }


def test_current_figures_are_deterministic_and_preserve_claim_boundaries() -> None:
    subprocess.run([sys.executable, "scripts/build_current_figures.py"], cwd=ROOT, check=True)
    first = _hashes()
    subprocess.run([sys.executable, "scripts/build_current_figures.py"], cwd=ROOT, check=True)
    second = _hashes()
    assert first == second

    expected_svg = {
        "fig1_architecture.svg",
        "fig2_generation_ledger.svg",
        "fig3_allocation_evidence.svg",
        "fig4_protected_random_audit.svg",
        "fig5_causal_diagnosis.svg",
        "fig6_transfer_boundary.svg",
    }
    assert expected_svg <= set(first)

    all_svg = "\n".join((OUT / name).read_text(encoding="utf-8") for name in sorted(expected_svg))
    lowered = all_svg.lower()
    assert "optimal allocation" not in lowered
    assert "universal winner" in lowered
    assert "fail/c" in lowered
    assert "fail/d" in lowered
    assert "claim b" in lowered

    fig3 = (OUT / "fig3_allocation_evidence.svg").read_text(encoding="utf-8")
    assert "0.925" in fig3
    assert "91.9%" in fig3
    assert "21.4%" in fig3

    fig4 = (OUT / "fig4_protected_random_audit.svg").read_text(encoding="utf-8")
    assert "97.75%" in fig4
    assert "52.4%" in fig4

    fig5 = (OUT / "fig5_causal_diagnosis.svg").read_text(encoding="utf-8")
    assert "0.961" in fig5
    assert "0.737" in fig5

    fig6 = (OUT / "fig6_transfer_boundary.svg").read_text(encoding="utf-8")
    assert "RESULT PENDING" in fig6
    assert "4 / 6" in fig6
    assert "5 / 6" in fig6
    assert "natural pollinator-detection accuracy" in fig6


def test_current_figure_csvs_encode_locked_headline_values() -> None:
    subprocess.run([sys.executable, "scripts/build_current_figures.py"], cwd=ROOT, check=True)
    allocation = (OUT / "fig3_allocation_evidence.csv").read_text(encoding="utf-8")
    assert "0.9247839629" in allocation
    assert "0.202475" in allocation
    assert "91.9" in allocation
    diagnosis = (OUT / "fig5_diagnostic_results.csv").read_text(encoding="utf-8")
    assert "0.9608" in diagnosis
    assert "0.7367" in diagnosis
    transfer = (OUT / "fig6_transfer_boundary.csv").read_text(encoding="utf-8")
    assert "0.62718017578125" in transfer
    assert "PENDING" in transfer
