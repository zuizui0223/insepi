from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def test_mee_manuscript_has_four_part_abstract_and_required_statements(tmp_path: Path) -> None:
    output = tmp_path / "submission.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/build_mee_submission_manuscript.py",
            "--source",
            "manuscript/METHODS_PAPER_DRAFT.md",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
    )
    text = output.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("## Data/Code for peer review", 1)[0]
    assert abstract.count("\n1. ") == 1
    assert abstract.count("\n2. ") == 1
    assert abstract.count("\n3. ") == 1
    assert abstract.count("\n4. ") == 1
    assert "\n5. " not in abstract
    assert "[[V7_LOCKED_RESULT]]" in abstract
    assert "## Data/Code for peer review" in text
    assert "### 2.13. AI-assisted software and manuscript development" in text
    assert "GPT-5.6 Sol" in text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_anonymous_bundle_is_deterministic_and_identity_scrubbed(tmp_path: Path) -> None:
    generated = ROOT / "manuscript" / "generated" / "MEE_PRE_V7_SUBMISSION.md"
    generated.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "scripts/build_mee_submission_manuscript.py", "--output", str(generated)],
        cwd=ROOT,
        check=True,
    )

    # Generate figures so the anonymous bundle contains the actual pre-V7 review visuals.
    subprocess.run([sys.executable, "scripts/build_pre_v7_figures.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/polish_pre_v7_figures.py"], cwd=ROOT, check=True)

    zip_a = tmp_path / "a.zip"
    zip_b = tmp_path / "b.zip"
    for label, zip_path in (("a", zip_a), ("b", zip_b)):
        subprocess.run(
            [
                sys.executable,
                "scripts/build_anonymous_peer_review_bundle.py",
                "--root",
                ".",
                "--staging",
                str(tmp_path / f"stage-{label}"),
                "--zip",
                str(zip_path),
            ],
            cwd=ROOT,
            check=True,
        )
    assert _sha256(zip_a) == _sha256(zip_b)

    with zipfile.ZipFile(zip_a) as archive:
        names = set(archive.namelist())
        assert "manuscript/generated/MEE_PRE_V7_SUBMISSION.md" in names
        assert "manuscript/figures/generated/fig1_generation_timeline.svg" in names
        assert "ANONYMOUS_BUNDLE_MANIFEST.json" in names
        combined = "\n".join(
            archive.read(name).decode("utf-8")
            for name in sorted(names)
            if name.endswith((".py", ".md", ".toml", ".json", ".txt", ".yml", ".yaml", ".svg"))
        )
    assert "zuizui0223" not in combined
    assert "github.com/zuizui0223" not in combined
    assert "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9" not in combined
    assert "980813bab996909020140fad5bd83b055eb3db9c" not in combined
    # 64-character scientific fingerprints are intentionally not scrubbed.
    assert "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3" in combined
