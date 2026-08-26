"""Risk-calibration helpers for the V14b nuisance decision contract."""
from __future__ import annotations

import numpy as np


def upper_negative_quantile_threshold(scores: np.ndarray, alpha: float) -> float:
    """Return the smallest float strictly above the empirical (1-alpha) quantile.

    The threshold is calibrated from negative-world scores only.  It is a
    decision-contract boundary, not a nuisance-process feature or learned model.
    """
    values = np.asarray(scores, dtype=float)
    if values.size == 0:
        raise ValueError("negative calibration scores must be non-empty")
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must lie strictly between 0 and 1")
    if not np.all(np.isfinite(values)):
        raise ValueError("negative calibration scores must be finite")
    q = float(np.quantile(values, 1.0 - alpha, method="higher"))
    return float(np.nextafter(q, np.inf))
