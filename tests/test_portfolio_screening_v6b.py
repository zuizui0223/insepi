from interaction_sensing.simulation.observer_portfolio_v6 import PortfolioWeights
from interaction_sensing.simulation.portfolio_screening_v6b import _unique_ablations


def test_sparse_screening_omits_already_zero_arm_ablation():
    weights = PortfolioWeights(0.4, 0.2, 0.0, 0.4)
    rows = _unique_ablations(weights)
    assert "v6_sparse" in rows
    assert "v6_sparse_no_pollipi" in rows
    assert "v6_sparse_no_disagreement" in rows
    assert "v6_sparse_no_insepi" not in rows


def test_sparse_screening_returns_removed_quota_to_exploration():
    weights = PortfolioWeights(0.4, 0.2, 0.1, 0.3)
    rows = _unique_ablations(weights)
    no_insepi = rows["v6_sparse_no_insepi"]
    assert no_insepi.insepi == 0.0
    assert no_insepi.exploration == 0.5
    assert abs(sum(no_insepi.to_dict().values()) - 1.0) < 1e-9
