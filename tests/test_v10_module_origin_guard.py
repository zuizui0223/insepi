from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load_script(name: str, module_name: str):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v10_frozen_module_origin_guards_accept_inside_and_reject_outside(tmp_path: Path) -> None:
    pollipi = load_script("v10_run_pollipi_frozen.py", "v10_pollipi_origin_guard_test")
    insepi = load_script("v10_run_insepi_frozen.py", "v10_insepi_origin_guard_test")
    root = tmp_path / "exact-checkout-src"
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
        prefix = f"v10_origin_guard_poison_{id(runner)}"
        sys.modules[prefix] = SimpleNamespace()
        sys.modules[prefix + ".child"] = SimpleNamespace()
        runner._purge_module_prefix(prefix)
        assert prefix not in sys.modules
        assert prefix + ".child" not in sys.modules


def test_v10_runner_text_exposes_origin_pass_markers() -> None:
    pollipi_text = (SCRIPTS / "v10_run_pollipi_frozen.py").read_text(encoding="utf-8")
    insepi_text = (SCRIPTS / "v10_run_insepi_frozen.py").read_text(encoding="utf-8")
    assert "V10_POLLIPI_MODULE_ORIGIN PASS" in pollipi_text
    assert "pollipi_analysis.pipeline" in pollipi_text
    assert "V10_INSEPI_MODULE_ORIGIN PASS" in insepi_text
    assert "interaction_sensing.noise" in insepi_text
    assert "interaction_sensing.simulation.factorial_benchmark_v4" in insepi_text
    assert "interaction_sensing.simulation.visual_contradiction_v2" in insepi_text


def test_v10_execution_freeze_declares_runtime_origin_gate() -> None:
    import json

    freeze = json.loads((ROOT / "benchmarks/v10_execution_implementation_freeze.json").read_text())
    gate = freeze["frozen_module_origin_gate"]
    assert gate["pollipi_verified_modules"] == ["pollipi_analysis", "pollipi_analysis.pipeline"]
    assert "interaction_sensing.noise" in gate["insepi_verified_modules"]
    assert "sys.modules" in gate["module_cache_rule"]
