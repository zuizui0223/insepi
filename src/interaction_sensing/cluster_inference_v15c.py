"""Locked V15c family-wise inference on actual day x scene clusters.

V15c consumes only the descriptive sufficient statistics emitted by the V15b
truth join.  It never reopens raw truth or predictions.  A separately frozen
analysis plan supplies sample-support requirements and scientific thresholds;
the repository template is intentionally not executable.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

from .heldout_measurement_v15b import (
    FAMILYWISE_ALPHA,
    SYSTEM_VARIANTS,
    validate_measurement_freeze,
)
from .heldout_measurement_v15b import (
    PROTOCOL_CANONICAL_SHA256 as V15B_PROTOCOL_CANONICAL_SHA256,
)
from .prefield_programming_closeout import canonical_json_sha256

PROTOCOL_CANONICAL_SHA256 = (
    "61007eea4777a1d069aba52eb97d28d8ad2690f67e77f57275db0f17648184af"
)
V14B_PHASE_SURFACE_SHA256 = (
    "1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34"
)
V15A_MEASUREMENT_PAYLOAD_SHA256 = (
    "4346304cbef50a0e68ed57c2ae45356ed118b7a8713d08bf557ce7e1f4f185a1"
)
BASELINE_VARIANT = "target_plus_nuisance_without_support_gate"
FULL_VARIANT = "full_direct_coupled_target_nuisance_observability_triad"
HYPOTHESIS_IDS = (
    "H1_false_absence_reduction",
    "H2_observable_visit_recall_noninferiority",
    "H3_unobservable_recall_floor",
    "H4_observable_false_censor_ceiling",
)
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 1515
PER_HYPOTHESIS_ALPHA = 0.0125

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COUNT_FIELDS = (
    "window_count",
    "resolved_visit_windows",
    "negative_calls_on_resolved_visit_windows",
    "observable_resolved_visit_windows",
    "retained_observable_resolved_visit_windows",
    "true_unobservable_windows",
    "censored_true_unobservable_windows",
    "true_observable_windows",
    "censored_true_observable_windows",
)
_DENOMINATOR_FIELDS = (
    "window_count",
    "resolved_visit_windows",
    "observable_resolved_visit_windows",
    "true_unobservable_windows",
    "true_observable_windows",
)
_MINIMUM_SUPPORT_FIELDS = (
    "actual_day_x_scene_clusters",
    "pooled_resolved_visit_windows",
    "pooled_observable_resolved_visit_windows",
    "pooled_true_unobservable_windows",
    "pooled_true_observable_windows",
)
_THRESHOLD_FIELDS = (
    "minimum_false_absence_reduction",
    "observable_visit_recall_noninferiority_margin",
    "minimum_unobservable_recall",
    "maximum_observable_false_censor_rate",
)


def _mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = parent.get(name)
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be an object")
    return value


def _rows(parent: Mapping[str, Any], name: str) -> Sequence[Mapping[str, Any]]:
    value = parent.get(name)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an array")
    if not value or not all(isinstance(row, Mapping) for row in value):
        raise ValueError(f"{name} must be a non-empty array of objects")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{name} keys changed: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _sha(name: str, value: Any) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256")
    return value


def _positive_int(name: str, value: Any, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _probability(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must lie in [0, 1]")
    return result


def validate_v15c_protocol(protocol: Mapping[str, Any]) -> None:
    """Validate the immutable inference software contract."""

    if protocol.get("schema") != "insepi-v15c-cluster-familywise-inference-protocol-v1":
        raise ValueError("wrong V15c protocol schema")
    if (
        protocol.get("status")
        != "software-contract-prefrozen-no-field-execution-authorized"
    ):
        raise ValueError("V15c protocol status changed")
    parents = _mapping(protocol, "frozen_parents")
    if parents.get("v14b_phase_surface_sha256") != V14B_PHASE_SURFACE_SHA256:
        raise ValueError("V14b parent changed")
    if (
        parents.get("v15a_measurement_payload_sha256")
        != V15A_MEASUREMENT_PAYLOAD_SHA256
    ):
        raise ValueError("V15a parent changed")
    if parents.get("v15b_protocol_canonical_sha256") != V15B_PROTOCOL_CANONICAL_SHA256:
        raise ValueError("V15b parent changed")
    if parents.get("target_or_nuisance_observer_retuning_permitted") is not False:
        raise ValueError("T/N observer retuning was enabled")
    if parents.get("familywise_alpha") != FAMILYWISE_ALPHA:
        raise ValueError("family-wise alpha changed")

    unit = _mapping(protocol, "analysis_unit")
    if unit.get("cluster_identity") != "recording_date_local x physical_scene_code":
        raise ValueError("actual cluster identity changed")
    if unit.get("frame_is_independent_replicate") is not False:
        raise ValueError("frames were enabled as independent replicates")
    if unit.get("window_is_independent_replicate") is not False:
        raise ValueError("windows were enabled as independent replicates")
    comparison = _mapping(protocol, "comparison")
    if comparison.get("baseline") != BASELINE_VARIANT:
        raise ValueError("support-gate baseline changed")
    if comparison.get("system_under_test") != FULL_VARIANT:
        raise ValueError("full-triad system changed")

    family = protocol.get("family")
    if not isinstance(family, Sequence) or isinstance(family, (str, bytes)):
        raise TypeError("family must be an array")
    if (
        tuple(row.get("id") for row in family if isinstance(row, Mapping))
        != HYPOTHESIS_IDS
    ):
        raise ValueError("V15c hypothesis family changed")
    estimator = _mapping(protocol, "estimator")
    if estimator.get("bootstrap_resamples") != BOOTSTRAP_RESAMPLES:
        raise ValueError("bootstrap resample count changed")
    if estimator.get("bootstrap_seed") != BOOTSTRAP_SEED:
        raise ValueError("bootstrap seed changed")
    if estimator.get("bootstrap_quantile_method") != "linear":
        raise ValueError("bootstrap quantile method changed")
    if estimator.get("multiplicity") != "Bonferroni simultaneous family":
        raise ValueError("family-wise correction changed")
    if estimator.get("hypothesis_count") != len(HYPOTHESIS_IDS):
        raise ValueError("hypothesis count changed")
    if estimator.get("per_hypothesis_one_sided_alpha") != PER_HYPOTHESIS_ALPHA:
        raise ValueError("per-hypothesis alpha changed")

    decision = _mapping(protocol, "decision_rule")
    if decision.get("post_truth_threshold_change_permitted") is not False:
        raise ValueError("post-truth threshold changes were enabled")
    if decision.get("failure_is_retained") is not True:
        raise ValueError("negative family outcomes would not be retained")
    gate = _mapping(protocol, "execution_gate")
    if gate.get("repository_analysis_plan_template_is_executable") is not False:
        raise ValueError("repository analysis-plan template became executable")
    if gate.get("committed_real_heldout_result_present") is not False:
        raise ValueError("protocol falsely reports a real V15c result")
    if canonical_json_sha256(protocol) != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("V15c protocol identity changed")


def validate_analysis_plan(
    plan: Mapping[str, Any],
    *,
    protocol: Mapping[str, Any],
    v15b_protocol: Mapping[str, Any],
    measurement_freeze: Mapping[str, Any],
) -> tuple[dict[str, int], dict[str, float]]:
    """Validate a real plan and its pre-heldout binding to the V15b freeze."""

    validate_v15c_protocol(protocol)
    validate_measurement_freeze(measurement_freeze, v15b_protocol)
    _exact_keys(
        plan,
        {
            "schema",
            "status",
            "protocol_canonical_sha256",
            "sample_size_plan_sha256",
            "cluster_identity",
            "familywise_alpha",
            "minimum_support",
            "claim_thresholds",
            "post_truth_plan_change_permitted",
        },
        "V15c analysis plan",
    )
    if plan.get("schema") != "insepi-v15c-cluster-analysis-plan-v1":
        raise ValueError("wrong V15c analysis-plan schema")
    if plan.get("status") != "frozen-before-heldout-input":
        raise ValueError("V15c analysis plan is not executable")
    if plan.get("protocol_canonical_sha256") != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("analysis plan references the wrong V15c protocol")
    if plan.get("cluster_identity") != "recording_date_local_x_physical_scene_code":
        raise ValueError("analysis-plan cluster identity changed")
    if plan.get("familywise_alpha") != FAMILYWISE_ALPHA:
        raise ValueError("analysis-plan family-wise alpha changed")
    if plan.get("post_truth_plan_change_permitted") is not False:
        raise ValueError("post-truth analysis-plan changes were enabled")

    analysis_identity = _mapping(measurement_freeze, "analysis_identity")
    sample_size_sha = _sha(
        "sample_size_plan_sha256", plan.get("sample_size_plan_sha256")
    )
    if sample_size_sha != analysis_identity.get("sample_size_plan_sha256"):
        raise ValueError("analysis plan references the wrong sample-size plan")
    if canonical_json_sha256(plan) != analysis_identity.get(
        "cluster_analysis_plan_sha256"
    ):
        raise ValueError("analysis plan differs from the hash frozen by V15b")

    raw_support = _mapping(plan, "minimum_support")
    _exact_keys(raw_support, set(_MINIMUM_SUPPORT_FIELDS), "minimum support")
    minimum_support = {
        name: _positive_int(
            name,
            raw_support.get(name),
            minimum=2 if name == "actual_day_x_scene_clusters" else 1,
        )
        for name in _MINIMUM_SUPPORT_FIELDS
    }
    raw_thresholds = _mapping(plan, "claim_thresholds")
    _exact_keys(raw_thresholds, set(_THRESHOLD_FIELDS), "claim thresholds")
    thresholds = {
        name: _probability(name, raw_thresholds.get(name)) for name in _THRESHOLD_FIELDS
    }
    if thresholds["minimum_false_absence_reduction"] <= 0.0:
        raise ValueError("minimum false-absence reduction must be positive")
    if thresholds["minimum_unobservable_recall"] <= 0.0:
        raise ValueError("minimum unobservable recall must be positive")
    if thresholds["observable_visit_recall_noninferiority_margin"] >= 1.0:
        raise ValueError("observable-visit noninferiority margin must be below one")
    if thresholds["maximum_observable_false_censor_rate"] >= 1.0:
        raise ValueError("observable false-censor ceiling must be below one")
    return minimum_support, thresholds


def _validated_cluster_rows(
    result: Mapping[str, Any],
    *,
    measurement_freeze: Mapping[str, Any],
) -> dict[tuple[str, str], dict[str, dict[str, int]]]:
    if result.get("schema") != "insepi-v15b-descriptive-heldout-evaluation-v2":
        raise ValueError("V15c requires the V15b v2 descriptive result")
    if result.get("status") != "descriptive-only-no-cluster-inference":
        raise ValueError("source is not a descriptive-only V15b result")
    provenance = _mapping(result, "provenance")
    if provenance.get("protocol_canonical_sha256") != V15B_PROTOCOL_CANONICAL_SHA256:
        raise ValueError("source result references the wrong V15b protocol")
    if provenance.get("measurement_freeze_canonical_sha256") != canonical_json_sha256(
        measurement_freeze
    ):
        raise ValueError("source result references the wrong measurement freeze")
    if provenance.get("post_truth_retuning_permitted") is not False:
        raise ValueError("source result permits post-truth retuning")

    measurement = _mapping(result, "measurement")
    if canonical_json_sha256(measurement) != result.get(
        "measurement_payload_canonical_sha256"
    ):
        raise ValueError("V15b measurement payload hash mismatch")
    if measurement.get("familywise_alpha_retained") != FAMILYWISE_ALPHA:
        raise ValueError("source result changed family-wise alpha")
    if measurement.get("familywise_hypothesis_tests_executed") != 0:
        raise ValueError("source V15b result already executed family-wise tests")
    if measurement.get("cluster_level_inference_executed") is not False:
        raise ValueError("source V15b result already executed cluster inference")
    if (
        measurement.get("cluster_sufficient_statistics_schema")
        != "insepi-v15b-day-scene-system-sufficient-statistics-v1"
    ):
        raise ValueError("wrong V15b sufficient-statistics schema")

    expected_keys = {
        "recording_date_local",
        "physical_scene_code",
        "system_variant",
        *_COUNT_FIELDS,
    }
    clusters: dict[tuple[str, str], dict[str, dict[str, int]]] = {}
    for row in _rows(measurement, "cluster_sufficient_statistics"):
        _exact_keys(row, expected_keys, "cluster sufficient-statistic row")
        date = row.get("recording_date_local")
        scene = row.get("physical_scene_code")
        variant = row.get("system_variant")
        if not isinstance(date, str) or not date.strip():
            raise ValueError("recording_date_local cannot be empty")
        if not isinstance(scene, str) or not scene.strip():
            raise ValueError("physical_scene_code cannot be empty")
        if variant not in SYSTEM_VARIANTS:
            raise ValueError("unknown system variant in sufficient statistics")
        bucket = clusters.setdefault((date, scene), {})
        if variant in bucket:
            raise ValueError("duplicate cluster/system sufficient-statistic row")
        counts = {
            name: _positive_int(
                name,
                row.get(name),
                minimum=1 if name == "window_count" else 0,
            )
            for name in _COUNT_FIELDS
        }
        for numerator, denominator in (
            ("negative_calls_on_resolved_visit_windows", "resolved_visit_windows"),
            (
                "retained_observable_resolved_visit_windows",
                "observable_resolved_visit_windows",
            ),
            ("censored_true_unobservable_windows", "true_unobservable_windows"),
            ("censored_true_observable_windows", "true_observable_windows"),
        ):
            if counts[numerator] > counts[denominator]:
                raise ValueError(f"{numerator} exceeds {denominator}")
        if any(
            counts[name] > counts["window_count"] for name in _DENOMINATOR_FIELDS[1:]
        ):
            raise ValueError("cluster denominator exceeds window_count")
        if (
            counts["observable_resolved_visit_windows"]
            > counts["resolved_visit_windows"]
        ):
            raise ValueError(
                "observable resolved visits exceed all resolved visit windows"
            )
        if (
            counts["observable_resolved_visit_windows"]
            > counts["true_observable_windows"]
        ):
            raise ValueError(
                "observable resolved visits exceed truth-observable windows"
            )
        if (
            counts["true_unobservable_windows"] + counts["true_observable_windows"]
            > counts["window_count"]
        ):
            raise ValueError("resolved support denominators exceed window_count")
        bucket[str(variant)] = counts

    expected_variants = set(SYSTEM_VARIANTS)
    for cluster, variants in clusters.items():
        if set(variants) != expected_variants:
            raise ValueError(f"cluster {cluster} does not contain all five systems")
        reference = variants[SYSTEM_VARIANTS[0]]
        for variant in SYSTEM_VARIANTS[1:]:
            if any(
                variants[variant][field] != reference[field]
                for field in _DENOMINATOR_FIELDS
            ):
                raise ValueError(
                    f"truth denominators differ across systems in cluster {cluster}"
                )

    if len(clusters) != measurement.get("actual_day_x_scene_cluster_count"):
        raise ValueError("cluster count differs from the V15b inventory")
    inventory: dict[tuple[str, str], int] = {}
    for row in _rows(measurement, "cluster_inventory"):
        _exact_keys(
            row,
            {"recording_date_local", "physical_scene_code", "window_count"},
            "cluster inventory row",
        )
        key = (str(row["recording_date_local"]), str(row["physical_scene_code"]))
        if key in inventory:
            raise ValueError("duplicate V15b cluster inventory row")
        inventory[key] = _positive_int("cluster window_count", row["window_count"])
    expected_inventory = {
        key: variants[SYSTEM_VARIANTS[0]]["window_count"]
        for key, variants in clusters.items()
    }
    if inventory != expected_inventory:
        raise ValueError("cluster inventory differs from sufficient statistics")
    if sum(inventory.values()) != measurement.get("window_count"):
        raise ValueError("cluster inventory does not sum to V15b window_count")
    return clusters


def _rate(matrix: np.ndarray, numerator: int, denominator: int) -> np.ndarray:
    den = matrix[:, :, denominator].sum(axis=1)
    if np.any(den == 0):
        raise ZeroDivisionError("a bootstrap resample has a zero estimand denominator")
    return matrix[:, :, numerator].sum(axis=1) / den


def _bound(draws: np.ndarray, *, side: str) -> float:
    quantile = PER_HYPOTHESIS_ALPHA if side == "lower" else 1.0 - PER_HYPOTHESIS_ALPHA
    return float(np.quantile(draws, quantile, method="linear"))


def evaluate_cluster_family(
    *,
    protocol: Mapping[str, Any],
    analysis_plan: Mapping[str, Any],
    v15b_protocol: Mapping[str, Any],
    measurement_freeze: Mapping[str, Any],
    descriptive_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Run the locked four-hypothesis family or retain a not-evaluable result."""

    minimum_support, thresholds = validate_analysis_plan(
        analysis_plan,
        protocol=protocol,
        v15b_protocol=v15b_protocol,
        measurement_freeze=measurement_freeze,
    )
    clusters = _validated_cluster_rows(
        descriptive_result,
        measurement_freeze=measurement_freeze,
    )
    ordered_keys = sorted(clusters)
    full_rows = [clusters[key][FULL_VARIANT] for key in ordered_keys]
    baseline_rows = [clusters[key][BASELINE_VARIANT] for key in ordered_keys]

    actual_support = {
        "actual_day_x_scene_clusters": len(ordered_keys),
        "pooled_resolved_visit_windows": sum(
            row["resolved_visit_windows"] for row in full_rows
        ),
        "pooled_observable_resolved_visit_windows": sum(
            row["observable_resolved_visit_windows"] for row in full_rows
        ),
        "pooled_true_unobservable_windows": sum(
            row["true_unobservable_windows"] for row in full_rows
        ),
        "pooled_true_observable_windows": sum(
            row["true_observable_windows"] for row in full_rows
        ),
    }
    support_failures = [
        {
            "quantity": name,
            "observed": actual_support[name],
            "required_minimum": minimum_support[name],
            "reason": "predeclared minimum support not reached",
        }
        for name in _MINIMUM_SUPPORT_FIELDS
        if actual_support[name] < minimum_support[name]
    ]
    provenance = {
        "protocol_canonical_sha256": PROTOCOL_CANONICAL_SHA256,
        "analysis_plan_canonical_sha256": canonical_json_sha256(analysis_plan),
        "v15b_protocol_canonical_sha256": V15B_PROTOCOL_CANONICAL_SHA256,
        "v15b_measurement_freeze_canonical_sha256": canonical_json_sha256(
            measurement_freeze
        ),
        "source_v15b_result_canonical_sha256": canonical_json_sha256(
            descriptive_result
        ),
        "source_v15b_measurement_payload_canonical_sha256": descriptive_result.get(
            "measurement_payload_canonical_sha256"
        ),
        "raw_truth_reopened": False,
        "post_truth_retuning_permitted": False,
    }
    if support_failures:
        return {
            "schema": "insepi-v15c-cluster-familywise-result-v1",
            "status": "familywise_not_evaluable",
            "provenance": provenance,
            "actual_support": actual_support,
            "minimum_support": minimum_support,
            "support_failures": support_failures,
            "hypotheses": [],
            "familywise": {
                "alpha": FAMILYWISE_ALPHA,
                "method": "Bonferroni simultaneous family",
                "hypothesis_tests_executed": 0,
                "decision": "not_evaluable",
            },
            "claim": {
                "field_observation_support_claim": False,
                "reason": "predeclared cluster or denominator support was not reached",
            },
        }

    field_index = {name: index for index, name in enumerate(_COUNT_FIELDS)}
    full_array = np.asarray(
        [[row[name] for name in _COUNT_FIELDS] for row in full_rows], dtype=float
    )
    baseline_array = np.asarray(
        [[row[name] for name in _COUNT_FIELDS] for row in baseline_rows], dtype=float
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    chosen = rng.integers(
        0, len(ordered_keys), size=(BOOTSTRAP_RESAMPLES, len(ordered_keys))
    )
    full_boot = full_array[chosen]
    baseline_boot = baseline_array[chosen]

    try:
        h1_draws = _rate(
            baseline_boot,
            field_index["negative_calls_on_resolved_visit_windows"],
            field_index["resolved_visit_windows"],
        ) - _rate(
            full_boot,
            field_index["negative_calls_on_resolved_visit_windows"],
            field_index["resolved_visit_windows"],
        )
        h2_draws = _rate(
            full_boot,
            field_index["retained_observable_resolved_visit_windows"],
            field_index["observable_resolved_visit_windows"],
        ) - _rate(
            baseline_boot,
            field_index["retained_observable_resolved_visit_windows"],
            field_index["observable_resolved_visit_windows"],
        )
        h3_draws = _rate(
            full_boot,
            field_index["censored_true_unobservable_windows"],
            field_index["true_unobservable_windows"],
        )
        h4_draws = _rate(
            full_boot,
            field_index["censored_true_observable_windows"],
            field_index["true_observable_windows"],
        )
    except ZeroDivisionError as exc:
        return {
            "schema": "insepi-v15c-cluster-familywise-result-v1",
            "status": "familywise_not_evaluable",
            "provenance": provenance,
            "actual_support": actual_support,
            "minimum_support": minimum_support,
            "support_failures": [
                {
                    "quantity": "bootstrap_estimand_denominator",
                    "observed": None,
                    "required_minimum": "nonzero in every paired cluster resample",
                    "reason": str(exc),
                }
            ],
            "hypotheses": [],
            "familywise": {
                "alpha": FAMILYWISE_ALPHA,
                "method": "Bonferroni simultaneous family",
                "hypothesis_tests_executed": 0,
                "decision": "not_evaluable",
            },
            "claim": {
                "field_observation_support_claim": False,
                "reason": "at least one bootstrap estimand denominator was zero",
            },
        }

    def pooled(
        row_set: list[dict[str, int]], numerator: str, denominator: str
    ) -> float:
        return sum(row[numerator] for row in row_set) / sum(
            row[denominator] for row in row_set
        )

    h1_estimate = pooled(
        baseline_rows,
        "negative_calls_on_resolved_visit_windows",
        "resolved_visit_windows",
    ) - pooled(
        full_rows,
        "negative_calls_on_resolved_visit_windows",
        "resolved_visit_windows",
    )
    h2_estimate = pooled(
        full_rows,
        "retained_observable_resolved_visit_windows",
        "observable_resolved_visit_windows",
    ) - pooled(
        baseline_rows,
        "retained_observable_resolved_visit_windows",
        "observable_resolved_visit_windows",
    )
    h3_estimate = pooled(
        full_rows,
        "censored_true_unobservable_windows",
        "true_unobservable_windows",
    )
    h4_estimate = pooled(
        full_rows,
        "censored_true_observable_windows",
        "true_observable_windows",
    )
    h1_bound = _bound(h1_draws, side="lower")
    h2_bound = _bound(h2_draws, side="lower")
    h3_bound = _bound(h3_draws, side="lower")
    h4_bound = _bound(h4_draws, side="upper")

    hypotheses = [
        {
            "id": HYPOTHESIS_IDS[0],
            "estimate": h1_estimate,
            "bound_side": "lower",
            "simultaneous_bound": h1_bound,
            "threshold": thresholds["minimum_false_absence_reduction"],
            "status": "supported"
            if h1_bound >= thresholds["minimum_false_absence_reduction"]
            else "not_supported",
        },
        {
            "id": HYPOTHESIS_IDS[1],
            "estimate": h2_estimate,
            "bound_side": "lower",
            "simultaneous_bound": h2_bound,
            "threshold": -thresholds["observable_visit_recall_noninferiority_margin"],
            "status": "supported"
            if h2_bound >= -thresholds["observable_visit_recall_noninferiority_margin"]
            else "not_supported",
        },
        {
            "id": HYPOTHESIS_IDS[2],
            "estimate": h3_estimate,
            "bound_side": "lower",
            "simultaneous_bound": h3_bound,
            "threshold": thresholds["minimum_unobservable_recall"],
            "status": "supported"
            if h3_bound >= thresholds["minimum_unobservable_recall"]
            else "not_supported",
        },
        {
            "id": HYPOTHESIS_IDS[3],
            "estimate": h4_estimate,
            "bound_side": "upper",
            "simultaneous_bound": h4_bound,
            "threshold": thresholds["maximum_observable_false_censor_rate"],
            "status": "supported"
            if h4_bound <= thresholds["maximum_observable_false_censor_rate"]
            else "not_supported",
        },
    ]
    supported = all(row["status"] == "supported" for row in hypotheses)
    decision = "supported" if supported else "not_supported"
    return {
        "schema": "insepi-v15c-cluster-familywise-result-v1",
        "status": f"familywise_{decision}",
        "provenance": provenance,
        "actual_support": actual_support,
        "minimum_support": minimum_support,
        "support_failures": [],
        "bootstrap": {
            "resampling_unit": "actual recording_date_local x physical_scene_code cluster",
            "paired_across_systems": True,
            "resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
            "quantile_method": "linear",
        },
        "hypotheses": hypotheses,
        "familywise": {
            "alpha": FAMILYWISE_ALPHA,
            "method": "Bonferroni simultaneous family",
            "per_hypothesis_one_sided_alpha": PER_HYPOTHESIS_ALPHA,
            "hypothesis_tests_executed": len(HYPOTHESIS_IDS),
            "decision": decision,
        },
        "claim": {
            "field_observation_support_claim": supported,
            "reason": (
                "all four locked observation-support hypotheses met their thresholds"
                if supported
                else "at least one locked observation-support hypothesis missed its threshold"
            ),
            "censored_windows_are_biological_absence": False,
            "universal_superiority_claim": False,
            "pollination_effectiveness_claim": False,
        },
    }
