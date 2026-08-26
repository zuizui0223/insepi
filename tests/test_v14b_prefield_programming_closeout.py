from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from interaction_sensing.prefield_programming_closeout import (
    FROZEN_V14B_PHASE_SURFACE_SHA256,
    build_v14b_prefield_programming_closeout,
)
from interaction_sensing.simulation.dimensionless_observability_v14 import (
    LatentRegime,
)
from interaction_sensing.simulation.dimensionless_observability_v14a2 import (
    SpatiotemporalPoint,
    nuisance_field,
    signature_for,
)

ROOT = Path(__file__).resolve().parents[1]
WORLD_PATH = ROOT / "benchmarks/v14a2_spatiotemporal_world_protocol.json"
TERNARY_PATH = ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_protocol.json"
SUMMARY_PATH = ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_result.json"
FIGURE_PATH = ROOT / "benchmarks/v14b_frozen_ternary_phase_figure_data.json"
CLOSEOUT_PATH = ROOT / "benchmarks/v14b_prefield_programming_closeout.json"
SCRIPT_PATH = ROOT / "scripts/build_v14b_prefield_programming_closeout.py"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sources() -> dict[str, dict[str, object]]:
    return {
        "world_protocol": _read(WORLD_PATH),
        "ternary_protocol": _read(TERNARY_PATH),
        "locked_summary": _read(SUMMARY_PATH),
        "figure_data": _read(FIGURE_PATH),
    }


def test_closeout_rebuilds_exactly_from_locked_evidence() -> None:
    result = build_v14b_prefield_programming_closeout(**_sources())

    assert result == _read(CLOSEOUT_PATH)
    assert result["status"] == "closed-pre-field-programming-result"
    assert (
        result["source_identity"]["phase_surface_sha256"]
        == FROZEN_V14B_PHASE_SURFACE_SHA256
    )
    assert result["source_identity"]["world_count"] == 5_880_000
    assert result["source_identity"]["observer_retuned"] is False
    assert (
        result["synthesis_boundary"]["explicit_cross_state_observation_factor_measured"]
        is False
    )


def test_reason_tagged_u_is_a_conditioned_estimand_not_silent_absence() -> None:
    result = build_v14b_prefield_programming_closeout(**_sources())
    measurement = result["frozen_measurement"]
    direct = result["observation_condition_dependence"][
        "direct_actor_channel_boundary_on_target_truth"
    ]

    assert measurement["global_undetermined_rate"] == pytest.approx(0.2533362244897959)
    assert measurement["overlap_share_of_undetermined"] == pytest.approx(
        0.8943976874592596
    )
    assert measurement["forced_binary_false_negative_rate"] == 0.3569
    assert direct["pi3_zero"]["forced_binary_false_negative_rate"] == 1.0
    assert direct["pi3_positive_mean"]["forced_binary_false_negative_rate"] == 0.1961
    assert direct["zero_minus_positive"]["undetermined_rate"] == pytest.approx(
        0.257623214285714
    )


def test_interaction_process_and_exogenous_field_share_one_generator() -> None:
    point = SpatiotemporalPoint(1.0, 1.0, 1.0, 1.0, 1.0, 8.0)
    target = signature_for(point, LatentRegime.TARGET_ONLY, seed=141001)
    nuisance = signature_for(point, LatentRegime.NUISANCE_ONLY, seed=141001)

    assert target.entry_exit_completeness == 1.0
    assert target.direct_target_signal_fraction > 0.0
    assert nuisance.entry_exit_completeness == 0.0
    assert nuisance.direct_target_signal_fraction == 0.0

    first = nuisance_field(point, seed=141001)
    second = nuisance_field(point, seed=141001)
    assert all(
        np.array_equal(left, right) for left, right in zip(first, second, strict=True)
    )


@pytest.mark.parametrize(
    ("source_name", "mutation", "message"),
    [
        (
            "locked_summary",
            lambda source: source["provenance"].__setitem__(
                "phase_surface_sha256", "0" * 64
            ),
            "phase-surface identity changed",
        ),
        (
            "ternary_protocol",
            lambda source: source.__setitem__("alpha", 0.10),
            "family-wise alpha changed",
        ),
        (
            "locked_summary",
            lambda source: source["global_summary"].__setitem__(
                "observer_retuned", True
            ),
            "observer_retuned must remain false",
        ),
        (
            "world_protocol",
            lambda source: source["process_model"].__setitem__(
                "target", "changed after freeze"
            ),
            "world protocol identity changed",
        ),
    ],
)
def test_closeout_fails_if_frozen_identity_changes(
    source_name: str,
    mutation,
    message: str,
) -> None:
    sources = deepcopy(_sources())
    mutation(sources[source_name])

    with pytest.raises(ValueError, match=message):
        build_v14b_prefield_programming_closeout(**sources)


def test_runner_writes_the_committed_closeout(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("v14b_closeout_runner", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    output_path = tmp_path / "closeout.json"

    result = runner.run(
        world_protocol_path=WORLD_PATH,
        ternary_protocol_path=TERNARY_PATH,
        locked_summary_path=SUMMARY_PATH,
        figure_data_path=FIGURE_PATH,
        output_path=output_path,
    )

    assert result == _read(CLOSEOUT_PATH)
    assert json.loads(output_path.read_text(encoding="utf-8")) == result
