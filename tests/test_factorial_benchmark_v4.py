from interaction_sensing.simulation.factorial_benchmark_v4 import (
    run_factorial_v4,
    summarize_factorial_v4,
)


def test_factorial_v4_insepi_runner_is_deterministic_and_split_safe():
    first = run_factorial_v4()
    second = run_factorial_v4()
    assert [row.to_dict() for row in first] == [row.to_dict() for row in second]
    assert len(first) == 120
    assert len(run_factorial_v4("calibration")) == 52
    assert len(run_factorial_v4("test")) == 68
    summary = summarize_factorial_v4(first)
    assert 0.0 <= summary["calibration_disturbance_risk_recall"] <= 1.0
    assert 0.0 <= summary["test_disturbance_risk_recall"] <= 1.0
