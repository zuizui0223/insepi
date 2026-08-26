import hashlib
import json
from pathlib import Path


REGISTRY = Path("benchmarks/v15_prefreeze_readiness_registry.json")
ABSENCE = Path("benchmarks/v15_absence_strategy_v1.json")
CLAIMS = Path("benchmarks/v15_claim_thresholds_v1_template.json")
ABSENCE_METRICS = Path("benchmarks/v15_absence_metric_freeze_v1.json")
EXPOSURE_ESTIMAND = Path("benchmarks/v15_cluster_exposure_estimand_freeze_v1.json")
TRUTH_ANNOTATION = Path("benchmarks/v15_truth_annotation_freeze_v1.json")
TARGET_ADAPTER = Path("benchmarks/v15_target_field_adapter_freeze_v1.json")
NUISANCE_ADAPTER = Path("benchmarks/v15_nuisance_field_adapter_freeze_v1.json")


def _registry_item(registry: dict, name: str) -> dict:
    return next(item for item in registry["items"] if item["name"] == name)


def test_absence_strategy_artifact_matches_registered_sha256() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    strategy = json.loads(ABSENCE.read_text(encoding="utf-8"))
    digest = hashlib.sha256(ABSENCE.read_bytes()).hexdigest()
    assert registry["absence_strategy"] == "retain_upper_bound_1_without_A_minus"
    assert registry["absence_strategy_evidence_path"] == str(ABSENCE)
    assert registry["absence_strategy_sha256"] == digest
    assert strategy["strategy"] == registry["absence_strategy"]
    assert strategy["safe_target_presence_upper_bound"] == 1.0
    assert registry["safe_target_presence_upper_bound"] == 1.0


def test_claim_template_contains_no_invented_numerical_thresholds() -> None:
    payload = json.loads(CLAIMS.read_text(encoding="utf-8"))
    slots = payload["claim_slots"]
    assert slots
    assert all(slot["threshold"] is None for slot in slots)
    assert any(slot["requires_A_minus"] for slot in slots)
    assert payload["decision_policy"]["point_estimate_alone_can_authorize_claim"] is False


def test_frozen_absence_metric_artifact_matches_registry_sha256() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    item = _registry_item(registry, "forced_vs_certified_absence_metrics")
    digest = hashlib.sha256(ABSENCE_METRICS.read_bytes()).hexdigest()
    assert item["status"] == "frozen"
    assert item["evidence_path"] == str(ABSENCE_METRICS)
    assert item["sha256"] == digest


def test_frozen_cluster_exposure_estimand_matches_registry_sha256() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    item = _registry_item(registry, "cluster_exposure_estimand")
    payload = json.loads(EXPOSURE_ESTIMAND.read_text(encoding="utf-8"))
    digest = hashlib.sha256(EXPOSURE_ESTIMAND.read_bytes()).hexdigest()
    assert item["status"] == "frozen"
    assert item["evidence_path"] == str(EXPOSURE_ESTIMAND)
    assert item["sha256"] == digest
    assert payload["primary_estimand"] == "detected visit-event rate conditional on interpretable primary-stream exposure"
    assert payload["denominator"]["censored_time"] == "excluded from the rate denominator and retained separately"


def test_four_truth_layers_share_one_frozen_annotation_artifact() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload = json.loads(TRUTH_ANNOTATION.read_text(encoding="utf-8"))
    digest = hashlib.sha256(TRUTH_ANNOTATION.read_bytes()).hexdigest()
    frozen_names = (
        "biological_truth_annotation",
        "coupling_truth_annotation",
        "nuisance_truth_annotation",
        "support_truth_annotation",
    )
    for name in frozen_names:
        item = _registry_item(registry, name)
        assert item["status"] == "frozen"
        assert item["evidence_path"] == str(TRUTH_ANNOTATION)
        assert item["sha256"] == digest
    assert payload["double_annotation"]["minimum_fraction"] == 0.2
    assert payload["ledger_join"]["automatic_cross_layer_conflict_resolution"] is False
    assert payload["support_truth_annotation"]["overall_rule"] == [
        "any failed necessary component => resolved UNOBSERVABLE",
        "else any unresolved component => overall support truth unresolved",
        "else any compromised component => resolved COMPROMISED",
        "else five adequate components => resolved OBSERVABLE",
    ]
    assert "final development/held-out block assignment" in payload["split_blinding_boundary"]["not_frozen_here"]


def test_target_field_adapter_artifact_matches_registry_and_pollipi_provenance() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload = json.loads(TARGET_ADAPTER.read_text(encoding="utf-8"))
    digest = hashlib.sha256(TARGET_ADAPTER.read_bytes()).hexdigest()
    item = _registry_item(registry, "target_field_adapter")
    assert item["status"] == "frozen"
    assert item["evidence_path"] == str(TARGET_ADAPTER)
    assert item["sha256"] == digest
    assert payload["pollipi_provenance"]["repository"] == "zuizui0223/pollipi"
    assert payload["pollipi_provenance"]["main_commit"] == "f3b266897f3e9139e6c3fe9ce6b645e25371e092"
    assert payload["pollipi_provenance"]["adapter_git_blob_sha1"] == "4be5f7c88edda1dda3b62e8a95529386d702bb47"
    assert payload["frozen_mapping"] == {
        "no_activity": 0.0,
        "environmental_noise": 0.0,
        "uncertain_local_activity": 0.5,
        "strong_visitation_candidate": 1.0,
    }


def test_nuisance_field_adapter_artifact_matches_registry_and_separates_calibration() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    payload = json.loads(NUISANCE_ADAPTER.read_text(encoding="utf-8"))
    digest = hashlib.sha256(NUISANCE_ADAPTER.read_bytes()).hexdigest()
    item = _registry_item(registry, "nuisance_field_adapter")
    assert item["status"] == "frozen"
    assert item["evidence_path"] == str(NUISANCE_ADAPTER)
    assert item["sha256"] == digest
    assert payload["measurement_code"]["git_blob_sha1"] == "1e0498e853d79c1c9b3ee0b100e190e54e65ba7b"
    assert payload["reference_manifest"]["must_be_selected_before_model_scoring"] is True
    assert payload["remaining_calibration_blocker"] == "target_nuisance_decision_calibration"
    assert "the nuisance_process_index is not a probability" in payload["hard_boundaries"]
