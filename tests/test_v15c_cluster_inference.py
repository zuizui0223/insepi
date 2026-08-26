from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from interaction_sensing.cluster_inference_v15c import (
    HYPOTHESIS_IDS,
    PROTOCOL_CANONICAL_SHA256,
    evaluate_cluster_family,
    validate_analysis_plan,
    validate_v15c_protocol,
)
from interaction_sensing.heldout_measurement_v15b import (
    PROTOCOL_CANONICAL_SHA256 as V15B_PROTOCOL_CANONICAL_SHA256,
)
from interaction_sensing.heldout_measurement_v15b import SYSTEM_VARIANTS
from interaction_sensing.prefield_programming_closeout import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "benchmarks/v15c_cluster_inference_protocol.json"
PLAN_TEMPLATE_PATH = ROOT / "benchmarks/v15c_cluster_analysis_plan_TEMPLATE.json"
V15B_PROTOCOL_PATH = ROOT / "benchmarks/v15b_heldout_measurement_gate_protocol.json"
RUNNER_PATH = ROOT / "scripts/v15c_run_cluster_inference.py"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def protocol() -> dict[str, object]:
    return _read(PROTOCOL_PATH)


def v15b_protocol() -> dict[str, object]:
    return _read(V15B_PROTOCOL_PATH)


def analysis_plan(*, minimum_clusters: int = 4) -> dict[str, object]:
    return {
        "schema": "insepi-v15c-cluster-analysis-plan-v1",
        "status": "frozen-before-heldout-input",
        "protocol_canonical_sha256": PROTOCOL_CANONICAL_SHA256,
        "sample_size_plan_sha256": "5" * 64,
        "cluster_identity": "recording_date_local_x_physical_scene_code",
        "familywise_alpha": 0.05,
        "minimum_support": {
            "actual_day_x_scene_clusters": minimum_clusters,
            "pooled_resolved_visit_windows": 40,
            "pooled_observable_resolved_visit_windows": 20,
            "pooled_true_unobservable_windows": 40,
            "pooled_true_observable_windows": 40,
        },
        "claim_thresholds": {
            "minimum_false_absence_reduction": 0.20,
            "observable_visit_recall_noninferiority_margin": 0.05,
            "minimum_unobservable_recall": 0.80,
            "maximum_observable_false_censor_rate": 0.05,
        },
        "post_truth_plan_change_permitted": False,
    }


def measurement_freeze(plan: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "insepi-v15b-heldout-measurement-freeze-v1",
        "status": "frozen-before-heldout-input",
        "protocol_canonical_sha256": V15B_PROTOCOL_CANONICAL_SHA256,
        "v14b_phase_surface_sha256": (
            "1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34"
        ),
        "development_complete": True,
        "heldout_data_accessed_before_freeze": False,
        "observer_identity": {
            "target_observer_commit": "1" * 40,
            "nuisance_observer_commit": "2" * 40,
            "coupled_route_definition_sha256": "3" * 64,
            "support_measurement_profile_sha256": "4" * 64,
        },
        "analysis_identity": {
            "sample_size_plan_sha256": "5" * 64,
            "cluster_analysis_plan_sha256": canonical_json_sha256(plan),
            "cluster_identity": "recording_date_local_x_physical_scene_code",
            "frame_is_independent_replicate": False,
            "claim_mode": "descriptive_only_until_cluster_inference_generation",
            "familywise_alpha": 0.05,
        },
        "thresholds": {
            "target_high": 0.65,
            "target_low": 0.25,
            "nuisance_high": 0.60,
            "support_observable": 0.70,
            "support_unobservable": 0.30,
        },
        "missing_data_rule": "fail closed; unresolved support is not absence",
        "post_truth_retuning_permitted": False,
    }


def _cluster_row(
    date: str,
    scene: str,
    variant: str,
    *,
    supported: bool,
) -> dict[str, object]:
    is_baseline = variant == "target_plus_nuisance_without_support_gate"
    is_full = variant == "full_direct_coupled_target_nuisance_observability_triad"
    negative = (
        8 if is_baseline else (2 if supported and is_full else 7 if is_full else 5)
    )
    return {
        "recording_date_local": date,
        "physical_scene_code": scene,
        "system_variant": variant,
        "window_count": 100,
        "resolved_visit_windows": 20,
        "negative_calls_on_resolved_visit_windows": negative,
        "observable_resolved_visit_windows": 10,
        "retained_observable_resolved_visit_windows": 9,
        "true_unobservable_windows": 20,
        "censored_true_unobservable_windows": 19 if is_full else 0,
        "true_observable_windows": 60,
        "censored_true_observable_windows": 1 if is_full else 0,
    }


def descriptive_result(
    freeze: dict[str, object], *, supported: bool = True
) -> dict[str, object]:
    rows = [
        _cluster_row(
            f"2026-09-{10 + cluster_index:02d}",
            f"scene-{cluster_index}",
            variant,
            supported=supported,
        )
        for cluster_index in range(6)
        for variant in SYSTEM_VARIANTS
    ]
    measurement = {
        "window_count": 600,
        "block_count": 60,
        "actual_day_x_scene_cluster_count": 6,
        "cluster_inventory": [
            {
                "recording_date_local": f"2026-09-{10 + index:02d}",
                "physical_scene_code": f"scene-{index}",
                "window_count": 100,
            }
            for index in range(6)
        ],
        "cluster_sufficient_statistics_schema": (
            "insepi-v15b-day-scene-system-sufficient-statistics-v1"
        ),
        "cluster_sufficient_statistics": rows,
        "total_opportunity_seconds": 6000.0,
        "system_summaries": {},
        "familywise_alpha_retained": 0.05,
        "familywise_hypothesis_tests_executed": 0,
        "cluster_level_inference_executed": False,
    }
    return {
        "schema": "insepi-v15b-descriptive-heldout-evaluation-v2",
        "status": "descriptive-only-no-cluster-inference",
        "provenance": {
            "protocol_canonical_sha256": V15B_PROTOCOL_CANONICAL_SHA256,
            "measurement_freeze_canonical_sha256": canonical_json_sha256(freeze),
            "post_truth_retuning_permitted": False,
        },
        "measurement": measurement,
        "measurement_payload_canonical_sha256": canonical_json_sha256(measurement),
        "claim": {
            "level": "descriptive_only",
            "familywise_decision": None,
            "field_performance_claim": False,
        },
    }


def _chain(
    *, supported: bool = True, minimum_clusters: int = 4
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    plan = analysis_plan(minimum_clusters=minimum_clusters)
    freeze = measurement_freeze(plan)
    return plan, freeze, descriptive_result(freeze, supported=supported)


def _write(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _load_script():
    spec = importlib.util.spec_from_file_location("v15c_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_is_fixed_but_repository_plan_template_cannot_execute() -> None:
    validate_v15c_protocol(protocol())
    assert canonical_json_sha256(protocol()) == PROTOCOL_CANONICAL_SHA256
    template = _read(PLAN_TEMPLATE_PATH)
    fake_freeze = measurement_freeze(analysis_plan())
    with pytest.raises(ValueError, match="not executable"):
        validate_analysis_plan(
            template,
            protocol=protocol(),
            v15b_protocol=v15b_protocol(),
            measurement_freeze=fake_freeze,
        )


def test_supported_family_uses_four_simultaneous_cluster_bounds() -> None:
    plan, freeze, result = _chain(supported=True)
    evaluated = evaluate_cluster_family(
        protocol=protocol(),
        analysis_plan=plan,
        v15b_protocol=v15b_protocol(),
        measurement_freeze=freeze,
        descriptive_result=result,
    )

    assert evaluated["status"] == "familywise_supported"
    assert evaluated["familywise"]["alpha"] == 0.05
    assert evaluated["familywise"]["per_hypothesis_one_sided_alpha"] == 0.0125
    assert evaluated["familywise"]["hypothesis_tests_executed"] == 4
    assert tuple(row["id"] for row in evaluated["hypotheses"]) == HYPOTHESIS_IDS
    assert all(row["status"] == "supported" for row in evaluated["hypotheses"])
    assert evaluated["provenance"]["raw_truth_reopened"] is False
    assert evaluated["claim"]["censored_windows_are_biological_absence"] is False


def test_negative_family_result_is_retained_without_threshold_rescue() -> None:
    plan, freeze, result = _chain(supported=False)
    evaluated = evaluate_cluster_family(
        protocol=protocol(),
        analysis_plan=plan,
        v15b_protocol=v15b_protocol(),
        measurement_freeze=freeze,
        descriptive_result=result,
    )
    assert evaluated["status"] == "familywise_not_supported"
    h1 = next(row for row in evaluated["hypotheses"] if row["id"] == HYPOTHESIS_IDS[0])
    assert h1["status"] == "not_supported"
    assert evaluated["claim"]["field_observation_support_claim"] is False

    rescued = deepcopy(plan)
    rescued["claim_thresholds"]["minimum_false_absence_reduction"] = 0.01
    with pytest.raises(ValueError, match="differs from the hash frozen by V15b"):
        evaluate_cluster_family(
            protocol=protocol(),
            analysis_plan=rescued,
            v15b_protocol=v15b_protocol(),
            measurement_freeze=freeze,
            descriptive_result=result,
        )


def test_insufficient_cluster_support_is_reason_tagged_not_evaluable() -> None:
    plan, freeze, result = _chain(minimum_clusters=7)
    evaluated = evaluate_cluster_family(
        protocol=protocol(),
        analysis_plan=plan,
        v15b_protocol=v15b_protocol(),
        measurement_freeze=freeze,
        descriptive_result=result,
    )
    assert evaluated["status"] == "familywise_not_evaluable"
    assert evaluated["familywise"]["hypothesis_tests_executed"] == 0
    assert evaluated["support_failures"] == [
        {
            "quantity": "actual_day_x_scene_clusters",
            "observed": 6,
            "required_minimum": 7,
            "reason": "predeclared minimum support not reached",
        }
    ]


def test_v15b_sufficient_statistic_tamper_is_rejected() -> None:
    plan, freeze, result = _chain()
    result["measurement"]["cluster_sufficient_statistics"][0][
        "resolved_visit_windows"
    ] = 21
    with pytest.raises(ValueError, match="payload hash mismatch"):
        evaluate_cluster_family(
            protocol=protocol(),
            analysis_plan=plan,
            v15b_protocol=v15b_protocol(),
            measurement_freeze=freeze,
            descriptive_result=result,
        )

    result["measurement_payload_canonical_sha256"] = canonical_json_sha256(
        result["measurement"]
    )
    with pytest.raises(ValueError, match="denominators differ across systems"):
        evaluate_cluster_family(
            protocol=protocol(),
            analysis_plan=plan,
            v15b_protocol=v15b_protocol(),
            measurement_freeze=freeze,
            descriptive_result=result,
        )


def test_cli_reads_only_v15b_result_and_refuses_overwrite(tmp_path: Path) -> None:
    plan, freeze, source_result = _chain()
    plan_path = tmp_path / "plan.json"
    freeze_path = tmp_path / "freeze.json"
    source_path = tmp_path / "v15b-result.json"
    output_path = tmp_path / "v15c-result.json"
    _write(plan_path, plan)
    _write(freeze_path, freeze)
    _write(source_path, source_result)

    runner = _load_script()
    result = runner.run(
        protocol_path=PROTOCOL_PATH,
        analysis_plan_path=plan_path,
        v15b_protocol_path=V15B_PROTOCOL_PATH,
        measurement_freeze_path=freeze_path,
        v15b_result_path=source_path,
        output_path=output_path,
    )
    assert result == _read(output_path)
    assert result["status"] == "familywise_supported"
    with pytest.raises(FileExistsError, match="overwrite"):
        runner.run(
            protocol_path=PROTOCOL_PATH,
            analysis_plan_path=plan_path,
            v15b_protocol_path=V15B_PROTOCOL_PATH,
            measurement_freeze_path=freeze_path,
            v15b_result_path=source_path,
            output_path=output_path,
        )
