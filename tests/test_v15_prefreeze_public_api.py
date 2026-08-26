import interaction_sensing.v15 as v15


def test_v15_facade_exposes_prefreeze_gate_without_polluting_root_api() -> None:
    assert v15.PrefreezeGateState.BLOCKED_SAFE.value == "blocked_safe"
    assert v15.AbsenceStrategy.RETAIN_UPPER_BOUND_1.value == "retain_upper_bound_1_without_A_minus"
    assert "sampling_power_plan" in v15.CORE_FREEZE_ITEMS
    assert "coupled_field_adapter" in v15.CORE_FREEZE_ITEMS
    assert "target_nuisance_decision_calibration" in v15.CORE_FREEZE_ITEMS
    assert callable(v15.evaluate_prefreeze_registry)
    assert callable(v15.assert_ready_for_heldout)


def test_v15_facade_exposes_uncalibrated_nuisance_field_measurement() -> None:
    assert v15.NuisanceReferenceLayout.__name__ == "NuisanceReferenceLayout"
    assert v15.FieldNuisanceProcessMeasurement.__name__ == "FieldNuisanceProcessMeasurement"
    assert callable(v15.measure_field_nuisance_process)


def test_v15_facade_exposes_frozen_positive_only_pollipi_target_adapter() -> None:
    assert v15.POLLIPI_ORDINAL_TARGET_SCALE == "ordinal-v14-reference"
    assert v15.POLLIPI_TARGET_EVIDENCE_MAPPING["environmental_noise"] == 0.0
    record = v15.PolliPiTargetEvidenceInput("strong_visitation_candidate", 1.0)
    adapted = v15.adapt_pollipi_target_evidence(record)
    assert adapted.direct_target_score == 1.0
    assert adapted.to_target_routes().coupled_target_score == 0.0


def test_v15_facade_exposes_development_only_support_calibration() -> None:
    assert v15.SupportCalibrationBudget.__name__ == "SupportCalibrationBudget"
    assert v15.SupportCalibrationRow.__name__ == "SupportCalibrationRow"
    assert callable(v15.calibrate_support_thresholds)


def test_v15_facade_exposes_parameterized_cluster_power_planner() -> None:
    assert v15.EffectDirection.HIGHER_IS_BETTER.value == "higher_is_better"
    assert v15.ClusterPlanningAssumptions.__name__ == "ClusterPlanningAssumptions"
    assert callable(v15.plan_binary_metric_precision)
    assert callable(v15.plan_binary_system_comparison)


def test_v15_facade_exposes_confidence_bound_claim_gate() -> None:
    assert v15.ClaimDirection.AT_LEAST.value == "at_least"
    assert v15.ClaimDecision.NOT_EVALUABLE.value == "not_evaluable"
    assert v15.ClaimFamily.TARGET_ABSENCE.value == "target_absence"
    assert callable(v15.evaluate_claim)
