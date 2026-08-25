from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_audit_module():
    path = ROOT / "scripts/v10_audit_frozen_observer_independence.py"
    spec = importlib.util.spec_from_file_location("v10_observer_independence_audit_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_observer_independence_audit_allows_unrelated_and_self_imports(tmp_path: Path) -> None:
    audit = _load_audit_module()
    source = tmp_path / "source"
    source.mkdir()
    (source / "ok.py").write_text(
        "import numpy as np\n"
        "from pollipi_analysis.pipeline import analyze\n"
        "def f():\n    return np.array([1])\n",
        encoding="utf-8",
    )
    assert audit.audit_tree(source, "interaction_sensing") == []


def test_observer_independence_audit_detects_static_cross_import(tmp_path: Path) -> None:
    audit = _load_audit_module()
    source = tmp_path / "source"
    source.mkdir()
    (source / "bad.py").write_text(
        "from interaction_sensing.noise import NoiseFirstPolicy\n",
        encoding="utf-8",
    )
    violations = audit.audit_tree(source, "interaction_sensing")
    assert len(violations) == 1
    assert "interaction_sensing.noise" in violations[0]


def test_observer_independence_audit_detects_literal_dynamic_import(tmp_path: Path) -> None:
    audit = _load_audit_module()
    source = tmp_path / "source"
    source.mkdir()
    (source / "bad_dynamic.py").write_text(
        "import importlib\n"
        "x = importlib.import_module('pollipi_analysis.pipeline')\n",
        encoding="utf-8",
    )
    violations = audit.audit_tree(source, "pollipi_analysis")
    assert len(violations) == 1
    assert "pollipi_analysis.pipeline" in violations[0]


def test_observer_independence_audit_does_not_overclaim_statistical_independence() -> None:
    text = (ROOT / "scripts/v10_audit_frozen_observer_independence.py").read_text(encoding="utf-8")
    assert "does not claim statistical independence" in text
    assert "V10_STATISTICAL_ERROR_INDEPENDENCE_CLAIM false" in text
