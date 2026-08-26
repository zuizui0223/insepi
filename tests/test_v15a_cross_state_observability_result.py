from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from interaction_sensing.cross_state_observability_v15a import (
    PHYSICAL_REGIMES,
    build_v15a_cross_state_result,
)
from interaction_sensing.prefield_programming_closeout import canonical_json_sha256

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "benchmarks/v15a_cross_state_observability_protocol.json"
SUMMARY_PATH = ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_result.json"
V15_CONTRACT_PATH = ROOT / "benchmarks/v15_observability_estimator_contract.json"
V14B_CLOSEOUT_PATH = ROOT / "benchmarks/v14b_prefield_programming_closeout.json"
RESULT_PATH = ROOT / "benchmarks/v15a_cross_state_observability_result.json"
RUNNER_PATH = ROOT / "scripts/run_v15a_cross_state_observability.py"
PREFREEZE_COMMIT = "5e8163891cd5f358f522cc0f9e99c6ff3c1318b4"
RESULT_CANONICAL_SHA256 = (
    "8fb62092fd739a9637ac366afc9b4d1ba3be7e5f7b1b948df8430a65810e837f"
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sources() -> dict[str, dict[str, object]]:
    return {
        "protocol": _read(PROTOCOL_PATH),
        "locked_summary": _read(SUMMARY_PATH),
        "v15_observability_contract": _read(V15_CONTRACT_PATH),
        "v14b_closeout": _read(V14B_CLOSEOUT_PATH),
    }


def test_committed_result_is_exact_rebuild_of_prefrozen_contract() -> None:
    committed = _read(RESULT_PATH)
    rebuilt = build_v15a_cross_state_result(
        **_sources(),
        prefreeze_commit=PREFREEZE_COMMIT,
    )

    assert rebuilt == committed
    assert canonical_json_sha256(committed) == RESULT_CANONICAL_SHA256
    assert committed["status"] == "locked-first-deterministic-expansion"
    assert committed["provenance"]["observer_retuned"] is False
    assert committed["provenance"]["parent_worlds_regenerated"] is False


def test_observation_layer_crosses_quiet_and_every_dynamic_regime() -> None:
    measurement = _read(RESULT_PATH)["measurement"]
    matrix = measurement["physical_regime_by_observation_availability"]

    assert set(matrix) == set(PHYSICAL_REGIMES)
    for regime in PHYSICAL_REGIMES:
        by_o = matrix[regime]["by_availability"]
        assert by_o["compromised"]["final_state_rates"]["undetermined"] == 1.0
        assert by_o["compromised"]["reason_rates"]["observation_compromised"] == 1.0
        assert by_o["unobservable"]["final_state_rates"]["censored"] == 1.0
        assert by_o["unobservable"]["reason_rates"]["observation_unavailable"] == 1.0

    quiet = measurement["quiet_baseline_cross"]
    assert quiet["observable"]["final_state_rates"]["baseline"] == 1.0
    assert quiet["compromised"]["final_state_rates"]["undetermined"] == 1.0
    assert quiet["unobservable"]["final_state_rates"]["censored"] == 1.0


def test_unsafe_binary_coercion_is_condition_dependent() -> None:
    comparator = _read(RESULT_PATH)["measurement"]["forced_binary_comparator"]
    by_o = comparator["by_availability"]

    assert by_o["observable"]["false_negative_rate"] == 0.3569
    assert by_o["compromised"]["false_negative_rate"] == 1.0
    assert by_o["unobservable"]["false_negative_rate"] == 1.0
    assert comparator["lattice_weighted_false_negative_rate"] == pytest.approx(
        0.9415363636363636
    )
    assert "not field prevalence" in comparator["warning"]


def test_partial_identification_and_parent_residual_are_not_hidden() -> None:
    measurement = _read(RESULT_PATH)["measurement"]
    widths = measurement["partial_identification"]
    consistency = measurement["parent_summary_consistency"]

    assert widths["observable_width"] == pytest.approx(0.4835690476190476)
    assert widths["compromised_width"] == 1.0
    assert widths["unobservable_width"] == 1.0
    assert widths["lattice_weighted_width"] == pytest.approx(0.9530517316017316)
    assert consistency["regime_rates_normalised_or_repaired"] is False
    assert consistency["within_regime_rate_sum_audit"]["target_nuisance_coupled"][
        "one_minus_state_rate_sum"
    ] == pytest.approx(5.102040816495901e-07)


def test_runner_rebuilds_to_new_path_and_refuses_overwrite(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("v15a_result_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    output = tmp_path / "v15a-result.json"

    rebuilt = runner.run(
        protocol_path=PROTOCOL_PATH,
        locked_summary_path=SUMMARY_PATH,
        v15_contract_path=V15_CONTRACT_PATH,
        v14b_closeout_path=V14B_CLOSEOUT_PATH,
        prefreeze_commit=PREFREEZE_COMMIT,
        output_path=output,
    )
    assert rebuilt == _read(RESULT_PATH)
    assert _read(output) == rebuilt
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        runner.run(
            protocol_path=PROTOCOL_PATH,
            locked_summary_path=SUMMARY_PATH,
            v15_contract_path=V15_CONTRACT_PATH,
            v14b_closeout_path=V14B_CLOSEOUT_PATH,
            prefreeze_commit=PREFREEZE_COMMIT,
            output_path=output,
        )
