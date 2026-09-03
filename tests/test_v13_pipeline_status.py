from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def _load_status_module():
    name = "v13_pipeline_status_test"
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts/v13_pipeline_status.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _touch(root: Path, relative: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def _complete_stage(root: Path, stage) -> None:
    for relative in stage.required_paths:
        _touch(root, relative)


def test_v13_empty_workspace_starts_at_private_randomisation(tmp_path: Path) -> None:
    module = _load_status_module()
    status = module.inspect_workspace(tmp_path)
    assert status["valid"] is True
    assert status["clip_count"] == 0
    assert status["next_stage"] == "stage_1_private_randomisation"
    assert "randomisation" in status["next_action"].lower()


def test_v13_plan_and_templates_advance_to_physical_acquisition(tmp_path: Path) -> None:
    module = _load_status_module()
    _complete_stage(tmp_path, module.STAGES[0])
    _complete_stage(tmp_path, module.STAGES[1])
    status = module.inspect_workspace(tmp_path)
    assert status["valid"] is True
    assert status["next_stage"] == "stage_3_physical_acquisition"
    assert "720" in status["next_action"]


def test_v13_partial_artifact_set_is_fail_closed(tmp_path: Path) -> None:
    module = _load_status_module()
    _touch(tmp_path, module.STAGES[0].required_paths[0])
    status = module.inspect_workspace(tmp_path)
    assert status["valid"] is False
    assert any("partial artifact set" in item for item in status["violations"])


def test_v13_downstream_trace_before_capture_is_blocked(tmp_path: Path) -> None:
    module = _load_status_module()
    _complete_stage(tmp_path, module.STAGES[5])
    status = module.inspect_workspace(tmp_path)
    assert status["valid"] is False
    assert any("do not skip the frozen execution order" in item for item in status["violations"])


def test_v13_complete_artifact_skeleton_reports_complete(tmp_path: Path) -> None:
    module = _load_status_module()
    for stage in module.STAGES:
        _complete_stage(tmp_path, stage)
    clips = tmp_path / "V13_CLIPS"
    clips.mkdir()
    for index in range(module.EXPECTED_CLIP_COUNT):
        (clips / f"clip_{index:03d}.mp4").write_bytes(b"")
    status = module.inspect_workspace(tmp_path)
    assert status["valid"] is True
    assert status["acquisition_complete"] is True
    assert status["next_stage"] == "complete"


def test_v13_status_cli_exits_nonzero_when_order_is_violated(tmp_path: Path) -> None:
    module = _load_status_module()
    _complete_stage(tmp_path, module.STAGES[8])
    completed = subprocess.run(
        [sys.executable, "scripts/v13_pipeline_status.py", "--workspace", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "V13_PIPELINE_STATUS BLOCKED" in completed.stdout
