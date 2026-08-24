from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from interaction_sensing.simulation import v10_evaluator as v10

ROOT = Path(__file__).resolve().parents[1]


def test_v10_evaluator_constants_match_preobserver_freeze() -> None:
    freeze = json.loads((ROOT / "benchmarks/v10_evaluator_freeze.json").read_text())
    assert freeze["required_pixel_npz_sha256"] == v10.PIXEL_SHA256
    assert freeze["condition_registry_sha256"] == v10.CONDITION_REGISTRY_SHA256
    assert freeze["panel_registry_sha256"] == v10.PANEL_REGISTRY_SHA256
    assert freeze["required_observer_commits"] == {
        "pollipi": v10.POLLIPI_COMMIT,
        "insepi": v10.INSEPI_COMMIT,
    }
    assert freeze["pollipi_evidence_score"] == {
        **v10.EVIDENCE_SCORE,
        "unknown_state_rule": "fail",
    }
    assert freeze["allocation"]["budget_values"] == [value for value, _ in v10.BUDGETS]
    assert freeze["allocation"]["replicates"] == v10.REPLICATES
    assert freeze["allocation"]["selection_seed_domain"] == v10.SELECTION_SEED_DOMAIN


def test_v10_trace_result_contract_contains_no_truth_keys() -> None:
    forbidden = {
        "family", "tier", "tier_index", "known_disturbed", "intensity",
        "video_index", "temporal_quartile", "panel_id", "base_index", "variant_index",
    }
    assert not (v10.POLLIPI_RESULT_KEYS & forbidden)
    assert not (v10.INSEPI_RESULT_KEYS & forbidden)


def test_v10_pollipi_score_mapping_and_unknown_fail() -> None:
    for state, expected in v10.EVIDENCE_SCORE.items():
        assert v10.evidence_score({"pollipi_state": state}) == expected
    with pytest.raises(RuntimeError, match="unknown frozen PolliPi state"):
        v10.evidence_score({"pollipi_state": "post_result_new_state"})


def test_v10_insepi_risk_contract() -> None:
    assert v10.observability_risk({
        "false_event_risk": 0.2,
        "missed_event_risk": 0.7,
        "attribution_risk": 0.4,
    }) == 0.7
    with pytest.raises(RuntimeError, match="invalid frozen InsePi risk"):
        v10.observability_risk({
            "false_event_risk": 0.2,
            "missed_event_risk": 1.01,
            "attribution_risk": 0.4,
        })


def test_v10_selection_seed_matches_frozen_serialisation() -> None:
    panel_id = "glare:tier2"
    token = "0.25"
    replicate = 137
    raw = hashlib.sha256(
        f"{v10.SELECTION_SEED_DOMAIN}|{panel_id}|{token}|{replicate}".encode()
    ).digest()
    assert v10.selection_seed(panel_id, token, replicate) == int.from_bytes(raw[:8], "big")


def test_v10_policy_registry_is_exactly_frozen_six() -> None:
    assert v10.POLICIES == (
        "uniform",
        "guarded_v6",
        "guarded_e_only",
        "guarded_o_only",
        "guarded_fused_20_80",
        "guarded_max",
    )
    assert v10._policy("guarded_v6").exploration == 0.50
    assert v10._policy("guarded_v6").arms == (("evidence", 0.10), ("observability", 0.40))


@pytest.mark.parametrize(
    ("positive", "global_high", "monotone", "allocation_pass", "level"),
    [
        (2, 0.4, 6, True, "D"),
        (6, 0.0, 6, True, "D"),
        (5, 0.1, 4, True, "A"),
        (5, 0.1, 4, False, "B"),
        (4, 0.1, 6, True, "C"),
        (6, 0.1, 3, True, "C"),
    ],
)
def test_v10_claim_precedence_is_frozen(
    positive: int,
    global_high: float,
    monotone: int,
    allocation_pass: bool,
    level: str,
) -> None:
    observer = {
        "positive_high_tier_family_count": positive,
        "dose_monotone_family_count": monotone,
        "global_high_tier_median_risk_delta": global_high,
    }
    allocation = {"v6_allocation_pass": allocation_pass}
    actual, _label = v10._claim(observer, allocation)
    assert actual == level


def test_v10_score_rows_do_not_receive_truth() -> None:
    rows = v10._score_rows([0.0, 0.7, 1.0], [0.2, 0.4, 0.9])
    assert all(set(row) == {"evidence", "observability", "fused", "maximum"} for row in rows)


def _synthetic_v10_artifact_and_traces():
    families = ("shadow", "occlusion", "blur", "sensor_banding", "glare", "framing_drift")
    variants = [{"variant_index": 0, "family": None, "tier_index": None}]
    variant_index = 1
    for family in families:
        for tier in range(3):
            variants.append({"variant_index": variant_index, "family": family, "tier_index": tier})
            variant_index += 1

    base_registry = [
        {
            "base_index": base,
            "video_index": base % 7,
            "temporal_quartile": (base // 7) % 4,
        }
        for base in range(364)
    ]
    panel_registry = [
        {
            "panel_id": f"{family}:tier{tier}",
            "family": family,
            "tier_index": tier,
            "disturbed_base_indices": list(range(182)),
        }
        for family in families
        for tier in range(3)
    ]

    pollipi_rows = []
    insepi_rows = []
    for base in range(364):
        for variant in variants:
            tier = variant["tier_index"]
            native = variant["variant_index"] == 0
            pollipi_rows.append({
                "pollipi_state": "no_activity" if native else "environmental_noise",
            })
            risk = 0.10 if native else 0.20 + 0.20 * int(tier)
            insepi_rows.append({
                "false_event_risk": risk,
                "missed_event_risk": risk * 0.8,
                "attribution_risk": risk * 0.6,
            })
    artifact = SimpleNamespace(
        variant_registry=tuple(variants),
        base_registry=tuple(base_registry),
        panel_registry=tuple(panel_registry),
    )
    pollipi = v10.TraceData(provenance={}, rows=tuple(pollipi_rows), sha256="p" * 64)
    insepi = v10.TraceData(provenance={}, rows=tuple(insepi_rows), sha256="i" * 64)
    return artifact, pollipi, insepi


def test_v10_complete_frozen_evaluator_plumbing_on_synthetic_traces(monkeypatch) -> None:
    """Exercise all families, panels, budgets and policies without real observer results."""
    artifact, pollipi, insepi = _synthetic_v10_artifact_and_traces()
    observer = v10._observer_transfer(artifact, pollipi, insepi)
    assert observer["positive_high_tier_family_count"] == 6
    assert observer["dose_monotone_family_count"] == 6
    assert observer["global_high_tier_median_risk_delta"] > 0.0
    assert len(observer["family_tier"]) == 18

    # Two paired replicates are sufficient to test the complete wiring; the
    # scientific V10 value remains frozen at 200 and is checked separately.
    monkeypatch.setattr(v10, "REPLICATES", 2)
    allocation = v10._allocation_transfer(artifact, pollipi, insepi)
    assert allocation["v6_cell_count"] == 54
    assert len(allocation["cells"]) == 18 * 3 * 6
    assert 0 <= allocation["v6_cell_pass_count"] <= 54
    assert allocation["v6_overall_mean_paired_uniform_recall_ratio"] > 0.0
    assert {row["policy"] for row in allocation["cells"]} == set(v10.POLICIES)


def _load_v10_evaluation_script():
    path = ROOT / "scripts/v10_evaluate_locked.py"
    spec = importlib.util.spec_from_file_location("v10_evaluate_locked_test_module", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_complete_v7_prerequisite(root: Path) -> Path:
    """Build a synthetic but internally complete frozen-V7 provenance chain."""
    pollipi_commit = "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
    insepi_commit = "980813bab996909020140fad5bd83b055eb3db9c"
    allocator = "a8ac75991ab28fd74a3f3a5482304a2b127a97bc"
    generator = "1c4c5ffc214ebdfb71ddabe170a071352acd4879"
    evaluator = "6860fa973ce8f25b25028f49723710e8a920709c"
    materializer = "11f5a7ad97dc71720a5ba0249bf36c6997a4e289"
    baseline = "94288d76f69b57e9b3096dfb9fc90f1602ea79d836a4dcf2534979f7c7cd9975"
    world_spec = "9442a25c3c35febaf44b1bc8f1bedce5524aa34a926f80513069593891982ac3"
    pixel_sha = "3" * 64
    world_fingerprint = "4" * 64

    v7_pip = root / "v7_pip_freeze.txt"
    v7_pip.write_text("numpy==2.4.6\n", encoding="utf-8")
    v7_runtime = root / "v7_runtime_environment.json"
    _write_json(v7_runtime, {
        "schema": "pollipi-insepi-v7-runtime-environment-v1",
        "python_version": "3.11.16",
        "numpy_version": "2.4.6",
        "master_seed_derived": False,
        "v7_pixels_materialised": False,
        "observer_output_inspected": False,
        "pip_freeze_sha256": _sha(v7_pip),
    })
    v7_runtime_freeze = root / "v7_runtime_freeze.json"
    _write_json(v7_runtime_freeze, {
        "schema": "pollipi-insepi-v7-runtime-freeze-v1",
        "python_version": "3.11.16",
        "numpy_version": "2.4.6",
    })
    v7_report = root / "v7_report.json"
    _write_json(v7_report, {"schema": "synthetic-v7-report-for-contract-test"})
    v7_pollipi = root / "pollipi_v7_trace.jsonl"
    v7_pollipi.write_text("synthetic-pollipi-trace\n", encoding="utf-8")
    v7_insepi = root / "insepi_v7_trace.jsonl"
    v7_insepi.write_text("synthetic-insepi-trace\n", encoding="utf-8")
    v7_materialisation = root / "v7_materialisation_receipt.json"
    _write_json(v7_materialisation, {
        "frozen_inputs": {
            "pollipi_method_sha": pollipi_commit,
            "insepi_method_sha": insepi_commit,
            "allocator_sha": allocator,
            "generator_sha": generator,
            "baseline_registry_sha256": baseline,
            "world_spec_sha256": world_spec,
        },
        "pixel_artifact_sha256": pixel_sha,
        "world_fingerprint": world_fingerprint,
    })
    v7_ledger = root / "v7_execution_ledger.json"
    _write_json(v7_ledger, {
        "schema": "pollipi-insepi-v7-execution-ledger-v1",
        "claim_level": "B",
        "gate_passed": False,
        "pollipi_source_commit": pollipi_commit,
        "insepi_source_commit": insepi_commit,
        "allocator_sha": allocator,
        "generator_sha": generator,
        "evaluator_freeze_sha": evaluator,
        "materializer_freeze_sha": materializer,
        "baseline_registry_sha256": baseline,
        "world_spec_sha256": world_spec,
        "runtime_python_version": "3.11.16",
        "runtime_numpy_version": "2.4.6",
        "orchestrator_sha": "5" * 40,
        "pixel_artifact_sha256": pixel_sha,
        "world_fingerprint": world_fingerprint,
        "report_sha256": _sha(v7_report),
        "runtime_environment_sha256": _sha(v7_runtime),
        "runtime_pip_freeze_sha256": _sha(v7_pip),
        "runtime_freeze_sha256": _sha(v7_runtime_freeze),
        "materialisation_receipt_sha256": _sha(v7_materialisation),
        "pollipi_trace_sha256": _sha(v7_pollipi),
        "insepi_trace_sha256": _sha(v7_insepi),
    })
    return v7_ledger


def test_v10_evaluation_receipt_binds_complete_execution_provenance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_v10_evaluation_script()
    implementation = tmp_path / "implementation.json"
    evaluator = tmp_path / "evaluator.json"
    pixel = tmp_path / "pixel.json"
    protocol = tmp_path / "protocol.json"
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    runtime_manifest = runtime_dir / "runtime_environment.json"
    pip_freeze = runtime_dir / "pip_freeze.txt"
    implementation.write_text(json.dumps({
        "schema": "interaction-sensing-v10-execution-implementation-freeze-v1"
    }) + "\n")
    evaluator.write_text(json.dumps({
        "schema": "interaction-sensing-v10-evaluator-freeze-v1"
    }) + "\n")
    pixel.write_text(json.dumps({
        "schema": "interaction-sensing-v10-real-pixel-artifact-freeze-v1"
    }) + "\n")
    protocol.write_text(json.dumps({
        "schema": "interaction-sensing-v10-real-video-protocol-freeze-v1"
    }) + "\n")
    pip_freeze.write_text("numpy==2.4.6\npollipi-analysis==0.2.0\n")
    runtime_manifest.write_text(json.dumps({
        "schema": "interaction-sensing-v10-runtime-environment-v1",
        "python_version": "3.11.16",
        "numpy_version": "2.4.6",
        "pip_freeze_sha256": hashlib.sha256(pip_freeze.read_bytes()).hexdigest(),
        "observer_output_inspected": False,
        "canonical_v10_pixels_read": False,
    }) + "\n")
    v7_ledger = _build_complete_v7_prerequisite(tmp_path)
    v7_ledger_payload = json.loads(v7_ledger.read_text())

    fake_report = {
        "schema": "interaction-sensing-v10-locked-report-v1",
        "claim": {"level": "C", "label": "partial_or_family_specific_transfer"},
        "provenance": {
            "pollipi_trace_sha256": "1" * 64,
            "insepi_trace_sha256": "2" * 64,
            "pixel_artifact_sha256": "3" * 64,
        },
        "observer_transfer": {
            "positive_high_tier_family_count": 3,
            "dose_monotone_family_count": 2,
        },
        "allocation_transfer": {
            "v6_cell_pass_count": 20,
            "v6_overall_mean_paired_uniform_recall_ratio": 0.95,
        },
    }
    monkeypatch.setattr(module, "evaluate_v10", lambda *_args, **_kwargs: fake_report.copy())

    report_path = tmp_path / "v10_report.json"
    receipt_path = tmp_path / "out" / "v10_evaluation_receipt.json"
    orchestrator = "a" * 40
    monkeypatch.setattr(sys, "argv", [
        "v10_evaluate_locked.py",
        "--artifact-dir", str(tmp_path / "unused-artifact"),
        "--pollipi-trace", str(tmp_path / "unused-pollipi.jsonl"),
        "--insepi-trace", str(tmp_path / "unused-insepi.jsonl"),
        "--output", str(report_path),
        "--receipt", str(receipt_path),
        "--orchestrator-sha", orchestrator,
        "--implementation-freeze", str(implementation),
        "--evaluator-freeze", str(evaluator),
        "--pixel-freeze", str(pixel),
        "--protocol-freeze", str(protocol),
        "--runtime-manifest", str(runtime_manifest),
        "--v7-ledger", str(v7_ledger),
    ])
    module.main()

    report = json.loads(report_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    copied_v7 = receipt_path.parent / "v7_prerequisite_execution_ledger.json"
    copied_v7_report = receipt_path.parent / "v7_prerequisite_report.json"
    copied_v7_materialisation = receipt_path.parent / "v7_prerequisite_materialisation_receipt.json"
    copied_v7_runtime = receipt_path.parent / "v7_prerequisite_runtime_environment.json"
    copied_v7_pip = receipt_path.parent / "v7_prerequisite_runtime_pip_freeze.txt"
    copied_v7_runtime_freeze = receipt_path.parent / "v7_prerequisite_runtime_freeze.json"
    copied_v7_pollipi = receipt_path.parent / "v7_prerequisite_pollipi_trace.jsonl"
    copied_v7_insepi = receipt_path.parent / "v7_prerequisite_insepi_trace.jsonl"
    copied_runtime = receipt_path.parent / "runtime_environment.json"
    copied_freeze = receipt_path.parent / "runtime_pip_freeze.txt"

    assert copied_v7.read_bytes() == v7_ledger.read_bytes()
    assert copied_v7_report.read_bytes() == (tmp_path / "v7_report.json").read_bytes()
    assert copied_v7_materialisation.read_bytes() == (tmp_path / "v7_materialisation_receipt.json").read_bytes()
    assert copied_v7_runtime.read_bytes() == (tmp_path / "v7_runtime_environment.json").read_bytes()
    assert copied_v7_pip.read_bytes() == (tmp_path / "v7_pip_freeze.txt").read_bytes()
    assert copied_v7_runtime_freeze.read_bytes() == (tmp_path / "v7_runtime_freeze.json").read_bytes()
    assert copied_v7_pollipi.read_bytes() == (tmp_path / "pollipi_v7_trace.jsonl").read_bytes()
    assert copied_v7_insepi.read_bytes() == (tmp_path / "insepi_v7_trace.jsonl").read_bytes()
    assert copied_runtime.read_bytes() == runtime_manifest.read_bytes()
    assert copied_freeze.read_bytes() == pip_freeze.read_bytes()

    expected = {
        "orchestrator_sha": orchestrator,
        "implementation_freeze_sha256": module.sha256_file(implementation),
        "evaluator_freeze_sha256": module.sha256_file(evaluator),
        "pixel_freeze_sha256": module.sha256_file(pixel),
        "protocol_freeze_sha256": module.sha256_file(protocol),
        "runtime_environment_sha256": module.sha256_file(runtime_manifest),
        "runtime_pip_freeze_sha256": module.sha256_file(pip_freeze),
        "runtime_python_version": "3.11.16",
        "runtime_numpy_version": "2.4.6",
        "v7_prerequisite_ledger_sha256": module.sha256_file(v7_ledger),
        "v7_prerequisite_claim_level": "B",
        "v7_prerequisite_gate_passed": False,
        "v7_prerequisite_world_fingerprint": v7_ledger_payload["world_fingerprint"],
        "v7_prerequisite_pixel_artifact_sha256": v7_ledger_payload["pixel_artifact_sha256"],
    }
    assert report["execution_provenance"] == expected
    for key, value in expected.items():
        assert receipt[key] == value
    assert receipt["report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert receipt["pollipi_trace_sha256"] == "1" * 64
    assert receipt["insepi_trace_sha256"] == "2" * 64
    assert receipt["pixel_artifact_sha256"] == "3" * 64
