from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = _load_script("v13_builder", ROOT / "scripts/v13_build_randomisation.py")
validator = _load_script("v13_validator", ROOT / "scripts/v13_validate_field_bundle.py")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v13_protocol_freezes_block_level_replication_and_prior_results() -> None:
    protocol = json.loads((ROOT / "benchmarks/v13_physical_intervention_protocol.json").read_text())
    assert protocol["status"] == "pre-field-frozen-template"
    assert "frames within a block are repeated measurements" in protocol["experimental_unit"]
    assert protocol["splits"]["development"]["expected_block_count"] == 108
    assert protocol["splits"]["heldout"]["expected_block_count"] == 72
    assert protocol["splits"]["total_expected_block_count"] == 180
    assert protocol["historical_boundary"]["v7"] == {"gate": "FAIL", "claim_level": "C"}
    assert protocol["historical_boundary"]["v11"]["claim_level"] == "D"
    assert protocol["historical_boundary"]["v12"]["claim_level"] == "B"


def test_v13_randomisation_is_deterministic_for_same_private_salt(tmp_path: Path) -> None:
    salt = "ab" * 32
    a = tmp_path / "a"
    b = tmp_path / "b"
    first = builder.build(salt, a)
    second = builder.build(salt, b)
    assert first == second
    for name in (
        "v13_private_truth_ledger.csv",
        "v13_observer_plan.csv",
        "v13_protected_qc_plan.csv",
        "v13_randomisation_commitment.json",
    ):
        assert (a / name).read_bytes() == (b / name).read_bytes()


def test_v13_different_salt_changes_opaque_ids_without_changing_design_size(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    ca = builder.build("ab" * 32, a)
    cb = builder.build("cd" * 32, b)
    ids_a = {row["block_id"] for row in _rows(a / "v13_private_truth_ledger.csv")}
    ids_b = {row["block_id"] for row in _rows(b / "v13_private_truth_ledger.csv")}
    assert ids_a.isdisjoint(ids_b)
    assert ca["counts"]["private_blocks"] == cb["counts"]["private_blocks"] == 180
    assert ca["counts"]["observer_phase_rows"] == cb["counts"]["observer_phase_rows"] == 720


def test_v13_public_plan_contains_no_latent_treatment_truth(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    salt = "12" * 32
    commitment = builder.build(salt, out)
    public = (out / "v13_observer_plan.csv").read_text(encoding="utf-8").lower()
    private = (out / "v13_private_truth_ledger.csv").read_text(encoding="utf-8").lower()
    assert "treatment_class" not in public
    assert "event_side" not in public
    assert "nuisance_side" not in public
    assert "shared_optical" not in public
    assert "no_fault" not in public
    assert "treatment_class" in private
    assert "event_side" in private
    assert salt not in public
    assert salt not in private
    assert salt not in json.dumps(commitment)
    assert commitment["salt_sha256"] == hashlib.sha256(salt.encode()).hexdigest()


def test_v13_every_block_has_placebo_then_exactly_three_randomised_active_phases(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    builder.build("34" * 32, out)
    private = {row["block_id"]: row for row in _rows(out / "v13_private_truth_ledger.csv")}
    public: dict[str, list[dict[str, str]]] = {}
    for row in _rows(out / "v13_observer_plan.csv"):
        public.setdefault(row["opaque_block_id"], []).append(row)
    assert len(private) == len(public) == 180
    for block_id, phases in public.items():
        phases.sort(key=lambda row: int(row["phase_order"]))
        assert [int(row["phase_order"]) for row in phases] == [0, 1, 2, 3]
        assert phases[0]["phase_name"] == "placebo"
        active = [row["phase_name"] for row in phases[1:]]
        assert active == private[block_id]["active_order"].split(";")
        assert set(active) == {"event_restore", "observability_restore", "shared_restore"}


def test_v13_development_and_heldout_day_scene_clusters_are_disjoint(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    builder.build("56" * 32, out)
    rows = _rows(out / "v13_private_truth_ledger.csv")
    dev = {(row["day_id"], row["scene_id"]) for row in rows if row["split"] == "development"}
    held = {(row["day_id"], row["scene_id"]) for row in rows if row["split"] == "heldout"}
    assert len(dev) == 9
    assert len(held) == 6
    assert dev.isdisjoint(held)


def test_v13_protected_qc_is_close_to_preregistered_quarter_without_affecting_truth(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    commitment = builder.build("78" * 32, out)
    selected = int(commitment["counts"]["protected_qc_blocks"])
    assert 30 <= selected <= 60
    qc = _rows(out / "v13_protected_qc_plan.csv")
    assert all(set(row) == {"block_id", "split", "protected_qc"} for row in qc)


def test_v13_validator_accepts_committed_plan_and_rejects_tamper(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    builder.build("9a" * 32, out)
    receipt = validator.validate(
        out / "v13_randomisation_commitment.json",
        out / "v13_private_truth_ledger.csv",
        out / "v13_observer_plan.csv",
        out / "v13_protected_qc_plan.csv",
    )
    assert receipt["status"] == "validated-randomisation-plan"
    assert receipt["block_count"] == 180
    assert receipt["phase_row_count"] == 720
    assert receipt["truth_leakage_detected"] is False

    public_path = out / "v13_observer_plan.csv"
    public_path.write_text(public_path.read_text() + "# tamper\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="committed file hash mismatch"):
        validator.validate(
            out / "v13_randomisation_commitment.json",
            out / "v13_private_truth_ledger.csv",
            public_path,
            out / "v13_protected_qc_plan.csv",
        )


def test_v13_validator_rejects_truth_leak_even_if_hash_commitment_is_recomputed(tmp_path: Path) -> None:
    out = tmp_path / "plan"
    builder.build("bc" * 32, out)
    public_path = out / "v13_observer_plan.csv"
    public_path.write_text(public_path.read_text() + "# no_fault\n", encoding="utf-8")
    commitment_path = out / "v13_randomisation_commitment.json"
    commitment = json.loads(commitment_path.read_text())
    commitment["observer_plan_sha256"] = hashlib.sha256(public_path.read_bytes()).hexdigest()
    commitment_path.write_text(json.dumps(commitment, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="truth leakage"):
        validator.validate(
            commitment_path,
            out / "v13_private_truth_ledger.csv",
            public_path,
            out / "v13_protected_qc_plan.csv",
        )


def test_v13_bad_salt_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        builder.build("not-a-64-hex-salt", tmp_path / "bad")
