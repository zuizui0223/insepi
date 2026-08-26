import inspect
import json
from pathlib import Path

from interaction_sensing.support_estimation import PrimaryStreamSupportEstimator


ROOT = Path(__file__).resolve().parents[1]


def test_v15_observability_contract_keeps_o_independent_of_t_and_n() -> None:
    contract = json.loads((ROOT / "benchmarks" / "v15_observability_estimator_contract.json").read_text())
    assert contract["generation"] == "V15"
    assert "O is not defined as 1 minus nuisance burden" in contract["hard_independence_rules"]
    assert "the O estimator may not consume PolliPi/target evidence" in contract["hard_independence_rules"]
    assert "the O estimator may not consume InsePi/nuisance risk" in contract["hard_independence_rules"]
    assert "the O estimator may not consume biological-event truth" in contract["hard_independence_rules"]

    parameters = tuple(inspect.signature(PrimaryStreamSupportEstimator.estimate).parameters)
    assert parameters == ("self", "measurements")


def test_v15_observability_contract_requires_all_five_measurement_requirements() -> None:
    contract = json.loads((ROOT / "benchmarks" / "v15_observability_estimator_contract.json").read_text())
    names = [row["name"] for row in contract["primary_stream_measurements"]]
    assert names == [
        "target_zone_coverage",
        "target_zone_visibility",
        "spatial_resolution",
        "photometric_sufficiency",
        "temporal_continuity",
    ]


def test_v15_observability_claim_ceiling_remains_pre_data() -> None:
    contract = json.loads((ROOT / "benchmarks" / "v15_observability_estimator_contract.json").read_text())
    assert contract["claim_ceiling"]["before_real_support_data"] == "software/semantic separation only"
    assert "field-calibrated observability" in contract["claim_ceiling"]["forbidden"]
    assert "visit accuracy" in contract["claim_ceiling"]["forbidden"]
