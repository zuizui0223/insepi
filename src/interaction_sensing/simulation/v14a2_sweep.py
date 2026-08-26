"""Frozen execution helpers for the V14a2 spatiotemporal phase sweep."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .dimensionless_observability_v14 import LatentRegime
from .dimensionless_observability_v14a2 import (
    IndeterminacyReasonA2,
    SpatiotemporalPoint,
    SpatiotemporalSignature,
    VisitInferenceA2,
    observation_support,
    route_scores,
    signature_for,
    truth,
)

PROTOTYPE_SEEDS = (101, 211, 307, 401)
REPLICATE_SEED_BASE = 1_402_000_000
DEVIATION_REGIME_ORDER = (
    LatentRegime.TARGET_ONLY,
    LatentRegime.NUISANCE_ONLY,
    LatentRegime.TARGET_COUPLED,
    LatentRegime.TARGET_NUISANCE_SUPERPOSED,
    LatentRegime.TARGET_NUISANCE_COUPLED,
)
_EPS = 1e-12


@dataclass(frozen=True, slots=True)
class FrozenThresholds:
    support_minimum: float = 0.20
    ambiguity_margin: float = 0.15
    target_high: float = 0.55
    target_low: float = 0.25
    nuisance_high: float = 0.55


@dataclass(frozen=True, slots=True)
class FrozenSweepInterpretation:
    inference: VisitInferenceA2
    indeterminacy_reason: IndeterminacyReasonA2
    target_support: float
    nuisance_support: float
    observation_support: float
    identifiability_margin: float
    both_supported: bool
    indirect_rescue: bool


def replicate_seed(coordinate_index: int, regime_index: int, replicate: int) -> int:
    if coordinate_index < 0 or regime_index < 0 or replicate < 0:
        raise ValueError("seed indices must be non-negative")
    if regime_index >= 10 or replicate >= 100:
        raise ValueError("frozen seed encoding requires regime<10 and replicate<100")
    return REPLICATE_SEED_BASE + coordinate_index * 1_000 + regime_index * 100 + replicate


def prototype_vectors(point: SpatiotemporalPoint) -> dict[LatentRegime, np.ndarray]:
    return {
        regime: np.mean(
            np.stack([signature_for(point, regime, seed=seed).vector() for seed in PROTOTYPE_SEEDS]),
            axis=0,
        )
        for regime in DEVIATION_REGIME_ORDER
    }


def margin_from_prototypes(
    signature: SpatiotemporalSignature,
    prototypes: Mapping[LatentRegime, np.ndarray],
) -> float:
    if set(prototypes) != set(DEVIATION_REGIME_ORDER):
        raise ValueError("prototype set must contain every frozen deviation regime exactly once")
    vector = signature.vector()
    distances = sorted(float(np.linalg.norm(vector - prototypes[regime])) for regime in DEVIATION_REGIME_ORDER)
    d1, d2 = distances[:2]
    # Exact best/second-best ties are maximal ambiguity, not maximal certainty.
    # V14a inherited the opposite edge-case convention; V14a2 fixes it before
    # any scientific result is generated.
    if d2 <= _EPS:
        return 0.0
    return float(np.clip((d2 - d1) / (d2 + _EPS), 0.0, 1.0))


def interpret_with_prototypes(
    point: SpatiotemporalPoint,
    regime: LatentRegime,
    *,
    seed: int,
    prototypes: Mapping[LatentRegime, np.ndarray],
    thresholds: FrozenThresholds,
) -> FrozenSweepInterpretation:
    target_truth, _, coupling_truth = truth(regime)
    signature = signature_for(point, regime, seed=seed)
    direct, indirect, nuisance = route_scores(signature)
    target = max(direct, indirect)
    support = observation_support(point, coupling_available=(coupling_truth or not target_truth))
    margin = margin_from_prototypes(signature, prototypes)

    if support < thresholds.support_minimum:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.INFORMATION_ABSENT
    elif margin < thresholds.ambiguity_margin:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.ESSENTIAL_AMBIGUITY
    elif target >= thresholds.target_high:
        inference = VisitInferenceA2.PRESENT
        reason = IndeterminacyReasonA2.NONE
    elif target <= thresholds.target_low and nuisance < thresholds.nuisance_high:
        inference = VisitInferenceA2.ABSENT
        reason = IndeterminacyReasonA2.NONE
    else:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.MODEL_UNCERTAINTY

    both = target >= thresholds.target_high and nuisance >= thresholds.nuisance_high
    rescue = inference is VisitInferenceA2.PRESENT and direct < thresholds.target_high and indirect >= thresholds.target_high
    return FrozenSweepInterpretation(
        inference=inference,
        indeterminacy_reason=reason,
        target_support=target,
        nuisance_support=nuisance,
        observation_support=support,
        identifiability_margin=margin,
        both_supported=both,
        indirect_rescue=rescue,
    )
