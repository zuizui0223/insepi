from pathlib import Path


def test_only_normal_ci_and_manual_v13_preflight_are_active() -> None:
    root = Path(__file__).resolve().parents[1]
    active = {p.name for p in (root / ".github" / "workflows").glob("*.yml")}
    assert active == {"test.yml", "v13-manual-preflight.yml"}


def test_v13_generation_workflow_is_manual_only() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / ".github" / "workflows" / "v13-manual-preflight.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "push:" not in text


def test_archived_workflow_provenance_is_retained() -> None:
    root = Path(__file__).resolve().parents[1]
    archive = root / "provenance" / "frozen_github_workflows"
    archived = {p.name for p in archive.glob("*.yml")}
    assert "v7-one-shot.yml" in archived
    assert "v10-one-shot.yml" in archived
    assert "v13-pre-field.yml" in archived
    assert "v14-dimensionless-phase.yml" in archived
    assert "v14b-frozen-ternary-phase-surface-fast.yml" in archived
    assert len(archived) == 36
