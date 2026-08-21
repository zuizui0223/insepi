from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def test_polish_wraps_fig2_and_moves_fig4_legend_without_touching_v7(tmp_path: Path) -> None:
    output = tmp_path / "figures"
    subprocess.run(
        [
            sys.executable,
            "scripts/build_pre_v7_figures.py",
            "--evidence",
            "manuscript/figures/pre_v7_evidence.json",
            "--output-dir",
            str(output),
        ],
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/polish_pre_v7_figures.py", "--output-dir", str(output)],
        check=True,
    )

    fig2_path = output / "fig2_v3_equal_budget.svg"
    fig4_path = output / "fig4_v6_architecture.svg"
    fig2 = fig2_path.read_text(encoding="utf-8")
    assert "targeted policies trade event recovery against hidden-error recovery and sampling distortion;</text>" in fig2
    assert "fixed disagreement is not a free improvement.</text>" in fig2
    assert 'x="200.0" y="718.0"' in fig2
    assert "candidate OR risky</text>" in fig2
    assert "candidate AND risky</text>" in fig2

    fig4 = fig4_path.read_text(encoding="utf-8")
    assert 'x="805.0" y="535.0"' in fig4
    assert 'x="832.0" y="550.0"' in fig4
    assert "observability risk</text>" in fig4

    combined = fig2 + fig4
    assert "[[V7_LOCKED_RESULT]]" not in combined
    assert "master_seed_hex" not in combined

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["presentation_polished"] is True
    by_name = manifest["outputs"]
    assert by_name["fig2_v3_equal_budget"]["sha256"] == _sha256(fig2_path)
    assert by_name["fig4_v6_architecture"]["sha256"] == _sha256(fig4_path)
