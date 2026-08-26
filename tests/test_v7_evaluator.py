from interaction_sensing.simulation.v7_evaluator import (
    apply_locked_gate,
    build_report,
    evaluate_v7_traces,
    load_baseline_registry,
)


DUMMY_MASTER_SEED = "ef" * 32


def _dummy_traces():
    pollipi = []
    insepi = []
    states = [
        (False, "no_activity", 0.05),
        (False, "strong_visitation_candidate", 0.75),
        (False, "environmental_noise", 0.85),
        (True, "strong_visitation_candidate", 0.05),
        (True, "no_activity", 0.80),
        (True, "environmental_noise", 0.90),
        (True, "uncertain_local_activity", 0.55),
        (False, "no_activity", 0.65),
    ]
    families = ["clean", "clutter", "wind", "clean", "occlusion", "shadow", "blur", "lens"]
    for index, ((true_visit, state, risk), family) in enumerate(zip(states, families, strict=True)):
        condition_id = f"dummy-{index}"
        pollipi.append({
            "condition_id": condition_id,
            "true_visit": true_visit,
            "family": family,
            "pollipi_state": state,
        })
        insepi.append({
            "condition_id": condition_id,
            "true_visit": true_visit,
            "family": family,
            "false_event_risk": risk,
            "missed_event_risk": risk,
            "attribution_risk": risk / 2,
        })
    return pollipi, insepi


def test_baseline_registry_hash_is_frozen():
    registry = load_baseline_registry("benchmarks/v7_baseline_registry.json")
    assert len(registry["entries"]) == 9
    assert registry["registry_sha256"] == "94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975"


def test_trace_only_evaluator_runs_all_locked_policies_on_paired_dummy_worlds():
    pollipi, insepi = _dummy_traces()
    registry = load_baseline_registry("benchmarks/v7_baseline_registry.json")
    metrics = evaluate_v7_traces(
        pollipi,
        insepi,
        registry,
        master_seed_hex=DUMMY_MASTER_SEED,
        prevalences=(0.25, 0.75),
        budgets=(0.5,),
        world_windows=240,
        replicates=8,
    )
    assert len(metrics) == 18  # 2 regimes x 9 policies
    assert {row.policy for row in metrics} == {entry["name"] for entry in registry["entries"]}
    assert all(0.0 <= row.true_event_recall <= 1.0 for row in metrics)
    assert all(0.0 <= row.hidden_error_recall <= 1.0 for row in metrics)
    assert all(0.0 <= row.disturbance_tv_distance <= 1.0 for row in metrics)


def test_locked_gate_and_report_are_deterministic_on_dummy_traces():
    pollipi, insepi = _dummy_traces()
    registry = load_baseline_registry("benchmarks/v7_baseline_registry.json")
    kwargs = dict(
        pollipi_rows=pollipi,
        insepi_rows=insepi,
        baseline_registry=registry,
        master_seed_hex=DUMMY_MASTER_SEED,
        prevalences=(0.25, 0.75),
        budgets=(0.5,),
        world_windows=240,
        replicates=8,
    )
    first = evaluate_v7_traces(**kwargs)
    second = evaluate_v7_traces(**kwargs)
    assert first == second

    gate = apply_locked_gate(first)
    report_a = build_report(metrics=first, gate=gate, provenance={"dummy": True})
    report_b = build_report(metrics=second, gate=gate, provenance={"dummy": True})
    assert report_a["report_sha256"] == report_b["report_sha256"]
    assert len(report_a["report_sha256"]) == 64
