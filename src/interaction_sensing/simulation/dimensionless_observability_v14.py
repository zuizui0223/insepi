"""Dimensionless closed-world phase model for V14.

This is a development-world analyser, not a field classifier.  It keeps latent
`target` and `nuisance` processes non-exclusive, models a target-driven local
coupling response, and reports observability / identifiability separately from
nuisance burden.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi

import numpy as np


_EPS = 1e-12


class LatentRegime(str, Enum):
    BASELINE = "baseline"
    TARGET_ONLY = "target_only"
    NUISANCE_ONLY = "nuisance_only"
    COUPLED = "coupled"


class IndeterminacyReason(str, Enum):
    NONE = "none"
    INFORMATION_ABSENT = "information_absent"
    ESSENTIAL_AMBIGUITY = "essential_ambiguity"
    MODEL_UNCERTAINTY = "model_uncertainty"


class VisitInference(str, Enum):
    NO_QUERY = "no_query"
    PRESENT = "present"
    ABSENT = "absent"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True, slots=True)
class DimensionlessPoint:
    """The four V14 visitation coordinates.

    pi1 = observation window / target timescale
    pi2 = nuisance-or-flower-response timescale / target timescale
    pi3 = direct target amplitude / nuisance amplitude
    pi4 = target-driven local response amplitude / nuisance amplitude
    """

    pi1: float
    pi2: float
    pi3: float
    pi4: float

    def __post_init__(self) -> None:
        if self.pi1 <= 0 or self.pi2 <= 0:
            raise ValueError("pi1 and pi2 must be strictly positive")
        if self.pi3 < 0 or self.pi4 < 0:
            raise ValueError("pi3 and pi4 must be non-negative")


@dataclass(frozen=True, slots=True)
class ProcessSignature:
    net_displacement_over_path_length: float
    focal_neighbor_correlation: float
    spectral_concentration: float
    restoration_score: float
    entry_exit_completeness: float
    local_excess_motion_fraction: float
    direct_target_signal_fraction: float

    def vector(self) -> np.ndarray:
        return np.array(
            [
                self.net_displacement_over_path_length,
                self.focal_neighbor_correlation,
                self.spectral_concentration,
                self.restoration_score,
                self.entry_exit_completeness,
                self.local_excess_motion_fraction,
                self.direct_target_signal_fraction,
            ],
            dtype=float,
        )


@dataclass(frozen=True, slots=True)
class PhaseInterpretation:
    point: DimensionlessPoint
    latent_regime: LatentRegime
    signature: ProcessSignature
    direct_target_route: float
    indirect_target_route: float
    target_support: float
    nuisance_support: float
    observation_support: float
    closest_regime: LatentRegime | None
    identifiability_margin: float
    inference: VisitInference
    indeterminacy_reason: IndeterminacyReason
    both_target_and_nuisance_supported: bool
    indirect_target_rescue: bool


@dataclass(frozen=True, slots=True)
class PhaseDecisionThresholds:
    support_minimum: float = 0.20
    ambiguity_margin: float = 0.15
    target_high: float = 0.55
    target_low: float = 0.25
    nuisance_high: float = 0.55

    def __post_init__(self) -> None:
        for name, value in (
            ("support_minimum", self.support_minimum),
            ("ambiguity_margin", self.ambiguity_margin),
            ("target_high", self.target_high),
            ("target_low", self.target_low),
            ("nuisance_high", self.nuisance_high),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must lie in [0, 1]")
        if self.target_low >= self.target_high:
            raise ValueError("target_low must be below target_high")


def _rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(values))))


def _safe_abs_corr(a: np.ndarray, b: np.ndarray) -> float:
    if np.std(a) <= _EPS or np.std(b) <= _EPS:
        return 0.0
    value = float(np.corrcoef(a, b)[0, 1])
    if not np.isfinite(value):
        return 0.0
    return min(1.0, max(0.0, abs(value)))


def _restoration(values: np.ndarray) -> float:
    path = float(np.sum(np.abs(np.diff(values))))
    if path <= _EPS:
        return 0.0
    net = abs(float(values[-1] - values[0]))
    return min(1.0, max(0.0, 1.0 - net / path))


def _spectral_concentration(values: np.ndarray) -> float:
    centered = values - np.mean(values)
    power = np.abs(np.fft.rfft(centered)) ** 2
    if power.size <= 1:
        return 0.0
    power = power[1:]
    total = float(np.sum(power))
    if total <= _EPS:
        return 0.0
    return min(1.0, float(np.max(power) / total))


def _target_present(regime: LatentRegime) -> bool:
    return regime in {LatentRegime.TARGET_ONLY, LatentRegime.COUPLED}


def _nuisance_present(regime: LatentRegime) -> bool:
    return regime in {LatentRegime.NUISANCE_ONLY, LatentRegime.COUPLED}


def _signals(
    point: DimensionlessPoint,
    regime: LatentRegime,
    *,
    phase: float,
    samples: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    if samples < 16:
        raise ValueError("samples must be at least 16")

    half_window = point.pi1 / 2.0
    t = np.linspace(-half_window, half_window, samples, dtype=float)

    # Target process timescale is one.  The target enters at -0.5 and leaves at
    # +0.5.  A centered window shorter than one cannot contain both boundaries.
    active = (t >= -0.5) & (t <= 0.5)
    actor_position = np.zeros_like(t)
    actor_position[active] = t[active] + 0.5  # monotone 0 -> 1 transit
    actor_signal = np.zeros_like(t)
    if _target_present(regime):
        actor_signal[active] = point.pi3 * np.sin(pi * (t[active] + 0.5))

    global_nuisance = np.zeros_like(t)
    if _nuisance_present(regime):
        global_nuisance = np.sin((2.0 * pi / point.pi2) * t + phase)

    coupling = np.zeros_like(t)
    if _target_present(regime) and point.pi4 > 0:
        post = np.maximum(t, 0.0)
        triggered = t >= 0.0
        coupling[triggered] = (
            point.pi4
            * np.exp(-post[triggered] / max(2.0 * point.pi2, _EPS))
            * np.sin((2.0 * pi / point.pi2) * post[triggered])
        )

    focal_motion = global_nuisance + coupling
    neighbor_motion = global_nuisance.copy()
    observed_local = actor_signal + focal_motion

    event_left = max(-half_window, -0.5)
    event_right = min(half_window, 0.5)
    coverage = max(0.0, event_right - event_left)  # target duration is exactly 1
    entry_exit_completeness = min(1.0, coverage)
    return actor_position, observed_local, focal_motion, neighbor_motion, entry_exit_completeness


def _signature(
    point: DimensionlessPoint,
    regime: LatentRegime,
    *,
    phase: float,
    samples: int,
) -> ProcessSignature:
    actor_position, observed_local, focal, neighbor, completeness = _signals(
        point, regime, phase=phase, samples=samples
    )

    actor_path = float(np.sum(np.abs(np.diff(actor_position))))
    if actor_path <= _EPS or not _target_present(regime):
        transit_ratio = 0.0
    else:
        transit_ratio = min(1.0, abs(float(actor_position[-1] - actor_position[0])) / actor_path)

    focal_neighbor_corr = _safe_abs_corr(focal, neighbor)
    local_excess = _rms(focal - neighbor)
    scene_scale = _rms(focal) + _rms(neighbor) + _EPS
    local_excess_fraction = min(1.0, local_excess / scene_scale)

    # Direct target evidence competes with all local scene movement; this makes
    # pi3 an effective direct-route SNR coordinate without defining nuisance as
    # simply "not target".
    direct_component = observed_local - focal
    direct_rms = _rms(direct_component)
    scene_rms = _rms(focal)
    direct_fraction = min(1.0, direct_rms / (direct_rms + scene_rms + _EPS))

    return ProcessSignature(
        net_displacement_over_path_length=transit_ratio,
        focal_neighbor_correlation=focal_neighbor_corr,
        spectral_concentration=_spectral_concentration(focal),
        restoration_score=_restoration(focal),
        entry_exit_completeness=completeness if _target_present(regime) else 0.0,
        local_excess_motion_fraction=local_excess_fraction,
        direct_target_signal_fraction=direct_fraction,
    )


def _route_scores(signature: ProcessSignature) -> tuple[float, float, float]:
    direct = signature.direct_target_signal_fraction * (
        0.35 + 0.65 * signature.entry_exit_completeness
    )
    indirect = signature.local_excess_motion_fraction * (
        0.5 + 0.5 * signature.restoration_score
    )
    nuisance = signature.focal_neighbor_correlation * max(
        signature.restoration_score, signature.spectral_concentration
    )
    return (
        min(1.0, max(0.0, direct)),
        min(1.0, max(0.0, indirect)),
        min(1.0, max(0.0, nuisance)),
    )


def counterfactual_observation_support(point: DimensionlessPoint) -> float:
    """Support for observing a target *if one occurred* at this coordinate.

    This is deliberately independent of the realised nuisance classification.
    Direct spatial support can be weak while a target-driven local response still
    supplies an indirect route.
    """

    temporal_direct = min(1.0, point.pi1)
    direct = (point.pi3 / (1.0 + point.pi3)) * temporal_direct

    temporal_indirect = min(1.0, point.pi1 / max(point.pi2, _EPS))
    indirect = (point.pi4 / (1.0 + point.pi4)) * temporal_indirect
    return min(1.0, max(direct, indirect))


def _prototype_vector(point: DimensionlessPoint, regime: LatentRegime, samples: int) -> np.ndarray:
    phases = (0.0, 0.5 * pi, pi, 1.5 * pi)
    vectors = [_signature(point, regime, phase=p, samples=samples).vector() for p in phases]
    return np.mean(np.stack(vectors, axis=0), axis=0)


def model_relative_identifiability(
    point: DimensionlessPoint,
    signature: ProcessSignature,
    *,
    samples: int = 256,
) -> tuple[LatentRegime, float]:
    """Return nearest closed-world process prototype and a continuous margin.

    The margin is model-relative, not a claim that nature has a sharp ambiguity
    boundary.  A margin near zero means the first and second closest process
    prototypes are similarly compatible with the sufficient-statistic vector.
    """

    regimes = (LatentRegime.TARGET_ONLY, LatentRegime.NUISANCE_ONLY, LatentRegime.COUPLED)
    distances = []
    vector = signature.vector()
    for regime in regimes:
        prototype = _prototype_vector(point, regime, samples)
        distances.append((float(np.linalg.norm(vector - prototype)), regime))
    distances.sort(key=lambda item: (item[0], item[1].value))
    d1, best = distances[0]
    d2 = distances[1][0]
    margin = 1.0 if d2 <= _EPS and d1 <= _EPS else max(0.0, min(1.0, (d2 - d1) / (d2 + _EPS)))
    return best, margin


def analyse_phase_point(
    point: DimensionlessPoint,
    regime: LatentRegime,
    *,
    seed: int = 0,
    samples: int = 256,
    thresholds: PhaseDecisionThresholds | None = None,
) -> PhaseInterpretation:
    thresholds = thresholds or PhaseDecisionThresholds()
    if regime is LatentRegime.BASELINE:
        zero = ProcessSignature(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return PhaseInterpretation(
            point=point,
            latent_regime=regime,
            signature=zero,
            direct_target_route=0.0,
            indirect_target_route=0.0,
            target_support=0.0,
            nuisance_support=0.0,
            observation_support=counterfactual_observation_support(point),
            closest_regime=None,
            identifiability_margin=1.0,
            inference=VisitInference.NO_QUERY,
            indeterminacy_reason=IndeterminacyReason.NONE,
            both_target_and_nuisance_supported=False,
            indirect_target_rescue=False,
        )

    rng = np.random.default_rng(seed)
    phase = float(rng.uniform(0.0, 2.0 * pi))
    signature = _signature(point, regime, phase=phase, samples=samples)
    direct, indirect, nuisance = _route_scores(signature)
    target = max(direct, indirect)
    support = counterfactual_observation_support(point)
    closest, margin = model_relative_identifiability(point, signature, samples=samples)

    if support < thresholds.support_minimum:
        inference = VisitInference.UNDETERMINED
        reason = IndeterminacyReason.INFORMATION_ABSENT
    elif margin < thresholds.ambiguity_margin:
        inference = VisitInference.UNDETERMINED
        reason = IndeterminacyReason.ESSENTIAL_AMBIGUITY
    elif target >= thresholds.target_high:
        inference = VisitInference.PRESENT
        reason = IndeterminacyReason.NONE
    elif target <= thresholds.target_low and nuisance < thresholds.nuisance_high:
        inference = VisitInference.ABSENT
        reason = IndeterminacyReason.NONE
    else:
        inference = VisitInference.UNDETERMINED
        reason = IndeterminacyReason.MODEL_UNCERTAINTY

    both = target >= thresholds.target_high and nuisance >= thresholds.nuisance_high
    rescue = (
        inference is VisitInference.PRESENT
        and direct < thresholds.target_high
        and indirect >= thresholds.target_high
    )
    return PhaseInterpretation(
        point=point,
        latent_regime=regime,
        signature=signature,
        direct_target_route=direct,
        indirect_target_route=indirect,
        target_support=target,
        nuisance_support=nuisance,
        observation_support=support,
        closest_regime=closest,
        identifiability_margin=margin,
        inference=inference,
        indeterminacy_reason=reason,
        both_target_and_nuisance_supported=both,
        indirect_target_rescue=rescue,
    )
