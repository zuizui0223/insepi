from __future__ import annotations

import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from interaction_sensing.heldout_measurement_v15b import (
    PROTOCOL_CANONICAL_SHA256,
    SYSTEM_VARIANTS,
    build_blinded_prediction_ledger,
    build_prediction_commitment,
    evaluate_committed_predictions,
    validate_measurement_freeze,
    validate_prediction_commitment,
    validate_v15b_protocol,
)
from interaction_sensing.prefield_programming_closeout import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "benchmarks/v15b_heldout_measurement_gate_protocol.json"
TEMPLATE_PATH = ROOT / "benchmarks/v15b_heldout_measurement_freeze_TEMPLATE.json"
PREDICT_SCRIPT = ROOT / "scripts/v15b_predict_and_commit.py"
EVALUATE_SCRIPT = ROOT / "scripts/v15b_evaluate_locked.py"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def protocol() -> dict[str, object]:
    return _read(PROTOCOL_PATH)


def freeze() -> dict[str, object]:
    return {
        "schema": "insepi-v15b-heldout-measurement-freeze-v1",
        "status": "frozen-before-heldout-input",
        "protocol_canonical_sha256": PROTOCOL_CANONICAL_SHA256,
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
            "cluster_analysis_plan_sha256": "6" * 64,
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
        "missing_data_rule": "fail closed; retain missing support as unresolved",
        "post_truth_retuning_permitted": False,
    }


def _support_measurements(score: float) -> dict[str, object]:
    return {
        component: {
            "score": score,
            "provenance": "other_primary_stream_measurement",
            "method": "synthetic gate fixture; not field data",
        }
        for component in (
            "target_zone_coverage",
            "target_zone_visibility",
            "spatial_resolution",
            "photometric_sufficiency",
            "temporal_continuity",
        )
    }


def _component_row(
    window_id: str,
    *,
    block_id: str,
    direct: float,
    nuisance: float,
    support: float,
    primary_sha: str,
    date: str,
    scene: str,
) -> dict[str, object]:
    return {
        "window_id": window_id,
        "block_id": block_id,
        "recording_date_local": date,
        "physical_scene_code": scene,
        "opportunity_seconds": 10.0,
        "primary_clip_sha256": primary_sha,
        "direct_insect_score": direct,
        "coupled_response_score": 0.05,
        "target_link_confidence": 0.10,
        "target_source_state": "synthetic_fixture",
        "nuisance_false_event_risk": nuisance,
        "nuisance_missed_event_risk": nuisance,
        "nuisance_attribution_risk": nuisance,
        "nuisance_dominant_source": "synthetic_fixture",
        "support_measurements": _support_measurements(support),
        "protected_random_audit": window_id == "hidden-visit",
    }


def component_ledger(measurement_freeze: dict[str, object]) -> dict[str, object]:
    return {
        "schema": "insepi-v15b-truth-free-component-ledger-v1",
        "status": "heldout-components-before-truth-join",
        "split": "heldout",
        "measurement_freeze_canonical_sha256": canonical_json_sha256(
            measurement_freeze
        ),
        "truth_fields_present": False,
        "rows": [
            _component_row(
                "hidden-visit",
                block_id="b1",
                direct=0.05,
                nuisance=0.05,
                support=0.10,
                primary_sha="a" * 64,
                date="2026-09-10",
                scene="scene-a",
            ),
            _component_row(
                "quiet-absence",
                block_id="b2",
                direct=0.05,
                nuisance=0.05,
                support=0.90,
                primary_sha="b" * 64,
                date="2026-09-10",
                scene="scene-a",
            ),
            _component_row(
                "superposed-visit",
                block_id="b3",
                direct=0.90,
                nuisance=0.90,
                support=0.90,
                primary_sha="c" * 64,
                date="2026-09-11",
                scene="scene-b",
            ),
        ],
    }


def _support_truth(failed: bool) -> dict[str, str]:
    values = {
        component: "adequate"
        for component in (
            "target_zone_coverage",
            "target_zone_visibility",
            "spatial_resolution",
            "photometric_sufficiency",
            "temporal_continuity",
        )
    }
    if failed:
        values["target_zone_visibility"] = "failed"
    return values


def truth_bundle(measurement_freeze: dict[str, object]) -> dict[str, object]:
    biological_specs = (
        ("hidden-visit", "b1", "visit_event", "event-hidden"),
        ("quiet-absence", "b2", "no_insect", None),
        ("superposed-visit", "b3", "visit_event", "event-superposed"),
    )
    primary_shas = {
        "hidden-visit": "a" * 64,
        "quiet-absence": "b" * 64,
        "superposed-visit": "c" * 64,
    }
    return {
        "schema": "insepi-v15b-layered-truth-bundle-v1",
        "status": "sealed-heldout-layered-truth",
        "measurement_freeze_canonical_sha256": canonical_json_sha256(
            measurement_freeze
        ),
        "prediction_outputs_hidden_during_annotation": True,
        "layer_adjudication_complete": True,
        "automatic_cross_layer_conflict_resolution": False,
        "biological_truth_rows": [
            {
                "window_id": window_id,
                "block_id": block_id,
                "reference_clip_sha256": "d" * 64,
                "annotator_id": "bio-a",
                "resolution": "resolved",
                "state": state,
                "event_id": event_id,
            }
            for window_id, block_id, state, event_id in biological_specs
        ],
        "coupling_truth_rows": [
            {
                "window_id": window_id,
                "reference_clip_sha256": "d" * 64,
                "annotator_id": "coupling-a",
                "resolution": "resolved",
                "present": False,
            }
            for window_id, *_ in biological_specs
        ],
        "nuisance_truth_rows": [
            {
                "window_id": window_id,
                "primary_clip_sha256": primary_shas[window_id],
                "annotator_id": "nuisance-a",
                "effects": (["mask_target"] if window_id == "superposed-visit" else []),
            }
            for window_id, *_ in biological_specs
        ],
        "support_truth_rows": [
            {
                "window_id": window_id,
                "primary_clip_sha256": primary_shas[window_id],
                "annotator_id": "support-a",
                "components": _support_truth(window_id == "hidden-visit"),
                "annotation_method": "separate blinded synthetic fixture",
                "notes": "not field data",
            }
            for window_id, *_ in biological_specs
        ],
    }


def truth_seal(
    measurement_freeze: dict[str, object], truth_file_sha256: str
) -> dict[str, object]:
    return {
        "schema": "insepi-v15b-layered-truth-seal-receipt-v1",
        "status": "sealed-before-blinded-prediction",
        "truth_bundle_file_sha256": truth_file_sha256,
        "truth_window_count": 3,
        "measurement_freeze_canonical_sha256": canonical_json_sha256(
            measurement_freeze
        ),
        "prediction_stage_truth_content_read": False,
    }


def _prediction_chain(
    truth_file_sha256: str = "e" * 64,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    measurement_freeze = freeze()
    ledger = build_blinded_prediction_ledger(
        protocol=protocol(),
        measurement_freeze=measurement_freeze,
        component_ledger=component_ledger(measurement_freeze),
        component_ledger_file_sha256="f" * 64,
        truth_seal_receipt=truth_seal(measurement_freeze, truth_file_sha256),
    )
    return measurement_freeze, ledger, build_prediction_commitment(ledger)


def _write(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_is_fixed_but_repository_template_cannot_execute() -> None:
    validate_v15b_protocol(protocol())
    assert canonical_json_sha256(protocol()) == PROTOCOL_CANONICAL_SHA256
    with pytest.raises(ValueError, match="not executable"):
        validate_measurement_freeze(_read(TEMPLATE_PATH), protocol())


def test_prediction_stage_emits_every_variant_without_truth_fields() -> None:
    _, ledger, commitment = _prediction_chain()

    assert ledger["heldout_truth_read"] is False
    assert ledger["window_count"] == 3
    assert ledger["system_variants"] == list(SYSTEM_VARIANTS)
    serialized = json.dumps(ledger, sort_keys=True)
    assert "biological_state" not in serialized
    assert "support_truth" not in serialized
    assert commitment["heldout_truth_read"] is False
    validate_prediction_commitment(ledger, commitment)

    superposed = next(
        row for row in ledger["predictions"] if row["window_id"] == "superposed-visit"
    )
    full = superposed["predictions"][
        "full_direct_coupled_target_nuisance_observability_triad"
    ]
    assert full["positive_evidence"] is True
    assert full["audit_priority"] is True


def test_prediction_or_commitment_tamper_fails_before_truth_join() -> None:
    _, ledger, commitment = _prediction_chain()
    tampered = deepcopy(ledger)
    tampered["predictions"][0]["predictions"]["direct_target_only_naive"][
        "negative_evidence"
    ] = False
    with pytest.raises(ValueError, match="content/hash mismatch"):
        validate_prediction_commitment(tampered, commitment)

    bad_commitment = deepcopy(commitment)
    bad_commitment["window_count"] = 4
    with pytest.raises(ValueError, match="differs from its commitment"):
        validate_prediction_commitment(ledger, bad_commitment)


def test_locked_truth_join_is_descriptive_and_preserves_censoring() -> None:
    bundle = truth_bundle(freeze())
    truth_file_sha = "9" * 64
    measurement_freeze, ledger, commitment = _prediction_chain(truth_file_sha)
    result = evaluate_committed_predictions(
        protocol=protocol(),
        measurement_freeze=measurement_freeze,
        prediction_ledger=ledger,
        prediction_commitment=commitment,
        truth_seal_receipt=truth_seal(measurement_freeze, truth_file_sha),
        truth_bundle=bundle,
        truth_bundle_file_sha256=truth_file_sha,
    )

    assert result["status"] == "descriptive-only-no-cluster-inference"
    assert result["claim"]["familywise_decision"] is None
    assert result["claim"]["field_performance_claim"] is False
    assert result["measurement"]["familywise_hypothesis_tests_executed"] == 0
    assert result["measurement"]["actual_day_x_scene_cluster_count"] == 2
    summaries = result["measurement"]["system_summaries"]
    assert summaries["direct_target_only_naive"]["false_absence_count"] == 1
    assert summaries["target_plus_support_without_nuisance"]["false_absence_count"] == 0
    assert (
        summaries["full_direct_coupled_target_nuisance_observability_triad"][
            "unobservable_recall"
        ]
        == 1.0
    )


def test_truth_bundle_must_match_both_seal_and_prediction_commitment() -> None:
    measurement_freeze, ledger, commitment = _prediction_chain("8" * 64)
    with pytest.raises(ValueError, match="pre-prediction seal"):
        evaluate_committed_predictions(
            protocol=protocol(),
            measurement_freeze=measurement_freeze,
            prediction_ledger=ledger,
            prediction_commitment=commitment,
            truth_seal_receipt=truth_seal(measurement_freeze, "8" * 64),
            truth_bundle=truth_bundle(measurement_freeze),
            truth_bundle_file_sha256="7" * 64,
        )


def test_cli_prediction_commitment_then_locked_evaluation(tmp_path: Path) -> None:
    measurement_freeze = freeze()
    freeze_path = tmp_path / "freeze.json"
    components_path = tmp_path / "components.json"
    truth_path = tmp_path / "truth.json"
    seal_path = tmp_path / "truth-seal.json"
    prediction_path = tmp_path / "predictions.json"
    commitment_path = tmp_path / "commitment.json"
    result_path = tmp_path / "result.json"
    _write(freeze_path, measurement_freeze)
    _write(components_path, component_ledger(measurement_freeze))
    _write(truth_path, truth_bundle(measurement_freeze))
    truth_sha = hashlib.sha256(truth_path.read_bytes()).hexdigest()
    _write(seal_path, truth_seal(measurement_freeze, truth_sha))

    predictor = _load_script("v15b_predict_runner", PREDICT_SCRIPT)
    evaluator = _load_script("v15b_evaluate_runner", EVALUATE_SCRIPT)
    prediction, commitment = predictor.run(
        protocol_path=PROTOCOL_PATH,
        measurement_freeze_path=freeze_path,
        component_ledger_path=components_path,
        truth_seal_receipt_path=seal_path,
        prediction_output_path=prediction_path,
        commitment_output_path=commitment_path,
    )
    assert prediction["heldout_truth_read"] is False
    assert commitment == _read(commitment_path)

    result = evaluator.run(
        protocol_path=PROTOCOL_PATH,
        measurement_freeze_path=freeze_path,
        prediction_path=prediction_path,
        prediction_commitment_path=commitment_path,
        truth_seal_receipt_path=seal_path,
        truth_bundle_path=truth_path,
        output_path=result_path,
    )
    assert result == _read(result_path)
    assert result["provenance"]["truth_join_stage"] == (
        "after blinded prediction ledger commitment"
    )
    with pytest.raises(FileExistsError, match="overwrite"):
        evaluator.run(
            protocol_path=PROTOCOL_PATH,
            measurement_freeze_path=freeze_path,
            prediction_path=prediction_path,
            prediction_commitment_path=commitment_path,
            truth_seal_receipt_path=seal_path,
            truth_bundle_path=truth_path,
            output_path=result_path,
        )
