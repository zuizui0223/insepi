from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
    assert len(paths) == len(digest.CRITICAL_PATHS)
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
