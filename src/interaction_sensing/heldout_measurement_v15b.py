"""Fail-closed V15b boundary for blinded prediction and held-out truth join.

The prediction stage consumes only truth-free T/C/N/O component outputs plus a
receipt for an externally sealed truth bundle.  The evaluation stage validates
the prediction commitment before it accepts the truth bundle.  This module is a
software gate; it deliberately performs no cluster-level hypothesis test.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from .layered_visit_truth import (
    BiologicalTruthAnnotation,
    CouplingTruthAnnotation,
    NuisanceTruthAnnotation,
    SupportTruthAnnotation,
    join_layered_truth,
)
from .nuisance_effects import NuisanceEffect
from .observation_triad import NuisanceEvidence
from .prefield_programming_closeout import canonical_json_sha256
from .support_estimation import (
    PrimaryStreamSupportEstimator,
    PrimaryStreamSupportMeasurements,
    SupportComponentMeasurement,
    SupportMeasurementProvenance,
)
from .support_truth import PrimaryStreamSupportTruth, SupportComponentState
from .target_routes import TargetRouteEvidence
from .visit_systems import (
    VisitSystemInputs,
    VisitSystemThresholds,
    VisitSystemVariant,
    predict_all_visit_variants,
)
from .visit_validation import (
    CoupledResponseResolution,
    VisitPredictionRecord,
    VisitTruthRecord,
    VisitTruthResolution,
    VisitTruthState,
    evaluate_visit_predictions,
)

PROTOCOL_CANONICAL_SHA256 = (
    "156a505fe05279e9dbd4726eeb59082151fe54944f5cb7ea1a5eebcbe3bc9f8f"
)
V14B_PHASE_SURFACE_SHA256 = (
    "1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34"
)
V15A_MEASUREMENT_PAYLOAD_SHA256 = (
    "4346304cbef50a0e68ed57c2ae45356ed118b7a8713d08bf557ce7e1f4f185a1"
)
FAMILYWISE_ALPHA = 0.05
SUPPORT_COMPONENTS = (
    "target_zone_coverage",
    "target_zone_visibility",
    "spatial_resolution",
    "photometric_sufficiency",
    "temporal_continuity",
)
SYSTEM_VARIANTS = tuple(variant.value for variant in VisitSystemVariant)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True, slots=True)
class _PreparedWindow:
    window_id: str
    block_id: str
    recording_date_local: str
    physical_scene_code: str
    opportunity_seconds: float
    primary_clip_sha256: str
    inputs: VisitSystemInputs


def _mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = parent.get(name)
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be an object")
    return value


def _rows(parent: Mapping[str, Any], name: str) -> Sequence[Mapping[str, Any]]:
    value = parent.get(name)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an array")
    if not value:
        raise ValueError(f"{name} cannot be empty")
    if not all(isinstance(row, Mapping) for row in value):
        raise TypeError(f"every {name} item must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], name: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValueError(
            f"{name} keys changed: missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _require_sha(name: str, value: Any) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256")
    return value


def _require_commit(name: str, value: Any) -> str:
    if not isinstance(value, str) or _COMMIT.fullmatch(value) is None:
        raise ValueError(f"{name} must be a full lowercase Git commit")
    return value


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    return value


def _string(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text")
    return value


def _nullable_text(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _require_text(name, value)


def _require_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be boolean")
    return value


def _number(name: str, value: Any, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric")
    result = float(value)
    if positive and result <= 0.0:
        raise ValueError(f"{name} must be positive")
    return result


def validate_v15b_protocol(protocol: Mapping[str, Any]) -> None:
    """Verify the complete immutable software contract."""

    if protocol.get("schema") != "insepi-v15b-heldout-measurement-gate-protocol-v1":
        raise ValueError("wrong V15b gate protocol schema")
    if (
        protocol.get("status")
        != "software-contract-prefrozen-no-field-execution-authorized"
    ):
        raise ValueError("V15b gate protocol status changed")
    parents = _mapping(protocol, "frozen_parents")
    if parents.get("v14b_phase_surface_sha256") != V14B_PHASE_SURFACE_SHA256:
        raise ValueError("V14b phase-surface parent changed")
    if (
        parents.get("v15a_measurement_payload_sha256")
        != V15A_MEASUREMENT_PAYLOAD_SHA256
    ):
        raise ValueError("V15a measurement parent changed")
    if parents.get("v14b_or_v15a_retuning_permitted") is not False:
        raise ValueError("closed parent retuning was enabled")
    if parents.get("familywise_alpha") != FAMILYWISE_ALPHA:
        raise ValueError("family-wise alpha changed")

    prediction = _mapping(protocol, "prediction_stage")
    if list(prediction.get("system_variants", [])) != list(SYSTEM_VARIANTS):
        raise ValueError("V15b system variants changed")
    if prediction.get("full_triad_policy") != "ProcessPreservingObservationTriadPolicy":
        raise ValueError("V15b full-triad policy changed")
    if prediction.get("heldout_truth_read") is not False:
        raise ValueError("prediction stage reports held-out truth access")
    truth = _mapping(protocol, "truth_stage")
    if truth.get("automatic_cross_layer_conflict_resolution") is not False:
        raise ValueError("automatic truth conflict resolution was enabled")
    if truth.get("unresolved_truth_is_absence") is not False:
        raise ValueError("unresolved truth was converted to absence")
    if truth.get("unobservable_is_absence") is not False:
        raise ValueError("unobservable support was converted to absence")
    ceiling = _mapping(protocol, "current_evaluation_ceiling")
    if ceiling.get("mode") != "descriptive_only_until_cluster_inference_generation":
        raise ValueError("V15b evaluation ceiling changed")
    if ceiling.get("familywise_hypothesis_tests_executed") != 0:
        raise ValueError("V15b unexpectedly enables family-wise hypothesis tests")
    gate = _mapping(protocol, "execution_gate")
    if gate.get("repository_template_is_executable") is not False:
        raise ValueError("repository freeze template became executable")
    if gate.get("committed_real_heldout_result_present") is not False:
        raise ValueError("protocol falsely reports a real V15b result")
    if canonical_json_sha256(protocol) != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("V15b gate protocol identity changed")


def validate_measurement_freeze(
    freeze: Mapping[str, Any], protocol: Mapping[str, Any]
) -> dict[str, float]:
    """Require a separately completed manifest before any held-out input use."""

    validate_v15b_protocol(protocol)
    _exact_keys(
        freeze,
        {
            "schema",
            "status",
            "protocol_canonical_sha256",
            "v14b_phase_surface_sha256",
            "development_complete",
            "heldout_data_accessed_before_freeze",
            "observer_identity",
            "analysis_identity",
            "thresholds",
            "missing_data_rule",
            "post_truth_retuning_permitted",
        },
        "measurement freeze",
    )
    if freeze.get("schema") != "insepi-v15b-heldout-measurement-freeze-v1":
        raise ValueError("wrong V15b measurement-freeze schema")
    if freeze.get("status") != "frozen-before-heldout-input":
        raise ValueError("V15b measurement freeze is not executable")
    if freeze.get("protocol_canonical_sha256") != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("measurement freeze references the wrong V15b protocol")
    if freeze.get("v14b_phase_surface_sha256") != V14B_PHASE_SURFACE_SHA256:
        raise ValueError("measurement freeze references the wrong V14b parent")
    if freeze.get("development_complete") is not True:
        raise ValueError("V15b development is not complete")
    if freeze.get("heldout_data_accessed_before_freeze") is not False:
        raise ValueError("held-out data were accessed before the measurement freeze")
    if freeze.get("post_truth_retuning_permitted") is not False:
        raise ValueError("post-truth retuning was enabled")
    missing_rule = _require_text("missing_data_rule", freeze.get("missing_data_rule"))
    if missing_rule.startswith("REPLACE"):
        raise ValueError("missing-data rule remains a template placeholder")

    observer = _mapping(freeze, "observer_identity")
    _exact_keys(
        observer,
        {
            "target_observer_commit",
            "nuisance_observer_commit",
            "coupled_route_definition_sha256",
            "support_measurement_profile_sha256",
        },
        "observer identity",
    )
    _require_commit("target_observer_commit", observer.get("target_observer_commit"))
    _require_commit(
        "nuisance_observer_commit", observer.get("nuisance_observer_commit")
    )
    _require_sha(
        "coupled_route_definition_sha256",
        observer.get("coupled_route_definition_sha256"),
    )
    _require_sha(
        "support_measurement_profile_sha256",
        observer.get("support_measurement_profile_sha256"),
    )

    analysis = _mapping(freeze, "analysis_identity")
    _exact_keys(
        analysis,
        {
            "sample_size_plan_sha256",
            "cluster_analysis_plan_sha256",
            "cluster_identity",
            "frame_is_independent_replicate",
            "claim_mode",
            "familywise_alpha",
        },
        "analysis identity",
    )
    _require_sha("sample_size_plan_sha256", analysis.get("sample_size_plan_sha256"))
    _require_sha(
        "cluster_analysis_plan_sha256",
        analysis.get("cluster_analysis_plan_sha256"),
    )
    if analysis.get("cluster_identity") != "recording_date_local_x_physical_scene_code":
        raise ValueError("V15b cluster identity changed")
    if analysis.get("frame_is_independent_replicate") is not False:
        raise ValueError("frames were enabled as independent replicates")
    if (
        analysis.get("claim_mode")
        != "descriptive_only_until_cluster_inference_generation"
    ):
        raise ValueError("V15b claim mode exceeds the implemented analysis")
    if analysis.get("familywise_alpha") != FAMILYWISE_ALPHA:
        raise ValueError("measurement-freeze family-wise alpha changed")

    raw_thresholds = _mapping(freeze, "thresholds")
    _exact_keys(
        raw_thresholds,
        {
            "target_high",
            "target_low",
            "nuisance_high",
            "support_observable",
            "support_unobservable",
        },
        "thresholds",
    )
    thresholds = {name: _number(name, value) for name, value in raw_thresholds.items()}
    VisitSystemThresholds(
        target_high=thresholds["target_high"],
        target_low=thresholds["target_low"],
        nuisance_high=thresholds["nuisance_high"],
    )
    PrimaryStreamSupportEstimator(
        observable_threshold=thresholds["support_observable"],
        unobservable_threshold=thresholds["support_unobservable"],
    )
    return thresholds


def validate_truth_seal_receipt(
    receipt: Mapping[str, Any], *, measurement_freeze_sha256: str
) -> None:
    _exact_keys(
        receipt,
        {
            "schema",
            "status",
            "truth_bundle_file_sha256",
            "truth_window_count",
            "measurement_freeze_canonical_sha256",
            "prediction_stage_truth_content_read",
        },
        "truth seal receipt",
    )
    if receipt.get("schema") != "insepi-v15b-layered-truth-seal-receipt-v1":
        raise ValueError("wrong V15b truth-seal receipt schema")
    if receipt.get("status") != "sealed-before-blinded-prediction":
        raise ValueError("V15b truth bundle was not sealed before prediction")
    _require_sha("truth_bundle_file_sha256", receipt.get("truth_bundle_file_sha256"))
    count = receipt.get("truth_window_count")
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("truth_window_count must be a positive integer")
    if receipt.get("measurement_freeze_canonical_sha256") != measurement_freeze_sha256:
        raise ValueError("truth seal references the wrong measurement freeze")
    if receipt.get("prediction_stage_truth_content_read") is not False:
        raise ValueError("truth seal reports prediction-stage truth access")


def _component_measurement(
    name: str, value: Mapping[str, Any]
) -> SupportComponentMeasurement:
    _exact_keys(value, {"score", "provenance", "method"}, f"support component {name}")
    return SupportComponentMeasurement(
        score=_number(f"{name}.score", value.get("score")),
        provenance=SupportMeasurementProvenance(value.get("provenance")),
        method=_require_text(f"{name}.method", value.get("method")),
    )


def _prepare_component_windows(
    component_ledger: Mapping[str, Any],
    *,
    measurement_freeze_sha256: str,
    thresholds: Mapping[str, float],
) -> tuple[_PreparedWindow, ...]:
    _exact_keys(
        component_ledger,
        {
            "schema",
            "status",
            "split",
            "measurement_freeze_canonical_sha256",
            "truth_fields_present",
            "rows",
        },
        "component ledger",
    )
    if component_ledger.get("schema") != "insepi-v15b-truth-free-component-ledger-v1":
        raise ValueError("wrong V15b component-ledger schema")
    if component_ledger.get("status") != "heldout-components-before-truth-join":
        raise ValueError("V15b component ledger status changed")
    if component_ledger.get("split") != "heldout":
        raise ValueError("V15b component ledger must contain held-out rows only")
    if (
        component_ledger.get("measurement_freeze_canonical_sha256")
        != measurement_freeze_sha256
    ):
        raise ValueError("component ledger references the wrong measurement freeze")
    if component_ledger.get("truth_fields_present") is not False:
        raise ValueError("component ledger reports truth fields")

    estimator = PrimaryStreamSupportEstimator(
        observable_threshold=thresholds["support_observable"],
        unobservable_threshold=thresholds["support_unobservable"],
    )
    expected_row_keys = {
        "window_id",
        "block_id",
        "recording_date_local",
        "physical_scene_code",
        "opportunity_seconds",
        "primary_clip_sha256",
        "direct_insect_score",
        "coupled_response_score",
        "target_link_confidence",
        "target_source_state",
        "nuisance_false_event_risk",
        "nuisance_missed_event_risk",
        "nuisance_attribution_risk",
        "nuisance_dominant_source",
        "support_measurements",
        "protected_random_audit",
    }
    prepared: list[_PreparedWindow] = []
    for index, row in enumerate(_rows(component_ledger, "rows")):
        _exact_keys(row, expected_row_keys, f"component row {index}")
        window_id = _require_text("window_id", row.get("window_id"))
        support_values = _mapping(row, "support_measurements")
        _exact_keys(support_values, set(SUPPORT_COMPONENTS), "support measurements")
        measurements = PrimaryStreamSupportMeasurements(
            **{
                name: _component_measurement(name, _mapping(support_values, name))
                for name in SUPPORT_COMPONENTS
            }
        )
        support = estimator.estimate(measurements)
        target = TargetRouteEvidence(
            direct_insect_score=_number(
                "direct_insect_score", row.get("direct_insect_score")
            ),
            coupled_response_score=_number(
                "coupled_response_score", row.get("coupled_response_score")
            ),
            target_link_confidence=_number(
                "target_link_confidence", row.get("target_link_confidence")
            ),
            source_state=_nullable_text(
                "target_source_state", row.get("target_source_state")
            ),
        )
        nuisance = NuisanceEvidence(
            false_event_risk=_number(
                "nuisance_false_event_risk", row.get("nuisance_false_event_risk")
            ),
            missed_event_risk=_number(
                "nuisance_missed_event_risk", row.get("nuisance_missed_event_risk")
            ),
            attribution_risk=_number(
                "nuisance_attribution_risk", row.get("nuisance_attribution_risk")
            ),
            dominant_source=_nullable_text(
                "nuisance_dominant_source", row.get("nuisance_dominant_source")
            ),
        )
        protected_random_audit = _require_bool(
            "protected_random_audit", row.get("protected_random_audit")
        )
        prepared.append(
            _PreparedWindow(
                window_id=window_id,
                block_id=_require_text("block_id", row.get("block_id")),
                recording_date_local=_require_text(
                    "recording_date_local", row.get("recording_date_local")
                ),
                physical_scene_code=_require_text(
                    "physical_scene_code", row.get("physical_scene_code")
                ),
                opportunity_seconds=_number(
                    "opportunity_seconds", row.get("opportunity_seconds"), positive=True
                ),
                primary_clip_sha256=_require_sha(
                    "primary_clip_sha256", row.get("primary_clip_sha256")
                ),
                inputs=VisitSystemInputs(
                    window_id=window_id,
                    target_routes=target,
                    nuisance=nuisance,
                    support=support,
                    protected_random_audit=protected_random_audit,
                ),
            )
        )
    ids = [row.window_id for row in prepared]
    if len(ids) != len(set(ids)):
        raise ValueError("component-ledger window_id values must be unique")
    return tuple(sorted(prepared, key=lambda row: row.window_id))


def _serialize_prediction(prediction: VisitPredictionRecord) -> dict[str, Any]:
    return asdict(prediction)


def build_blinded_prediction_ledger(
    *,
    protocol: Mapping[str, Any],
    measurement_freeze: Mapping[str, Any],
    component_ledger: Mapping[str, Any],
    component_ledger_file_sha256: str,
    truth_seal_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    """Emit all V15b system predictions without accepting truth contents."""

    thresholds = validate_measurement_freeze(measurement_freeze, protocol)
    freeze_sha = canonical_json_sha256(measurement_freeze)
    validate_truth_seal_receipt(
        truth_seal_receipt, measurement_freeze_sha256=freeze_sha
    )
    component_file_sha = _require_sha(
        "component_ledger_file_sha256", component_ledger_file_sha256
    )
    windows = _prepare_component_windows(
        component_ledger,
        measurement_freeze_sha256=freeze_sha,
        thresholds=thresholds,
    )
    if len(windows) != truth_seal_receipt.get("truth_window_count"):
        raise ValueError("component ledger and sealed truth window counts differ")

    system_thresholds = VisitSystemThresholds(
        target_high=thresholds["target_high"],
        target_low=thresholds["target_low"],
        nuisance_high=thresholds["nuisance_high"],
    )
    prediction_rows: list[dict[str, Any]] = []
    for window in windows:
        predictions = predict_all_visit_variants(
            window.inputs, thresholds=system_thresholds
        )
        prediction_rows.append(
            {
                "window_id": window.window_id,
                "block_id": window.block_id,
                "recording_date_local": window.recording_date_local,
                "physical_scene_code": window.physical_scene_code,
                "opportunity_seconds": window.opportunity_seconds,
                "primary_clip_sha256": window.primary_clip_sha256,
                "predictions": {
                    variant.value: _serialize_prediction(predictions[variant])
                    for variant in VisitSystemVariant
                },
            }
        )
    rows_digest = canonical_json_sha256({"rows": prediction_rows})
    return {
        "schema": "insepi-v15b-blinded-prediction-ledger-v1",
        "status": "predictions-emitted-before-truth-unseal",
        "heldout_truth_read": False,
        "protocol_canonical_sha256": PROTOCOL_CANONICAL_SHA256,
        "measurement_freeze_canonical_sha256": freeze_sha,
        "component_ledger_file_sha256": component_file_sha,
        "component_ledger_canonical_sha256": canonical_json_sha256(component_ledger),
        "truth_seal_receipt_canonical_sha256": canonical_json_sha256(
            truth_seal_receipt
        ),
        "sealed_truth_bundle_file_sha256": truth_seal_receipt[
            "truth_bundle_file_sha256"
        ],
        "window_count": len(prediction_rows),
        "system_variants": list(SYSTEM_VARIANTS),
        "prediction_rows_canonical_sha256": rows_digest,
        "predictions": prediction_rows,
    }


_PREDICTION_FIELDS = {
    "window_id",
    "retain_candidate",
    "positive_evidence",
    "negative_evidence",
    "censored",
    "audit_priority",
    "protected_random_audit",
    "target_score",
    "nuisance_burden",
    "direct_target_score",
    "coupled_target_score",
}


def _deserialize_prediction(value: Mapping[str, Any]) -> VisitPredictionRecord:
    _exact_keys(value, _PREDICTION_FIELDS, "prediction")
    for name in (
        "retain_candidate",
        "positive_evidence",
        "negative_evidence",
        "censored",
        "audit_priority",
        "protected_random_audit",
    ):
        _require_bool(name, value.get(name))
    return VisitPredictionRecord(**dict(value))


def validate_blinded_prediction_ledger(ledger: Mapping[str, Any]) -> None:
    _exact_keys(
        ledger,
        {
            "schema",
            "status",
            "heldout_truth_read",
            "protocol_canonical_sha256",
            "measurement_freeze_canonical_sha256",
            "component_ledger_file_sha256",
            "component_ledger_canonical_sha256",
            "truth_seal_receipt_canonical_sha256",
            "sealed_truth_bundle_file_sha256",
            "window_count",
            "system_variants",
            "prediction_rows_canonical_sha256",
            "predictions",
        },
        "prediction ledger",
    )
    if ledger.get("schema") != "insepi-v15b-blinded-prediction-ledger-v1":
        raise ValueError("wrong V15b prediction-ledger schema")
    if ledger.get("status") != "predictions-emitted-before-truth-unseal":
        raise ValueError("V15b prediction-ledger status changed")
    if ledger.get("heldout_truth_read") is not False:
        raise ValueError("V15b prediction ledger reports held-out truth access")
    if ledger.get("protocol_canonical_sha256") != PROTOCOL_CANONICAL_SHA256:
        raise ValueError("V15b prediction ledger references the wrong protocol")
    _require_sha(
        "measurement_freeze_canonical_sha256",
        ledger.get("measurement_freeze_canonical_sha256"),
    )
    _require_sha(
        "component_ledger_file_sha256", ledger.get("component_ledger_file_sha256")
    )
    _require_sha(
        "component_ledger_canonical_sha256",
        ledger.get("component_ledger_canonical_sha256"),
    )
    _require_sha(
        "truth_seal_receipt_canonical_sha256",
        ledger.get("truth_seal_receipt_canonical_sha256"),
    )
    _require_sha(
        "sealed_truth_bundle_file_sha256",
        ledger.get("sealed_truth_bundle_file_sha256"),
    )
    if list(ledger.get("system_variants", [])) != list(SYSTEM_VARIANTS):
        raise ValueError("V15b prediction-ledger system variants changed")
    rows = _rows(ledger, "predictions")
    if ledger.get("window_count") != len(rows):
        raise ValueError("V15b prediction-ledger window count changed")
    expected_row_keys = {
        "window_id",
        "block_id",
        "recording_date_local",
        "physical_scene_code",
        "opportunity_seconds",
        "primary_clip_sha256",
        "predictions",
    }
    ids: list[str] = []
    for row in rows:
        _exact_keys(row, expected_row_keys, "prediction row")
        window_id = _require_text("window_id", row.get("window_id"))
        ids.append(window_id)
        _require_text("block_id", row.get("block_id"))
        _require_text("recording_date_local", row.get("recording_date_local"))
        _require_text("physical_scene_code", row.get("physical_scene_code"))
        _number("opportunity_seconds", row.get("opportunity_seconds"), positive=True)
        _require_sha("primary_clip_sha256", row.get("primary_clip_sha256"))
        predictions = _mapping(row, "predictions")
        _exact_keys(predictions, set(SYSTEM_VARIANTS), "system predictions")
        for variant in SYSTEM_VARIANTS:
            prediction = _deserialize_prediction(_mapping(predictions, variant))
            if prediction.window_id != window_id:
                raise ValueError("nested prediction window_id changed")
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ValueError("V15b prediction rows must have unique sorted window IDs")
    expected_digest = canonical_json_sha256({"rows": list(rows)})
    if ledger.get("prediction_rows_canonical_sha256") != expected_digest:
        raise ValueError("V15b prediction-row content/hash mismatch")


def build_prediction_commitment(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Bind exact blinded predictions and the pre-existing truth seal."""

    validate_blinded_prediction_ledger(ledger)
    return {
        "schema": "insepi-v15b-prediction-commitment-v1",
        "status": "preserve-before-heldout-truth-unseal",
        "prediction_ledger_canonical_sha256": canonical_json_sha256(ledger),
        "prediction_rows_canonical_sha256": ledger["prediction_rows_canonical_sha256"],
        "measurement_freeze_canonical_sha256": ledger[
            "measurement_freeze_canonical_sha256"
        ],
        "sealed_truth_bundle_file_sha256": ledger["sealed_truth_bundle_file_sha256"],
        "window_count": ledger["window_count"],
        "heldout_truth_read": False,
    }


def validate_prediction_commitment(
    ledger: Mapping[str, Any], commitment: Mapping[str, Any]
) -> None:
    validate_blinded_prediction_ledger(ledger)
    _exact_keys(
        commitment,
        {
            "schema",
            "status",
            "prediction_ledger_canonical_sha256",
            "prediction_rows_canonical_sha256",
            "measurement_freeze_canonical_sha256",
            "sealed_truth_bundle_file_sha256",
            "window_count",
            "heldout_truth_read",
        },
        "prediction commitment",
    )
    if commitment.get("schema") != "insepi-v15b-prediction-commitment-v1":
        raise ValueError("wrong V15b prediction-commitment schema")
    if commitment.get("status") != "preserve-before-heldout-truth-unseal":
        raise ValueError("V15b prediction commitment status changed")
    if commitment.get("heldout_truth_read") is not False:
        raise ValueError("V15b prediction commitment reports held-out truth access")
    expected = build_prediction_commitment(ledger)
    if dict(commitment) != expected:
        raise ValueError("V15b prediction ledger differs from its commitment")


def _truth_rows_by_id(
    bundle: Mapping[str, Any], name: str, expected_keys: set[str]
) -> dict[str, Mapping[str, Any]]:
    output: dict[str, Mapping[str, Any]] = {}
    for row in _rows(bundle, name):
        _exact_keys(row, expected_keys, name)
        window_id = _require_text("window_id", row.get("window_id"))
        if window_id in output:
            raise ValueError(f"duplicate {name} window_id: {window_id}")
        output[window_id] = row
    return output


def _parse_layered_truth(
    *,
    truth_bundle: Mapping[str, Any],
    ledger: Mapping[str, Any],
    measurement_freeze_sha256: str,
) -> list[VisitTruthRecord]:
    _exact_keys(
        truth_bundle,
        {
            "schema",
            "status",
            "measurement_freeze_canonical_sha256",
            "prediction_outputs_hidden_during_annotation",
            "layer_adjudication_complete",
            "automatic_cross_layer_conflict_resolution",
            "biological_truth_rows",
            "coupling_truth_rows",
            "nuisance_truth_rows",
            "support_truth_rows",
        },
        "layered truth bundle",
    )
    if truth_bundle.get("schema") != "insepi-v15b-layered-truth-bundle-v1":
        raise ValueError("wrong V15b layered-truth schema")
    if truth_bundle.get("status") != "sealed-heldout-layered-truth":
        raise ValueError("V15b layered truth is not sealed")
    if (
        truth_bundle.get("measurement_freeze_canonical_sha256")
        != measurement_freeze_sha256
    ):
        raise ValueError("layered truth references the wrong measurement freeze")
    if truth_bundle.get("prediction_outputs_hidden_during_annotation") is not True:
        raise ValueError("prediction outputs were not hidden during truth annotation")
    if truth_bundle.get("layer_adjudication_complete") is not True:
        raise ValueError("truth-layer adjudication is incomplete")
    if truth_bundle.get("automatic_cross_layer_conflict_resolution") is not False:
        raise ValueError("truth bundle reports automatic conflict resolution")

    biological_rows = _truth_rows_by_id(
        truth_bundle,
        "biological_truth_rows",
        {
            "window_id",
            "block_id",
            "reference_clip_sha256",
            "annotator_id",
            "resolution",
            "state",
            "event_id",
        },
    )
    coupling_rows = _truth_rows_by_id(
        truth_bundle,
        "coupling_truth_rows",
        {
            "window_id",
            "reference_clip_sha256",
            "annotator_id",
            "resolution",
            "present",
        },
    )
    nuisance_rows = _truth_rows_by_id(
        truth_bundle,
        "nuisance_truth_rows",
        {"window_id", "primary_clip_sha256", "annotator_id", "effects"},
    )
    support_rows = _truth_rows_by_id(
        truth_bundle,
        "support_truth_rows",
        {
            "window_id",
            "primary_clip_sha256",
            "annotator_id",
            "components",
            "annotation_method",
            "notes",
        },
    )
    prediction_rows = {
        str(row["window_id"]): row for row in _rows(ledger, "predictions")
    }
    window_sets = (
        set(biological_rows),
        set(coupling_rows),
        set(nuisance_rows),
        set(support_rows),
        set(prediction_rows),
    )
    if any(ids != window_sets[0] for ids in window_sets[1:]):
        raise ValueError("prediction and four truth-layer window sets differ")

    output: list[VisitTruthRecord] = []
    for window_id in sorted(prediction_rows):
        biological_row = biological_rows[window_id]
        coupling_row = coupling_rows[window_id]
        nuisance_row = nuisance_rows[window_id]
        support_row = support_rows[window_id]
        prediction_row = prediction_rows[window_id]

        biological_resolution = VisitTruthResolution(biological_row["resolution"])
        biological_state = (
            None
            if biological_row["state"] is None
            else VisitTruthState(biological_row["state"])
        )
        biological = BiologicalTruthAnnotation(
            window_id=window_id,
            block_id=_require_text("block_id", biological_row["block_id"]),
            reference_clip_sha256=_require_sha(
                "reference_clip_sha256", biological_row["reference_clip_sha256"]
            ),
            annotator_id=_require_text("annotator_id", biological_row["annotator_id"]),
            resolution=biological_resolution,
            state=biological_state,
            event_id=_nullable_text("event_id", biological_row["event_id"]),
        )
        coupling_present = coupling_row["present"]
        if coupling_present is not None:
            coupling_present = _require_bool("coupling present", coupling_present)
        coupling = CouplingTruthAnnotation(
            window_id=window_id,
            reference_clip_sha256=_require_sha(
                "reference_clip_sha256", coupling_row["reference_clip_sha256"]
            ),
            annotator_id=_require_text("annotator_id", coupling_row["annotator_id"]),
            resolution=CoupledResponseResolution(coupling_row["resolution"]),
            present=coupling_present,
        )
        effects_value = nuisance_row["effects"]
        if not isinstance(effects_value, Sequence) or isinstance(
            effects_value, (str, bytes)
        ):
            raise TypeError("nuisance effects must be an array")
        nuisance = NuisanceTruthAnnotation(
            window_id=window_id,
            primary_clip_sha256=_require_sha(
                "primary_clip_sha256", nuisance_row["primary_clip_sha256"]
            ),
            annotator_id=_require_text("annotator_id", nuisance_row["annotator_id"]),
            effects=tuple(NuisanceEffect(value) for value in effects_value),
        )
        components = _mapping(support_row, "components")
        _exact_keys(components, set(SUPPORT_COMPONENTS), "support truth components")
        support_truth = PrimaryStreamSupportTruth(
            **{
                name: SupportComponentState(components[name])
                for name in SUPPORT_COMPONENTS
            },
            annotation_method=_require_text(
                "annotation_method", support_row["annotation_method"]
            ),
            notes=_string("support truth notes", support_row["notes"]),
        )
        support = SupportTruthAnnotation(
            window_id=window_id,
            primary_clip_sha256=_require_sha(
                "primary_clip_sha256", support_row["primary_clip_sha256"]
            ),
            annotator_id=_require_text("annotator_id", support_row["annotator_id"]),
            truth=support_truth,
        )
        if biological.block_id != prediction_row["block_id"]:
            raise ValueError(
                "truth block_id differs from committed prediction metadata"
            )
        if nuisance.primary_clip_sha256 != prediction_row["primary_clip_sha256"]:
            raise ValueError(
                "truth primary clip differs from committed prediction metadata"
            )
        output.append(
            join_layered_truth(biological, coupling, nuisance, support).visit_truth
        )
    return output


def evaluate_committed_predictions(
    *,
    protocol: Mapping[str, Any],
    measurement_freeze: Mapping[str, Any],
    prediction_ledger: Mapping[str, Any],
    prediction_commitment: Mapping[str, Any],
    truth_seal_receipt: Mapping[str, Any],
    truth_bundle: Mapping[str, Any],
    truth_bundle_file_sha256: str,
) -> dict[str, Any]:
    """Join truth only after prediction identity has been validated."""

    thresholds = validate_measurement_freeze(measurement_freeze, protocol)
    freeze_sha = canonical_json_sha256(measurement_freeze)
    validate_prediction_commitment(prediction_ledger, prediction_commitment)
    validate_truth_seal_receipt(
        truth_seal_receipt, measurement_freeze_sha256=freeze_sha
    )
    truth_file_sha = _require_sha("truth_bundle_file_sha256", truth_bundle_file_sha256)
    if truth_file_sha != truth_seal_receipt.get("truth_bundle_file_sha256"):
        raise ValueError("held-out truth bundle differs from its pre-prediction seal")
    if truth_file_sha != prediction_commitment.get("sealed_truth_bundle_file_sha256"):
        raise ValueError("held-out truth bundle differs from the prediction commitment")

    truth = _parse_layered_truth(
        truth_bundle=truth_bundle,
        ledger=prediction_ledger,
        measurement_freeze_sha256=freeze_sha,
    )
    if len(truth) != truth_seal_receipt.get("truth_window_count"):
        raise ValueError("opened truth count differs from the seal receipt")

    prediction_rows = _rows(prediction_ledger, "predictions")
    summaries: dict[str, Any] = {}
    for variant in SYSTEM_VARIANTS:
        predictions = [
            _deserialize_prediction(_mapping(_mapping(row, "predictions"), variant))
            for row in prediction_rows
        ]
        summary = evaluate_visit_predictions(
            truth,
            predictions,
            target_low_threshold=thresholds["target_low"],
            target_high_threshold=thresholds["target_high"],
            nuisance_low_threshold=thresholds["nuisance_high"],
        )
        summaries[variant] = asdict(summary)

    cluster_counts = Counter(
        (str(row["recording_date_local"]), str(row["physical_scene_code"]))
        for row in prediction_rows
    )
    cluster_inventory = [
        {
            "recording_date_local": date,
            "physical_scene_code": scene,
            "window_count": count,
        }
        for (date, scene), count in sorted(cluster_counts.items())
    ]
    measurement_payload = {
        "window_count": len(prediction_rows),
        "block_count": len({str(row["block_id"]) for row in prediction_rows}),
        "actual_day_x_scene_cluster_count": len(cluster_inventory),
        "cluster_inventory": cluster_inventory,
        "total_opportunity_seconds": sum(
            float(row["opportunity_seconds"]) for row in prediction_rows
        ),
        "system_summaries": summaries,
        "familywise_alpha_retained": FAMILYWISE_ALPHA,
        "familywise_hypothesis_tests_executed": 0,
        "cluster_level_inference_executed": False,
    }
    return {
        "schema": "insepi-v15b-descriptive-heldout-evaluation-v1",
        "status": "descriptive-only-no-cluster-inference",
        "provenance": {
            "protocol_canonical_sha256": PROTOCOL_CANONICAL_SHA256,
            "measurement_freeze_canonical_sha256": freeze_sha,
            "prediction_ledger_canonical_sha256": canonical_json_sha256(
                prediction_ledger
            ),
            "prediction_commitment_canonical_sha256": canonical_json_sha256(
                prediction_commitment
            ),
            "truth_seal_receipt_canonical_sha256": canonical_json_sha256(
                truth_seal_receipt
            ),
            "truth_bundle_file_sha256": truth_file_sha,
            "truth_join_stage": "after blinded prediction ledger commitment",
            "post_truth_retuning_permitted": False,
        },
        "measurement": measurement_payload,
        "measurement_payload_canonical_sha256": canonical_json_sha256(
            measurement_payload
        ),
        "claim": {
            "level": "descriptive_only",
            "familywise_decision": None,
            "field_performance_claim": False,
            "reason": (
                "V15b implements the no-peek join and fixed window metrics but "
                "does not yet implement the separately frozen cluster-level "
                "family-wise inferential generation"
            ),
        },
    }
