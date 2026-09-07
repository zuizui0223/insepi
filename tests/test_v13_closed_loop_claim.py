from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "v13_emit_closed_loop_claim.py"
spec = importlib.util.spec_from_file_location("v13_emit_closed_loop_claim", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_level_a_maps_to_physical_loop_closure() -> None:
    report = {
        "schema": "interaction-sensing-v13-physical-evaluation-v1",
        "claim": {
            "level": "A",
            "label": "material_physical_distinct_channel_advantage",
        },
    }
    mapped = module.map_report(report, "abc123")
    updates = mapped["cross_repository_updates"]
    assert updates["v3_physical_strict_refinement"] is True
    assert updates["mrod_like_physical_prospective_refinement"] is True
    assert updates["unified_physical_loop_closure"] is True
    assert updates["boundary_exact_rank_reduction"] is False


def test_level_b_does_not_overclaim_strict_v3_advantage() -> None:
    report = {
        "schema": "interaction-sensing-v13-physical-evaluation-v1",
        "claim": {
            "level": "B",
            "label": "conditional_physical_causal_identification",
        },
    }
    mapped = module.map_report(report, "abc123")
    updates = mapped["cross_repository_updates"]
    assert updates["v3_physical_strict_refinement"] is False
    assert updates["mrod_like_physical_prospective_refinement"] is True
    assert updates["unified_physical_loop_closure"] is True


def test_label_level_mismatch_fails_closed() -> None:
    report = {
        "schema": "interaction-sensing-v13-physical-evaluation-v1",
        "claim": {
            "level": "A",
            "label": "conditional_physical_causal_identification",
        },
    }
    with pytest.raises(ValueError, match="label/level mismatch"):
        module.map_report(report, "abc123")


def test_wrong_schema_fails_closed() -> None:
    report = {"schema": "other", "claim": {"level": "D", "label": "x"}}
    with pytest.raises(ValueError, match="wrong V13 physical evaluation schema"):
        module.map_report(report, "abc123")
