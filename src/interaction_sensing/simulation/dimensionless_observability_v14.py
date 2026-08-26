"""Dimensionless closed-world phase model for V14.

This is a development-world analyser, not a field classifier. It keeps three
latent causes separate:

- T: focal target/event process;
- N: exogenous nuisance process;
- C: target-driven local scene response (C implies T).

The model reports target support, exogenous nuisance support, counterfactual
observability, and model-relative identifiability separately. It never defines
nuisance as "not target" and never defines unobservability as "high nuisance".
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import pi

import numpy as np


_EPS = 1e-12


class LatentRegime(str, Enum):
    BASELINE = "baseline"  # T=0,N=0,C=0
    TARGET_ONLY = "target_only"  # T=1,N=0,C=0
    NUISANCE_ONLY = "nuisance_only"  # T=0,N=1,C=0
    TARGET_COUPLED = "target_coupled"  # T=1,N=0,C=1
    TARGET_NUISANCE_SUPERPOSED = "target_nuisance_superposed"  # T=1,N=1,C=0
    TARGET_NUISANCE_COUPLED = "target_nuisance_coupled"  # T=1,N=1,C=1


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
    pi3 = direct target amplitude / reference nuisance amplitude
    pi4 = target-driven local response amplitude / reference nuisance amplitude
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
    exogenous_nuisance_support: float
    observation_support: float
    closest_regime: LatentRegime | None
    identifiability_margin: float
    inference: VisitInference
    indeterminacy_reason: IndeterminacyReason
    target_truth: bool
    exogenous_nuisance_truth: bool
    coupling_truth: bool
    both_target_and_nuisance_supported: bool
    indirect_target_rescue: bool


@dataclass(frozen=True, slots=True)
class PhaseDecisionThresholds:
    """Operational thresholds for the reference phase analyser.

    These are dimensionless development defaults. They are not physical field
    thresholds or calibrated visit probabilities.
    """

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


def _truth(regime: LatentRegime) -> tuple[bool, bool, bool]:
    if regime is LatentRegime.BASELINE:
        return False, False, False
    if regime is LatentRegime.TARGET_ONLY:
        return True, False, False
    if regime is LatentRegime.NUISANCE_ONLY:
        return False, True, False
    if regime is LatentRegime.TARGET_COUPLED:
        return True, False, True
    if regime is LatentRegime.TARGET_NUISANCE_SUPERPOSED:
        return True, True, False
    if regime is LatentRegime.TARGET_NUISANCE_COUPLED:
        return True, True, True
    raise ValueError(f"unsupported latent regime: {regime}")


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


def _signals(
    point: DimensionlessPoint,
    regime: LatentRegime,
    *,
    phase: float,
    samples: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]:
    if samples < 16:
        raise ValueError("samples must be at least 16")

    target_present, nuisance_present, coupling_present = _truth(regime)
    half_window = point.pi1 / 2.0
    t = np.linspace(-half_window, half_window, samples, dtype=float)

    # Target timescale is one. Entry and exit occur at -0.5 and +0.5.
    active = (t >= -0.5) & (t <= 0.5)
    actor_position = np.full_like(t, np.nan)
    actor_signal = np.zeros_like(t)
    if target_present:
        actor_position[active] = t[active] + 0.5
        actor_signal[active] = point.pi3 * np.sin(pi * (t[active] + 0.5))

    exogenous_nuisance = np.zeros_like(t)
    if nuisance_present:
        exogenous_nuisance = np.sin((2.0 * pi / point.pi2) * t + phase)

    coupling = np.zeros_like(t)
    if coupling_present and point.pi4 > 0:
        post = np.maximum(t, 0.0)
        triggered = t >= 0.0
        coupling[triggered] = (
            point.pi4
            * np.exp(-post[triggered] / max(2.0 * point.pi2, _EPS))
            * np.sin((2.0 * pi / point.pi2) * post[triggered])
        )

    focal_motion = exogenous_nuisance + coupling
    neighbor_motion = exogenous_nuisance.copy()
    observed_local = actor_signal + focal_motion

    event_left = max(-half_window, -0.5)
    event_right = min(half_window, 0.5)
    coverage = max(0.0, event_right - event_left)  # target duration = 1
    entry_exit_completeness = min(1.0, coverage) if target_present else 0.0

    finite_actor = actor_position[np.isfinite(actor_position)]
    if finite_actor.size < 2 or point.pi3 <= 0:
        transit_ratio = 0.0
    else:
        scaled = point.pi3 * finite_actor
        path = float(np.sum(np.abs(np.diff(scaled))))
        net = abs(float(scaled[-1] - scaled[0]))
        transit_ratio = 0.0 if path <= _EPS else min(1.0, net / path)

    return observed_local, focal_motion, neighbor_motion, actor_signal, entry_exit_completeness, transit_ratio


def _signature(
    point: DimensionlessPoint,
    regime: LatentRegime,
    *,
    phase: float,
    samples: int,
) -> ProcessSignature:
    observed_local, focal, neighbor, actor_signal, completeness, transit_ratio = _signals(
        point, regime, phase=phase, samples=samples
    )

    focal_neighbor_corr = _safe_abs_corr(focal, neighbor)
    local_excess = _rms(focal - neighbor)
    scene_scale = _rms(focal) + _rms(neighbor) + _EPS
    local_excess_fraction = min(1.0, local_excess / scene_scale)

    direct_rms = _rms(actor_signal)
    scene_rms = _rms(focal)
    direct_fraction = min(1.0, direct_rms / (direct_rms + scene_rms + _EPS))

    return ProcessSignature(
        net_displacement_over_path_length=transit_ratio,
        focal_neighbor_correlation=focal_neighbor_corr,
        spectral_concentration=_spectral_concentration(focal),
        restoration_score=_restoration(focal),
        entry_exit_completeness=completeness,
        local_excess_motion_fraction=local_excess_fraction,
        direct_target_signal_fraction=direct_fraction,
    )


def _route_scores(signature: ProcessSignature) -> tuple[float, float, float]:
    direct = signature.direct_target_signal_fraction * (
        0.35 + 0.65 * signature.entry_exit_completeness
    )
    # Local target-driven flower motion is allowed to be restorative: its causal
    # locality, not its "noise-like" oscillation alone, makes it a candidate
    # indirect target route.
    indirect = signature.local_excess_motion_fraction * (
        0.5 + 0.5 * signature.restoration_score
    )
    exogenous_nuisance = signature.focal_neighbor_correlation * max(
        signature.restoration_score, signature.spectral_concentration
    )
    return tuple(min(1.0, max(0.0, value)) for value in (direct, indirect, exogenous_nuisance))


def counterfactual_observation_support(
    point: DimensionlessPoint,
    *,
    coupling_available: bool = True,
) -> float:
    """Support for observing a target *if one occurred* at this coordinate.

    The direct route depends on pi1 and pi3. A second indirect route is available
    only when the physical target-to-scene coupling mechanism is part of the
    world under consideration. Neither route is defined as one minus nuisance.
    """

    temporal_direct = min(1.0, point.pi1)
    direct = (point.pi3 / (1.0 + point.pi3)) * temporal_direct

    indirect = 0.0
    if coupling_available:
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
    """Nearest closed-world process prototype and continuous separation margin.

    The margin is explicitly model-relative. It quantifies how distinct the best
    and second-best truth-known process prototypes are under the chosen sufficient
    statistics; it is not a claim that nature contains a sharp ambiguity class.
    """

    regimes = (
        LatentRegime.TARGET_ONLY,
        LatentRegime.NUISANCE_ONLY,
        LatentRegime.TARGET_COUPLED,
        LatentRegime.TARGET_NUISANCE_SUPERPOSED,
        LatentRegime.TARGET_NUISANCE_COUPLED,
    )
    vector = signature.vector()
    distances = [
        (float(np.linalg.norm(vector - _prototype_vector(point, regime, samples))), regime)
        for regime in regimes
    ]
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
    target_truth, nuisance_truth, coupling_truth = _truth(regime)

    if regime is LatentRegime.BASELINE:
        zero = ProcessSignature(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        return PhaseInterpretation(
            point=point,
            latent_regime=regime,
            signature=zero,
            direct_target_route=0.0,
            indirect_target_route=0.0,
            target_support=0.0,
            exogenous_nuisance_support=0.0,
            observation_support=counterfactual_observation_support(point, coupling_available=True),
            closest_regime=None,
            identifiability_margin=1.0,
            inference=VisitInference.NO_QUERY,
            indeterminacy_reason=IndeterminacyReason.NONE,
            target_truth=False,
            exogenous_nuisance_truth=False,
            coupling_truth=False,
            both_target_and_nuisance_supported=False,
            indirect_target_rescue=False,
        )

    rng = np.random.default_rng(seed)
    phase = float(rng.uniform(0.0, 2.0 * pi))
    signature = _signature(point, regime, phase=phase, samples=samples)
    direct, indirect, nuisance = _route_scores(signature)
    target = max(direct, indirect)

    # For an observed target world, only realised coupling is a valid indirect
    # route. For target-absent nuisance-only worlds, pi4 describes the
    # counterfactual response that would occur if a target event happened.
    coupling_available_for_support = coupling_truth or not target_truth
    support = counterfactual_observation_support(
        point, coupling_available=coupling_available_for_support
    )
    closest, margin = model_relative_identifiability(point, signature, samples=samples)

    if support < thresholds.support_minimum:
        inference = VisitInference.UNDETERMINED
        reason = IndeterminacyReason.INFORMATION_ABSENT
    elif margin < thresholds.ambiguity_margin:
        inference = VisitInference.UNDETERMINED
        reason = IndeterminacyReason.ESSENTIAL_AMBIGUITY
    elif target >= thresholds.target_high:
        # A target can be defensibly present even while exogenous nuisance is
        # also supported. Superposition is not itself an indeterminate outcome.
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
        exogenous_nuisance_support=nuisance,
        observation_support=support,
        closest_regime=closest,
        identifiability_margin=margin,
        inference=inference,
        indeterminacy_reason=reason,
        target_truth=target_truth,
        exogenous_nuisance_truth=nuisance_truth,
        coupling_truth=coupling_truth,
        both_target_and_nuisance_supported=both,
        indirect_target_rescue=rescue,
    )
