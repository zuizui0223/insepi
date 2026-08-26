from pathlib import Path


def test_nuisance_validation_runner_exists() -> None:
    root = Path(__file__).resolve().parents[1]
    assert (root / "scripts/run_v14b_nuisance_observer_process_scale_validation.py").exists()
