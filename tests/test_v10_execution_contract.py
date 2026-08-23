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
    v7_ledger = tmp_path / "v7_execution_ledger.json"
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
    v7_ledger.write_text(json.dumps({
        "schema": "pollipi-insepi-v7-execution-ledger-v1",
        "claim_level": "B",
        "gate_passed": False,
    }) + "\n")

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
    copied_runtime = receipt_path.parent / "runtime_environment.json"
    copied_freeze = receipt_path.parent / "runtime_pip_freeze.txt"
    assert copied_v7.read_bytes() == v7_ledger.read_bytes()
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
    }
    assert report["execution_provenance"] == expected
    for key, value in expected.items():
        assert receipt[key] == value
    assert receipt["report_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert receipt["pollipi_trace_sha256"] == "1" * 64
    assert receipt["insepi_trace_sha256"] == "2" * 64
    assert receipt["pixel_artifact_sha256"] == "3" * 64
