from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = (".py", ".md", ".toml", ".json", ".jsonl", ".bib", ".txt", ".yml", ".yaml", ".svg", ".csv", ".tsv")


def test_mee_manuscript_has_current_four_part_abstract_and_required_statements(tmp_path: Path) -> None:
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
    assert "[[V7_LOCKED_RESULT" not in text
    assert "## Data/Code for peer review" in text
    assert "### 2.15. AI-assisted software and manuscript development" in text
    assert "GPT-5.6 Sol" in text
    assert "**Target journal:**" not in text
    assert "**Status:**" not in text
    assert "PolliPi" not in text
    assert "InsePi" not in text
    assert "Observer-E" in text
    assert "Observer-O" in text
    assert "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9" not in text
    assert "980813bab996909020140fad5bd83b055eb3db9c" not in text

    # Current locked-result boundaries must survive the presentation transform.
    assert "0.9247839629" in text  # V7 locked failure
    assert "794/864" in text  # V8 generality map
    assert "97.75%" in text  # V9 design-based coverage
    assert "partial_or_family_specific_transfer" in text  # V10 claim C
    assert "0.3469" in text  # V11 locked failure
    assert "0.9608" in text and "0.7367" in text  # V12 first-intervention contrast
    assert "V13 physical validation is frozen but not yet claim-bearing" in text

    # Submission references must be the audited set, not the working list.
    assert "## References\n" in text
    assert "References (working citations)" not in text
    assert "10.1109/TSE.1985.231893" in text
    assert "On the impact of preferential sampling on ecological status and trend assessment" in text
    assert "MacKenzie et al., 2002" in text
    assert "Morris, White & Crowther, 2019" in text
    assert "Dwork et al., 2015" in text
    assert "Bothmann et al., 2023" in text
    assert "Reference metadata remains a working list" not in text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_verified_bibliography_has_unique_core_dois() -> None:
    bib = (ROOT / "manuscript" / "REFERENCES_VERIFIED.bib").read_text(encoding="utf-8")
    dois = [
        "10.1145/130385.130417",
        "10.1109/TSE.1985.231893",
        "10.1111/j.1467-9876.2009.00701.x",
        "10.1111/2041-210X.12803",
        "10.1111/2041-210X.14393",
        "10.1016/j.ecolmodel.2024.110707",
        "10.1016/j.ecoinf.2023.102231",
        "10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2",
        "10.1126/science.aaa9375",
        "10.1002/sim.8086",
    ]
    for doi in dois:
        assert bib.count(doi) == 1
    assert bib.count("@") == 11  # McKeeman (1998) has no DOI in the verified list.


def test_current_supplement_preserves_locked_failures_and_v13_boundary() -> None:
    supplement = (ROOT / "manuscript" / "SUPPLEMENTARY_INFORMATION_CURRENT.md").read_text(encoding="utf-8")
    for heading in (
        "## Appendix S4. V5 locked scalar-allocation falsification",
        "## Appendix S5. V6 development architecture and V7 locked challenge",
        "## Appendix S6. V8 abstract generality benchmark",
        "## Appendix S7. V9 finite-population inference",
        "## Appendix S8. V10 locked real-pixel perturbation transfer",
        "## Appendix S9. V11 locked static contradiction-state localisation",
        "## Appendix S10. V12 controlled causal-intervention diagnosis",
        "## Appendix S12. V13 blinded physical same-stream protocol",
    ):
        assert heading in supplement
    assert "[[V7_LOCKED_RESULT" not in supplement
    assert "gate: **FAIL**" in supplement
    assert "claim level: **D**" in supplement
    assert "Claim level: **B**" in supplement
    assert "V13 contains no scientific result" in supplement
    assert "96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d" in supplement


def test_anonymous_bundle_is_deterministic_and_identity_scrubbed(tmp_path: Path) -> None:
    generated = ROOT / "manuscript" / "generated" / "MEE_CURRENT_SUBMISSION.md"
    generated.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "scripts/build_mee_submission_manuscript.py", "--output", str(generated)],
        cwd=ROOT,
        check=True,
    )

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
        assert "manuscript/generated/MEE_CURRENT_SUBMISSION.md" in names
        assert "manuscript/REFERENCES_VERIFIED.bib" in names
        assert "manuscript/SUPPLEMENTARY_INFORMATION_CURRENT.md" in names
        assert "ANONYMOUS_BUNDLE_MANIFEST.json" in names
        assert "manuscript/TITLE_PAGE_TEMPLATE.md" not in names
        assert "manuscript/SUPPLEMENTARY_INFORMATION_PRE_V7.md" not in names
        assert "manuscript/V7_FINALIZATION_CONTRACT.md" not in names
        assert all("pollipi" not in name.lower() for name in names)
        assert all("insepi" not in name.lower() for name in names)
        combined = "\n".join(
            archive.read(name).decode("utf-8")
            for name in sorted(names)
            if name.endswith(TEXT_SUFFIXES)
        )
    lowered = combined.lower()
    assert "zuizui0223" not in lowered
    assert "github.com/zuizui0223" not in lowered
    assert "pollipi" not in lowered
    assert "insepi" not in lowered
    assert "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9" not in lowered
    assert "980813bab996909020140fad5bd83b055eb3db9c" not in lowered
    assert "[[v7_locked_result" not in lowered

    # Scientific 64-character fingerprints are intentionally retained.
    assert "20ff5eccd33d13f6115bde53e97ad80f16ccb2437870d3c1aeff3a6523089dae" in combined
    assert "f6af6292d7ce55bec6b3eefd0dd91b90e0a93de30d68e9fd22b3edf2bf41fd9b" in combined
    assert "7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222" in combined
    assert "96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d" in combined
