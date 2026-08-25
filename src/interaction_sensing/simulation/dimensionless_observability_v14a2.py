"""V14a2 prefrozen spatiotemporal closed-world generator.

This module fixes the *design* required after the negative V14a Pi2 result.  It
adds an independent spatial correlation-length coordinate (Pi5) and an explicit
sampling coordinate (Pi6).  It is safe to unit-test construction invariants, but
this prefreeze generation must not run or inspect the registered full scientific
sweep until the exact prefreeze commit and protocol hash are recorded.

The generator preserves the V14 ontology: target T, exogenous nuisance N, and
target-driven coupling C are positive, non-exclusive processes; C implies T.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, floor, pi

import numpy as np

from .dimensionless_observability_v14 import LatentRegime

_EPS = 1e-12
_REFERENCE_DISTANCES = (1.0, 2.0, 4.0)
_PROTOTYPE_SEEDS = (101, 211, 307, 401)


class IndeterminacyReasonA2(str, Enum):
    NONE = "none"
    INFORMATION_ABSENT = "information_absent"
    ESSENTIAL_AMBIGUITY = "essential_ambiguity"
    MODEL_UNCERTAINTY = "model_uncertainty"


class VisitInferenceA2(str, Enum):
    NO_QUERY = "no_query"
    PRESENT = "present"
    ABSENT = "absent"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True, slots=True)
class SpatiotemporalPoint:
    pi1: float
    pi2: float
    pi3: float
    pi4: float
    pi5: float
    pi6: float

    def __post_init__(self) -> None:
        for name in ("pi1", "pi2", "pi5", "pi6"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be strictly positive")
        for name in ("pi3", "pi4"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    @property
    def samples_per_target_timescale(self) -> float:
        return self.pi6

    @property
    def samples_per_nuisance_timescale(self) -> float:
        return self.pi2 * self.pi6

    @property
    def nuisance_timescales_per_window(self) -> float:
        return self.pi1 / self.pi2


@dataclass(frozen=True, slots=True)
class SpatiotemporalSignature:
    net_displacement_over_path_length: float
    focal_reference_correlation: float
    spatial_coherence: float
    spatial_structure_function: float
    restoration_score: float
    spectral_concentration: float
    entry_exit_completeness: float
    local_excess_motion_fraction: float
    direct_target_signal_fraction: float
    target_sampling_support: float
    nuisance_sampling_support: float
    nuisance_window_support: float

    def vector(self) -> np.ndarray:
        return np.array(
            [
                self.net_displacement_over_path_length,
                self.focal_reference_correlation,
                self.spatial_coherence,
                self.spatial_structure_function,
                self.restoration_score,
                self.spectral_concentration,
                self.entry_exit_completeness,
                self.local_excess_motion_fraction,
                self.direct_target_signal_fraction,
                self.target_sampling_support,
                self.nuisance_sampling_support,
                self.nuisance_window_support,
            ],
            dtype=float,
        )


@dataclass(frozen=True, slots=True)
class SpatiotemporalInterpretation:
    point: SpatiotemporalPoint
    latent_regime: LatentRegime
    signature: SpatiotemporalSignature
    target_support: float
    nuisance_support: float
    observation_support: float
    identifiability_margin: float
    inference: VisitInferenceA2
    indeterminacy_reason: IndeterminacyReasonA2
    target_truth: bool
    nuisance_truth: bool
    coupling_truth: bool
    both_target_and_nuisance_supported: bool
    indirect_target_rescue: bool


def truth(regime: LatentRegime) -> tuple[bool, bool, bool]:
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
    raise ValueError(f"unsupported regime: {regime}")


def spatial_shared_weight(distance_target_widths: float, pi5: float) -> float:
    """Shared nuisance weight from an exponential spatial correlation kernel."""
    if distance_target_widths < 0 or pi5 <= 0:
        raise ValueError("distance must be non-negative and pi5 positive")
    return float(exp(-distance_target_widths / pi5))


def _time_grid(point: SpatiotemporalPoint) -> np.ndarray:
    # Pi6 controls the actual sample count.  Do not silently restore high temporal
    # resolution for low-Pi6 worlds: undersampling is part of the design.
    n = max(2, int(floor(point.pi1 * point.pi6)) + 1)
    return np.linspace(-point.pi1 / 2.0, point.pi1 / 2.0, n, dtype=float)


def _ou_process(rng: np.random.Generator, n: int, dt: float, timescale: float) -> np.ndarray:
    """Stationary discrete OU process with unit marginal variance."""
    a = float(np.exp(-dt / max(timescale, _EPS)))
    innovation = float(np.sqrt(max(0.0, 1.0 - a * a)))
    out = np.empty(n, dtype=float)
    out[0] = rng.normal()
    for idx in range(1, n):
        out[idx] = a * out[idx - 1] + innovation * rng.normal()
    return out


def nuisance_field(
    point: SpatiotemporalPoint,
    *,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return times, focal nuisance, and three reference-region nuisance traces.

    The focal trace is the shared temporal component.  A reference at distance d
    receives rho*shared + sqrt(1-rho^2)*local, rho=exp(-d/Pi5).  Thus Pi5 changes
    spatial statistical dependence rather than merely rescaling one identical
    waveform.
    """
    times = _time_grid(point)
    dt = float(times[1] - times[0])
    rng = np.random.default_rng(seed)
    shared = _ou_process(rng, len(times), dt, point.pi2)
    refs: list[np.ndarray] = []
    for distance in _REFERENCE_DISTANCES:
        rho = spatial_shared_weight(distance, point.pi5)
        local = _ou_process(rng, len(times), dt, point.pi2)
        refs.append(rho * shared + np.sqrt(max(0.0, 1.0 - rho * rho)) * local)
    return times, shared, np.stack(refs, axis=0)


def normalized_spatial_structure(focal: np.ndarray, reference: np.ndarray) -> float:
    """Amplitude-sensitive normalized structure function in [0,1].

    Unlike Pearson correlation, this changes when two traces have the same shape
    but different amplitudes.  Zero means identical traces; larger values mean
    stronger scale-sensitive spatial mismatch.
    """
    if focal.shape != reference.shape:
        raise ValueError("focal and reference must share shape")
    numerator = float(np.sqrt(np.mean(np.square(focal - reference))))
    denominator = (
        float(np.sqrt(np.mean(np.square(focal))))
        + float(np.sqrt(np.mean(np.square(reference))))
        + _EPS
    )
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def _abs_corr(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3 or np.std(a) <= _EPS or np.std(b) <= _EPS:
        return 0.0
    value = float(np.corrcoef(a, b)[0, 1])
    return 0.0 if not np.isfinite(value) else float(np.clip(abs(value), 0.0, 1.0))


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a)))) if len(a) else 0.0


def _restoration_score(a: np.ndarray) -> float:
    """Evidence that increments oppose displacement from the equilibrium."""
    if len(a) < 3 or np.std(a[:-1]) <= _EPS or np.std(np.diff(a)) <= _EPS:
        return 0.0
    value = float(np.corrcoef(a[:-1], -np.diff(a))[0, 1])
    return float(np.clip(value, 0.0, 1.0)) if np.isfinite(value) else 0.0


def _spectral_concentration(a: np.ndarray) -> float:
    if len(a) < 4:
        return 0.0
    centered = a - np.mean(a)
    power = np.abs(np.fft.rfft(centered)) ** 2
    if power.size <= 1:
        return 0.0
    power = power[1:]
    total = float(np.sum(power))
    return 0.0 if total <= _EPS else float(np.clip(np.max(power) / total, 0.0, 1.0))


def _target_components(
    point: SpatiotemporalPoint,
    times: np.ndarray,
    *,
    target_present: bool,
    coupling_present: bool,
) -> tuple[np.ndarray, np.ndarray, float, float]:
    actor = np.zeros_like(times)
    coupling = np.zeros_like(times)
    active = (times >= -0.5) & (times <= 0.5)
    if target_present:
        actor[active] = point.pi3 * np.sin(pi * (times[active] + 0.5))
    if coupling_present and point.pi4 > 0:
        post = np.maximum(times, 0.0)
        triggered = times >= 0.0
        coupling[triggered] = (
            point.pi4
            * np.exp(-post[triggered] / max(2.0 * point.pi2, _EPS))
            * np.sin((2.0 * pi / max(point.pi2, _EPS)) * post[triggered])
        )

    half = point.pi1 / 2.0
    event_left = max(-half, -0.5)
    event_right = min(half, 0.5)
    coverage = max(0.0, event_right - event_left)
    completeness = min(1.0, coverage) if target_present else 0.0

    active_times = times[active]
    if target_present and len(active_times) >= 2 and point.pi3 > 0:
        position = active_times + 0.5
        path = float(np.sum(np.abs(np.diff(position))))
        net = abs(float(position[-1] - position[0]))
        transit = 0.0 if path <= _EPS else float(np.clip(net / path, 0.0, 1.0))
    else:
        transit = 0.0
    return actor, coupling, completeness, transit


def sampling_support(point: SpatiotemporalPoint, minimum_samples: float = 8.0) -> tuple[float, float, float]:
    if minimum_samples <= 0:
        raise ValueError("minimum_samples must be positive")
    target = min(1.0, point.pi6 / minimum_samples)
    nuisance = min(1.0, point.samples_per_nuisance_timescale / minimum_samples)
    nuisance_window = min(1.0, point.nuisance_timescales_per_window)
    return target, nuisance, nuisance_window


def temporally_resolved(
    point: SpatiotemporalPoint,
    *,
    minimum_samples: float = 8.0,
    minimum_timescales_per_window: float = 1.0,
) -> bool:
    return (
        point.pi1 >= 1.0
        and point.pi6 >= minimum_samples
        and point.samples_per_nuisance_timescale >= minimum_samples
        and point.nuisance_timescales_per_window >= minimum_timescales_per_window
    )


def signature_for(
    point: SpatiotemporalPoint,
    regime: LatentRegime,
    *,
    seed: int,
) -> SpatiotemporalSignature:
    target_present, nuisance_present, coupling_present = truth(regime)
    times = _time_grid(point)

    if nuisance_present:
        times, focal_nuisance, references = nuisance_field(point, seed=seed)
    else:
        focal_nuisance = np.zeros_like(times)
        references = np.zeros((len(_REFERENCE_DISTANCES), len(times)), dtype=float)

    actor, coupling, completeness, transit = _target_components(
        point,
        times,
        target_present=target_present,
        coupling_present=coupling_present,
    )
    observed_focal = actor + focal_nuisance + coupling
    reference = np.median(references, axis=0)

    corr = _abs_corr(focal_nuisance, reference)
    structure = normalized_spatial_structure(focal_nuisance, reference)
    coherence = 1.0 - structure
    local_excess = normalized_spatial_structure(observed_focal, reference)
    direct_rms = _rms(actor)
    nuisance_rms = _rms(focal_nuisance + coupling)
    direct_fraction = direct_rms / (direct_rms + nuisance_rms + _EPS)
    target_sampling, nuisance_sampling, nuisance_window = sampling_support(point)

    return SpatiotemporalSignature(
        net_displacement_over_path_length=transit,
        focal_reference_correlation=corr,
        spatial_coherence=float(np.clip(coherence, 0.0, 1.0)),
        spatial_structure_function=structure,
        restoration_score=_restoration_score(focal_nuisance + coupling),
        spectral_concentration=_spectral_concentration(focal_nuisance + coupling),
        entry_exit_completeness=completeness,
        local_excess_motion_fraction=local_excess,
        direct_target_signal_fraction=float(np.clip(direct_fraction, 0.0, 1.0)),
        target_sampling_support=target_sampling,
        nuisance_sampling_support=nuisance_sampling,
        nuisance_window_support=nuisance_window,
    )


def route_scores(signature: SpatiotemporalSignature) -> tuple[float, float, float]:
    direct = (
        signature.direct_target_signal_fraction
        * (0.35 + 0.65 * signature.entry_exit_completeness)
        * signature.target_sampling_support
    )
    indirect = (
        signature.local_excess_motion_fraction
        * (0.5 + 0.5 * signature.restoration_score)
        * signature.target_sampling_support
    )
    nuisance = (
        signature.spatial_coherence
        * max(signature.restoration_score, signature.spectral_concentration)
        * min(signature.nuisance_sampling_support, signature.nuisance_window_support)
    )
    return tuple(float(np.clip(v, 0.0, 1.0)) for v in (direct, indirect, nuisance))


def observation_support(point: SpatiotemporalPoint) -> float:
    target_sampling, _, _ = sampling_support(point)
    window_support = min(1.0, point.pi1)
    amplitude_support = max(point.pi3 / (1.0 + point.pi3), point.pi4 / (1.0 + point.pi4))
    return float(np.clip(min(window_support, target_sampling, amplitude_support), 0.0, 1.0))


def _prototype_vector(point: SpatiotemporalPoint, regime: LatentRegime) -> np.ndarray:
    vectors = [signature_for(point, regime, seed=seed).vector() for seed in _PROTOTYPE_SEEDS]
    return np.mean(np.stack(vectors, axis=0), axis=0)


def identifiability_margin(
    point: SpatiotemporalPoint,
    signature: SpatiotemporalSignature,
) -> float:
    regimes = (
        LatentRegime.TARGET_ONLY,
        LatentRegime.NUISANCE_ONLY,
        LatentRegime.TARGET_COUPLED,
        LatentRegime.TARGET_NUISANCE_SUPERPOSED,
        LatentRegime.TARGET_NUISANCE_COUPLED,
    )
    vector = signature.vector()
    distances = sorted(
        float(np.linalg.norm(vector - _prototype_vector(point, regime)))
        for regime in regimes
    )
    d1, d2 = distances[:2]
    if d2 <= _EPS:
        return 1.0 if d1 <= _EPS else 0.0
    return float(np.clip((d2 - d1) / (d2 + _EPS), 0.0, 1.0))


def analyse_point(
    point: SpatiotemporalPoint,
    regime: LatentRegime,
    *,
    seed: int,
    support_minimum: float = 0.20,
    ambiguity_margin: float = 0.15,
    target_high: float = 0.55,
    target_low: float = 0.25,
    nuisance_high: float = 0.55,
) -> SpatiotemporalInterpretation:
    target_truth, nuisance_truth, coupling_truth = truth(regime)
    if regime is LatentRegime.BASELINE:
        zero = SpatiotemporalSignature(*(0.0 for _ in range(12)))
        return SpatiotemporalInterpretation(
            point, regime, zero, 0.0, 0.0, observation_support(point), 1.0,
            VisitInferenceA2.NO_QUERY, IndeterminacyReasonA2.NONE,
            False, False, False, False, False,
        )

    signature = signature_for(point, regime, seed=seed)
    direct, indirect, nuisance = route_scores(signature)
    target = max(direct, indirect)
    support = observation_support(point)
    margin = identifiability_margin(point, signature)

    if support < support_minimum:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.INFORMATION_ABSENT
    elif margin < ambiguity_margin:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.ESSENTIAL_AMBIGUITY
    elif target >= target_high:
        # Positive target evidence remains positive even with simultaneous nuisance.
        inference = VisitInferenceA2.PRESENT
        reason = IndeterminacyReasonA2.NONE
    elif target <= target_low and nuisance < nuisance_high:
        inference = VisitInferenceA2.ABSENT
        reason = IndeterminacyReasonA2.NONE
    else:
        inference = VisitInferenceA2.UNDETERMINED
        reason = IndeterminacyReasonA2.MODEL_UNCERTAINTY

    both = target >= target_high and nuisance >= nuisance_high
    rescue = inference is VisitInferenceA2.PRESENT and direct < target_high and indirect >= target_high
    return SpatiotemporalInterpretation(
        point=point,
        latent_regime=regime,
        signature=signature,
        target_support=target,
        nuisance_support=nuisance,
        observation_support=support,
        identifiability_margin=margin,
        inference=inference,
        indeterminacy_reason=reason,
        target_truth=target_truth,
        nuisance_truth=nuisance_truth,
        coupling_truth=coupling_truth,
        both_target_and_nuisance_supported=both,
        indirect_target_rescue=rescue,
    )
