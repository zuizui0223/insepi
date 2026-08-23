from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from interaction_sensing.simulation import v10_evaluator as v10


def _artifact():
    return SimpleNamespace(
        condition_registry=tuple(
            {"condition_id": f"condition-{index}"}
            for index in range(6916)
        )
    )


def _pollipi_payloads() -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = [
        {
            "record_type": "provenance",
            "schema": v10.POLLIPI_TRACE_SCHEMA,
            "source_commit": v10.POLLIPI_COMMIT,
            "pixel_artifact_sha256": v10.PIXEL_SHA256,
            "condition_registry_sha256": v10.CONDITION_REGISTRY_SHA256,
            "condition_count": 6916,
        }
    ]
    payloads.extend(
        {
            "record_type": "result",
            "schema": v10.POLLIPI_TRACE_SCHEMA,
            "condition_index": index,
            "condition_id": f"condition-{index}",
            "pollipi_state": "no_activity",
            "pollipi_reason": "synthetic contract row",
            "global_synchrony": 0.0,
            "active_cell_proportion": 0.0,
            "estimated_global_shift": 0.0,
        }
        for index in range(6916)
    )
    return payloads


def _write(path: Path, payloads: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in payloads),
        encoding="utf-8",
    )


def _load(path: Path):
    return v10._load_trace(
        path,
        schema=v10.POLLIPI_TRACE_SCHEMA,
        expected_commit=v10.POLLIPI_COMMIT,
        provenance_keys=v10.POLLIPI_PROVENANCE_KEYS,
        result_keys=v10.POLLIPI_RESULT_KEYS,
        artifact=_artifact(),
    )


def test_v10_trace_reader_accepts_exact_canonical_contract(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    _write(path, _pollipi_payloads())
    trace = _load(path)
    assert len(trace.rows) == 6916
    assert trace.provenance["source_commit"] == v10.POLLIPI_COMMIT
    assert len(trace.sha256) == 64


def test_v10_trace_reader_rejects_truth_key_injection(tmp_path: Path) -> None:
    payloads = _pollipi_payloads()
    payloads[1]["family"] = "glare"
    path = tmp_path / "trace.jsonl"
    _write(path, payloads)
    with pytest.raises(RuntimeError, match="result key set differs"):
        _load(path)


def test_v10_trace_reader_rejects_condition_order_tamper(tmp_path: Path) -> None:
    payloads = _pollipi_payloads()
    payloads[1]["condition_index"] = 1
    payloads[2]["condition_index"] = 0
    path = tmp_path / "trace.jsonl"
    _write(path, payloads)
    with pytest.raises(RuntimeError, match="canonical condition-index order"):
        _load(path)


def test_v10_trace_reader_rejects_condition_id_tamper(tmp_path: Path) -> None:
    payloads = _pollipi_payloads()
    payloads[100]["condition_id"] = "condition-falsified"
    path = tmp_path / "trace.jsonl"
    _write(path, payloads)
    with pytest.raises(RuntimeError, match="condition id does not match"):
        _load(path)


@pytest.mark.parametrize(
    ("key", "replacement", "message"),
    [
        ("source_commit", "0" * 40, "exact frozen V5 commit"),
        ("pixel_artifact_sha256", "0" * 64, "pixel artifact identity"),
        ("condition_registry_sha256", "0" * 64, "condition-registry identity"),
    ],
)
def test_v10_trace_reader_rejects_provenance_identity_tamper(
    tmp_path: Path,
    key: str,
    replacement: str,
    message: str,
) -> None:
    payloads = _pollipi_payloads()
    payloads[0][key] = replacement
    path = tmp_path / "trace.jsonl"
    _write(path, payloads)
    with pytest.raises(RuntimeError, match=message):
        _load(path)


def test_v10_trace_reader_rejects_missing_or_extra_rows(tmp_path: Path) -> None:
    missing = _pollipi_payloads()[:-1]
    path = tmp_path / "missing.jsonl"
    _write(path, missing)
    with pytest.raises(RuntimeError, match="provenance \+ 6916 results"):
        _load(path)

    extra = _pollipi_payloads()
    extra.append(dict(extra[-1]))
    path = tmp_path / "extra.jsonl"
    _write(path, extra)
    with pytest.raises(RuntimeError, match="provenance \+ 6916 results"):
        _load(path)
