from pathlib import Path

from interaction_sensing import target_observer_v14b


def test_frozen_target_observer_blob_contract_is_documented() -> None:
    marker = Path(__file__).resolve().parents[1] / "benchmarks/NUISANCE_TARGET_FREEZE_SHA.txt"
    text = marker.read_text(encoding="utf-8")
    assert "8bbb35809108625a18fda31323668df74cb4f00b" in text
    assert "Target observer is frozen" in text
    assert target_observer_v14b.observe_target_v14b is not None
