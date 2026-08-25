from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from interaction_sensing.simulation.v14a2_sweep import replicate_seed

ROOT = Path(__file__).resolve().parents[1]


def _runner_module():
    path = ROOT / "scripts/run_v14a2_spatiotemporal_sweep.py"
    spec = importlib.util.spec_from_file_location("v14a2_locked_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prefrozen_replicate_seed_rule_is_deterministic_and_separates_indices() -> None:
    assert replicate_seed(0, 0, 0) == 1_402_000_000
    assert replicate_seed(1, 0, 0) == 1_402_001_000
    assert replicate_seed(0, 1, 0) == 1_402_000_100
    assert replicate_seed(0, 0, 1) == 1_402_000_001


def test_full_runner_fails_closed_without_prefreeze_receipt(tmp_path: Path) -> None:
    runner = _runner_module()
    with pytest.raises(RuntimeError, match="prefreeze receipt is absent"):
        runner.run(
            ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json",
            tmp_path / "missing_receipt.json",
            tmp_path / "out",
            sweep_name="coarse_sweep",
            smoke_limit=None,
        )


def test_tiny_smoke_is_noncanonical_and_does_not_need_receipt(tmp_path: Path) -> None:
    runner = _runner_module()
    result = runner.run(
        ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json",
        tmp_path / "missing_receipt.json",
        tmp_path / "out",
        sweep_name="coarse_sweep",
        smoke_limit=1,
    )
    assert result["canonical"] is False
    assert result["world_count"] == 20
    assert result["surface_row_count"] == 5
