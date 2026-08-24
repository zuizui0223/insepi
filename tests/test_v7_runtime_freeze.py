from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_script(relative: str, module_name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_evaluator_script():
    return _load_script("scripts/v7_evaluate_locked.py", "v7_evaluate_locked_runtime_test")


def _runtime_files(tmp_path: Path):
    pip_freeze = tmp_path / "v7_pip_freeze.txt"
    pip_freeze.write_text("numpy==2.4.6\npollipi-analysis==0.2.0\n", encoding="utf-8")
    runtime = tmp_path / "v7_runtime_environment.json"
    runtime.write_text(
        json.dumps(
            {
                "schema": "pollipi-insepi-v7-runtime-environment-v1",
                "python_version": "3.11.16",
                "numpy_version": "2.4.6",
                "pip_freeze_sha256": hashlib.sha256(pip_freeze.read_bytes()).hexdigest(),
                "master_seed_derived": False,
                "v7_pixels_materialised": False,
                "observer_output_inspected": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    freeze = tmp_path / "v7_runtime_freeze.json"
    freeze.write_text(
        json.dumps(
            {
                "schema": "pollipi-insepi-v7-runtime-freeze-v1",
                "python_version": "3.11.16",
                "numpy_version": "2.4.6",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime, pip_freeze, freeze


def test_v7_runtime_freeze_is_pre_materialisation_and_lock_has_no_result() -> None:
    freeze = json.loads((ROOT / "benchmarks/v7_runtime_freeze.json").read_text())
    lock = json.loads((ROOT / "benchmarks/v7_lock_manifest.json").read_text())
    assert freeze["schema"] == "pollipi-insepi-v7-runtime-freeze-v1"
    assert freeze["status"] == "pre-materialisation-frozen"
    assert freeze["python_version"] == "3.11.16"
    assert freeze["numpy_version"] == "2.4.6"
    assert freeze["insepi_frame_index_gate"]["probe_indices"] == [0, 1, 179]
    origin = freeze["frozen_module_origin_gate"]
    assert origin["pollipi_verified_modules"] == ["pollipi_analysis", "pollipi_analysis.pipeline"]
    assert "interaction_sensing.noise" in origin["insepi_verified_modules"]
    assert "sys.modules" in origin["module_cache_rule"]
    assert lock["status"] in {"blocked", "ready"}
    for key in ("master_seed_hex", "world_fingerprint", "pollipi_trace_sha256", "cross_report_sha256"):
        assert lock.get(key) in (None, "")


def test_v7_frozen_observer_runner_blobs_match_runtime_freeze() -> None:
    freeze = json.loads((ROOT / "benchmarks/v7_runtime_freeze.json").read_text())
    for relative, expected in freeze["execution_file_git_blob_sha1"].items():
        # Ask Git to apply the repository's clean filters so a Windows CRLF
        # checkout verifies the same canonical blob as the Linux one-shot run.
        actual = subprocess.run(
            ["git", "hash-object", relative],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert actual == expected


def test_v7_frozen_module_origin_guards_accept_inside_and_reject_outside(tmp_path: Path) -> None:
    pollipi = _load_script("scripts/v7_run_pollipi_frozen.py", "v7_pollipi_origin_guard_test")
    insepi = _load_script("scripts/v7_run_insepi_frozen.py", "v7_insepi_origin_guard_test")
    root = tmp_path / "frozen-src"
    root.mkdir()
    inside = root / "module.py"
    inside.write_text("# inside\n", encoding="utf-8")
    outside = tmp_path / "wrong-module.py"
    outside.write_text("# outside\n", encoding="utf-8")
    inside_module = SimpleNamespace(__file__=str(inside))
    outside_module = SimpleNamespace(__file__=str(outside))
    for runner in (pollipi, insepi):
        assert runner._require_module_under(inside_module, root, "inside") == inside.resolve()
        with pytest.raises(RuntimeError, match="imported from wrong origin"):
            runner._require_module_under(outside_module, root, "outside")
        prefix = f"v7_origin_guard_poison_{id(runner)}"
        sys.modules[prefix] = SimpleNamespace()
        sys.modules[prefix + ".child"] = SimpleNamespace()
        runner._purge_module_prefix(prefix)
        assert prefix not in sys.modules
        assert prefix + ".child" not in sys.modules


def test_v7_insepi_runner_declares_pre_materialisation_index_invariance_gate() -> None:
    path = ROOT / "scripts/v7_run_insepi_frozen.py"
    module = _load_script("scripts/v7_run_insepi_frozen.py", "v7_insepi_runner_contract_test")
    assert module.FRAME_INDEX_INVARIANCE_PROBES == (0, 1, 179)
    text = path.read_text(encoding="utf-8")
    assert "decision-relevant outputs depend on frame_index" in text
    assert "V7_INSEPI_FRAME_INDEX_INVARIANCE PASS" in text
    assert "V7_INSEPI_MODULE_ORIGIN PASS" in text


def test_v7_pollipi_runner_declares_frozen_module_origin_gate() -> None:
    text = (ROOT / "scripts/v7_run_pollipi_frozen.py").read_text(encoding="utf-8")
    assert "V7_POLLIPI_MODULE_ORIGIN PASS" in text
    assert "pollipi_analysis.pipeline" in text


def test_v7_runtime_loader_accepts_exact_pre_materialisation_environment(tmp_path: Path) -> None:
    module = _load_evaluator_script()
    runtime, pip_freeze, freeze = _runtime_files(tmp_path)
    loaded, loaded_freeze = module._load_runtime(runtime, pip_freeze, freeze)
    assert loaded["python_version"] == "3.11.16"
    assert loaded["numpy_version"] == "2.4.6"
    assert loaded_freeze["schema"] == "pollipi-insepi-v7-runtime-freeze-v1"


@pytest.mark.parametrize(
    ("field", "bad_value", "message"),
    [
        ("python_version", "3.11.17", "Python version"),
        ("numpy_version", "2.5.0", "NumPy version"),
        ("master_seed_derived", True, "before seed derivation"),
        ("v7_pixels_materialised", True, "before pixel materialisation"),
        ("observer_output_inspected", True, "before observer output"),
    ],
)
def test_v7_runtime_loader_rejects_runtime_drift(
    tmp_path: Path,
    field: str,
    bad_value: object,
    message: str,
) -> None:
    module = _load_evaluator_script()
    runtime, pip_freeze, freeze = _runtime_files(tmp_path)
    obj = json.loads(runtime.read_text())
    obj[field] = bad_value
    runtime.write_text(json.dumps(obj) + "\n")
    with pytest.raises(ValueError, match=message):
        module._load_runtime(runtime, pip_freeze, freeze)


def test_v7_runtime_loader_rejects_pip_freeze_tamper(tmp_path: Path) -> None:
    module = _load_evaluator_script()
    runtime, pip_freeze, freeze = _runtime_files(tmp_path)
    pip_freeze.write_text(pip_freeze.read_text() + "pytest==9.1.1\n")
    with pytest.raises(ValueError, match="pip-freeze bytes"):
        module._load_runtime(runtime, pip_freeze, freeze)


def test_v7_capture_script_forbids_existing_final_artifacts() -> None:
    module = _load_script("scripts/v7_capture_runtime_environment.py", "v7_capture_runtime_test")
    forbidden = set(module.FORBIDDEN_PRECAPTURE_PATHS)
    assert ".v7/run/v7_pixels.npz" in forbidden
    assert ".v7/run/v7_materialisation_receipt.json" in forbidden
    assert ".v7/run/pollipi_v7_trace.jsonl" in forbidden
    assert ".v7/run/v7_execution_ledger.json" in forbidden


def test_v7_evaluation_ledger_binds_runtime_provenance(tmp_path: Path, monkeypatch) -> None:
    module = _load_evaluator_script()
    runtime, pip_freeze, runtime_freeze = _runtime_files(tmp_path)

    receipt = tmp_path / "materialisation.json"
    pollipi_trace = tmp_path / "pollipi.jsonl"
    insepi_trace = tmp_path / "insepi.jsonl"
    baseline = tmp_path / "baseline.json"
    report = tmp_path / "out/v7_report.json"
    ledger = tmp_path / "out/v7_execution_ledger.json"
    receipt.write_text(
        json.dumps(
            {
                "world_fingerprint": "world-fingerprint",
                "pixel_artifact_sha256": "a" * 64,
                "master_seed_hex": "b" * 64,
                "frozen_inputs": {
                    "pollipi_method_sha": "pollipi-commit",
                    "insepi_method_sha": "insepi-commit",
                    "allocator_sha": "allocator",
                    "generator_sha": "generator",
                    "baseline_registry_sha256": "c" * 64,
                    "world_spec_sha256": "d" * 64,
                },
            }
        )
        + "\n"
    )
    pollipi_trace.write_text("pollipi\n")
    insepi_trace.write_text("insepi\n")
    baseline.write_text("{}\n")

    monkeypatch.setattr(
        module,
        "read_trace_jsonl",
        lambda path, **_kwargs: (
            {"source_commit": "pollipi-commit" if path == pollipi_trace else "insepi-commit"},
            [SimpleNamespace()],
        ),
    )
    monkeypatch.setattr(
        module,
        "load_baseline_registry",
        lambda _path: {"registry_sha256": "c" * 64},
    )
    monkeypatch.setattr(module, "evaluate_v7_traces", lambda *_args, **_kwargs: [SimpleNamespace()])
    robustness = SimpleNamespace(
        worst_joint_ratio=1.01,
        mean_joint_ratio=1.02,
        max_tv=0.20,
        to_dict=lambda: {"worst_joint_ratio": 1.01, "mean_joint_ratio": 1.02, "max_tv": 0.20},
    )
    gate = SimpleNamespace(passed=True, failures=(), v6=robustness)
    monkeypatch.setattr(module, "apply_locked_gate", lambda *_args, **_kwargs: gate)
    monkeypatch.setattr(
        module,
        "build_report",
        lambda *, metrics, gate, provenance: {"metrics": "synthetic", "provenance": provenance},
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "v7_evaluate_locked.py",
            "--receipt", str(receipt),
            "--pollipi-trace", str(pollipi_trace),
            "--insepi-trace", str(insepi_trace),
            "--baseline-registry", str(baseline),
            "--report", str(report),
            "--ledger", str(ledger),
            "--orchestrator-sha", "e" * 40,
            "--evaluator-freeze-sha", "f" * 40,
            "--materializer-freeze-sha", "1" * 40,
            "--runtime-manifest", str(runtime),
            "--runtime-pip-freeze", str(pip_freeze),
            "--runtime-freeze", str(runtime_freeze),
        ],
    )
    module.main()

    result = json.loads(ledger.read_text())
    assert result["runtime_python_version"] == "3.11.16"
    assert result["runtime_numpy_version"] == "2.4.6"
    assert result["runtime_environment_sha256"] == module._sha256_file(runtime)
    assert result["runtime_pip_freeze_sha256"] == module._sha256_file(pip_freeze)
    assert result["runtime_freeze_sha256"] == module._sha256_file(runtime_freeze)
    copied_freeze = ledger.parent / "v7_runtime_freeze.json"
    assert copied_freeze.read_bytes() == runtime_freeze.read_bytes()
    assert result["report_sha256"] == module._sha256_file(report)
