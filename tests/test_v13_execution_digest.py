from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "benchmarks/v13_execution_freeze.json"


def _load_digest_module():
    path = ROOT / "scripts/v13_execution_digest.py"
    spec = importlib.util.spec_from_file_location("v13_execution_digest_test_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


digest = _load_digest_module()


def test_v13_execution_digest_covers_scientific_and_execution_boundaries() -> None:
    paths = set(digest.CRITICAL_PATHS)
    required = {
        "benchmarks/v13_observer_measurement_freeze.json",
        "benchmarks/v13_physical_intervention_protocol.json",
        "benchmarks/v13_physical_phase_contract.json",
        "src/interaction_sensing/causal_diagnostics.py",
        "src/interaction_sensing/physical_artifact_v13.py",
        "src/interaction_sensing/physical_evaluation_v13.py",
        "src/interaction_sensing/physical_measurement_v13.py",
        "src/interaction_sensing/simulation/real_video_v10.py",
        "scripts/v13_run_pollipi_frozen.py",
        "scripts/v13_run_insepi_frozen.py",
        "scripts/v13_predict_blinded.py",
        "scripts/v13_evaluate_locked.py",
    }
    assert required <= paths
    assert ".github/workflows/v13-pre-field.yml" not in paths
    assert "scripts/v13_execution_digest.py" not in paths
    assert "benchmarks/v13_execution_freeze.json" not in paths
    assert len(paths) == len(digest.CRITICAL_PATHS) == 21
    assert all((ROOT / path).is_file() for path in paths)


def test_v13_execution_digest_is_stable_for_same_tree() -> None:
    first = digest.execution_digest(ROOT)
    second = digest.execution_digest(ROOT)
    assert first == second
    assert len(first) == 64


def test_v13_execution_digest_changes_when_one_critical_byte_changes(tmp_path: Path) -> None:
    # Copy the critical tree to a temporary root so the real repository is never modified.
    for relative in digest.CRITICAL_PATHS:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    baseline = digest.execution_digest(tmp_path)
    target = tmp_path / digest.CRITICAL_PATHS[0]
    target.write_bytes(target.read_bytes() + b"\n")
    assert digest.execution_digest(tmp_path) != baseline


def test_v13_committed_execution_freeze_matches_current_scientific_tree() -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert freeze["schema"] == "interaction-sensing-v13-execution-freeze-v1"
    assert freeze["status"] == "pre-field-scientific-execution-frozen"
    assert freeze["critical_path_count"] == len(digest.CRITICAL_PATHS) == 21
    assert digest.execution_digest(ROOT) == freeze["scientific_execution_digest_sha256"]

    helper_path = ROOT / freeze["digest_helper"]["path"]
    helper_sha256 = hashlib.sha256(helper_path.read_bytes()).hexdigest()
    assert helper_sha256 == freeze["digest_helper"]["sha256"]

    assert freeze["runtime"] == {
        "python": "3.11.16",
        "numpy": "2.4.6",
        "imageio_ffmpeg": "0.6.0",
        "ffmpeg_executable_sha256": "e7e7fb30477f717e6f55f9180a70386c62677ef8a4d4d1a5d948f4098aa3eb99",
    }
    assert freeze["observers"]["pollipi_commit"] == "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
    assert freeze["observers"]["insepi_commit"] == "980813bab996909020140fad5bd83b055eb3db9c"
    assert freeze["observers"]["branch_name"] == "frozen/v5-method"
    assert not any(freeze["materialisation_state"].values())
