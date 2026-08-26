import interaction_sensing.v15 as v15


def test_v15_facade_exposes_prefreeze_gate_without_polluting_root_api() -> None:
    assert v15.PrefreezeGateState.BLOCKED_SAFE.value == "blocked_safe"
    assert v15.AbsenceStrategy.RETAIN_UPPER_BOUND_1.value == "retain_upper_bound_1_without_A_minus"
    assert "sampling_power_plan" in v15.CORE_FREEZE_ITEMS
    assert callable(v15.evaluate_prefreeze_registry)
    assert callable(v15.assert_ready_for_heldout)


def test_v15_facade_exposes_uncalibrated_nuisance_field_measurement() -> None:
    assert v15.NuisanceReferenceLayout.__name__ == "NuisanceReferenceLayout"
    assert v15.FieldNuisanceProcessMeasurement.__name__ == "FieldNuisanceProcessMeasurement"
    assert callable(v15.measure_field_nuisance_process)


def test_v15_facade_exposes_parameterized_cluster_power_planner() -> None:
    assert v15.EffectDirection.HIGHER_IS_BETTER.value == "higher_is_better"
    assert v15.ClusterPlanningAssumptions.__name__ == "ClusterPlanningAssumptions"
    assert callable(v15.plan_binary_metric_precision)
    assert callable(v15.plan_binary_system_comparison)
