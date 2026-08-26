"""Fixed statistical primitives for the V14a2 plateau failure-source audit.

These helpers are intentionally small and frozen: the post-result diagnostic uses
pairwise AUC and one ridge-regularized LDA projection with no hyperparameter
search. They classify the source of the locked V14a2 ambiguity plateau; they do
not retune the locked observer or phase surface.
"""
from __future__ import annotations

import numpy as np


def auc(pos: np.ndarray, neg: np.ndarray) -> float:
    """Pairwise AUC with half credit for ties."""
    pos = np.asarray(pos, dtype=float)
    neg = np.asarray(neg, dtype=float)
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    diff = pos[:, None] - neg[None, :]
    return float(np.mean(diff > 0) + 0.5 * np.mean(diff == 0))


def fit_lda(x0: np.ndarray, x1: np.ndarray, ridge_fraction: float) -> np.ndarray:
    """Fit the single prefrozen ridge-LDA direction used by the audit."""
    x0 = np.asarray(x0, dtype=float)
    x1 = np.asarray(x1, dtype=float)
    if x0.ndim != 2 or x1.ndim != 2 or x0.shape[1] != x1.shape[1]:
        raise ValueError("LDA inputs must be two matrices with the same feature count")
    if len(x0) < 2 or len(x1) < 2:
        raise ValueError("each LDA class must contain at least two rows")
    if ridge_fraction <= 0:
        raise ValueError("ridge_fraction must be positive")

    pooled_rows = np.vstack([x0, x1])
    mean_variance = float(np.mean(np.var(pooled_rows, axis=0, ddof=1)))
    ridge = max(1e-12, ridge_fraction * mean_variance)
    c0 = np.atleast_2d(np.cov(x0, rowvar=False))
    c1 = np.atleast_2d(np.cov(x1, rowvar=False))
    pooled = ((len(x0) - 1) * c0 + (len(x1) - 1) * c1) / max(1, len(x0) + len(x1) - 2)
    pooled = pooled + ridge * np.eye(x0.shape[1])
    return np.linalg.pinv(pooled) @ (np.mean(x1, axis=0) - np.mean(x0, axis=0))
