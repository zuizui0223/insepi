"""V14 development benchmark for target–nuisance–observability semantics.

This benchmark is intentionally abstract. It tests whether an explicit
observation-support axis changes *what can be inferred from a non-detection*.
It does not model field pollinator accuracy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from interaction_sensing.observation_triad import (
    NuisanceEvidence,
    ObservationSupport,
    ObservationTriadPolicy,
    TargetEvidence,
)
from interaction_sensing.visit_observation import (
    VisitObservationStatus,
    visit_record_from_interpretation,
)


SUPPORT_LEVELS = {
    "observable": 0.90,
    "compromised": 0.50,
    "unobservable": 0.10,
}
NUISANCE_MECHANISMS = ("clean", "mimic", "mask", "attribution", "support_loss")
SUPPORT_STATES = tuple(SUPPORT_LEVELS)
POLICIES = ("target_only", "target_plus_nuisance", "triad")


@dataclass(frozen=True, slots=True)
class SimulatedVisitWindow:
    visit_truth: bool
    nuisance_mechanism: str
    support_truth: str
    target_score: float
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float
    support_score: float


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    status: VisitObservationStatus
    denominator_eligible: bool


@dataclass(frozen=True, slots=True)
class MetricSummary:
    policy: str
    false_absence_rate_among_true_visits: float
    false_positive_candidate_rate_among_true_absences: float
    unobservable_denominator_contamination: float
    observable_opportunity_retention: float
    observable_true_visit_candidate_recall: float
    unobservable_censor_recall: float


def _clip(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _nuisance_centres(mechanism: str) -> tuple[float, float, float]:
    return {
        "clean": (0.05, 0.05, 0.05),
        "mimic": (0.80, 0.15, 0.25),
        "mask": (0.10, 0.80, 0.30),
        "attribution": (0.15, 0.20, 0.85),
        # A support-degrading physical process need not itself produce a very
        # large nuisance risk. This is the deliberate low-nuisance/unobservable
        # case that a two-axis target+nuisance system cannot identify safely.
        "support_loss": (0.10, 0.35, 0.20),
    }[mechanism]


def simulate_window(
    rng: np.random.Generator,
    *,
    visit_truth: bool,
    nuisance_mechanism: str,
    support_truth: str,
) -> SimulatedVisitWindow:
    """Generate one abstract observation while keeping the three latent axes distinct."""

    if nuisance_mechanism not in NUISANCE_MECHANISMS:
        raise ValueError(f"unknown nuisance mechanism: {nuisance_mechanism}")
    if support_truth not in SUPPORT_LEVELS:
        raise ValueError(f"unknown support state: {support_truth}")

    target = 0.84 if visit_truth else 0.10
    if visit_truth:
        target += {"observable": 0.0, "compromised": -0.22, "unobservable": -0.52}[support_truth]
        target += {
            "clean": 0.0,
            "mimic": 0.02,
            "mask": -0.36,
            "attribution": -0.02,
            "support_loss": -0.22,
        }[nuisance_mechanism]
    else:
        target += {
            "clean": 0.0,
            "mimic": 0.52,
            "mask": 0.0,
            "attribution": 0.10,
            "support_loss": 0.0,
        }[nuisance_mechanism]

    target_score = _clip(target + rng.normal(0.0, 0.10))
    f0, m0, a0 = _nuisance_centres(nuisance_mechanism)
    false_risk = _clip(f0 + rng.normal(0.0, 0.08))
    missed_risk = _clip(m0 + rng.normal(0.0, 0.08))
    attribution_risk = _clip(a0 + rng.normal(0.0, 0.08))
    support_score = _clip(SUPPORT_LEVELS[support_truth] + rng.normal(0.0, 0.06))

    return SimulatedVisitWindow(
        visit_truth=visit_truth,
        nuisance_mechanism=nuisance_mechanism,
        support_truth=support_truth,
        target_score=target_score,
        false_event_risk=false_risk,
        missed_event_risk=missed_risk,
        attribution_risk=attribution_risk,
        support_score=support_score,
    )


def generate_world(seed: int, windows_per_cell: int) -> tuple[SimulatedVisitWindow, ...]:
    if windows_per_cell <= 0:
        raise ValueError("windows_per_cell must be positive")
    rng = np.random.default_rng(seed)
    rows: list[SimulatedVisitWindow] = []
    for visit_truth in (False, True):
        for nuisance in NUISANCE_MECHANISMS:
            for support_truth in SUPPORT_STATES:
                for _ in range(windows_per_cell):
                    rows.append(
                        simulate_window(
                            rng,
                            visit_truth=visit_truth,
                            nuisance_mechanism=nuisance,
                            support_truth=support_truth,
                        )
                    )
    return tuple(rows)


def _target_only(row: SimulatedVisitWindow) -> PolicyDecision:
    if row.target_score >= 0.65:
        status = VisitObservationStatus.VISIT_CANDIDATE
    elif row.target_score <= 0.25:
        status = VisitObservationStatus.OBSERVABLE_NONDETECTION
    else:
        status = VisitObservationStatus.AMBIGUOUS
    return PolicyDecision(status=status, denominator_eligible=True)


def _target_plus_nuisance(row: SimulatedVisitWindow) -> PolicyDecision:
    if row.target_score >= 0.65 and row.false_event_risk < 0.60 and row.attribution_risk < 0.60:
        status = VisitObservationStatus.VISIT_CANDIDATE
    elif row.target_score <= 0.25 and row.missed_event_risk < 0.60:
        status = VisitObservationStatus.OBSERVABLE_NONDETECTION
    else:
        status = VisitObservationStatus.CONFLICT_AUDIT
    return PolicyDecision(status=status, denominator_eligible=row.missed_event_risk < 0.60)


def _triad(row: SimulatedVisitWindow) -> PolicyDecision:
    interpretation = ObservationTriadPolicy().decide(
        TargetEvidence(row.target_score),
        NuisanceEvidence(
            row.false_event_risk,
            row.missed_event_risk,
            row.attribution_risk,
            dominant_source=row.nuisance_mechanism,
        ),
        ObservationSupport(
            row.support_score,
            row.support_score,
            row.support_score,
            row.support_score,
            row.support_score,
        ),
    )
    record = visit_record_from_interpretation("sim", 1.0, interpretation)
    return PolicyDecision(record.status, record.denominator_eligible)


def decide(policy: str, row: SimulatedVisitWindow) -> PolicyDecision:
    if policy == "target_only":
        return _target_only(row)
    if policy == "target_plus_nuisance":
        return _target_plus_nuisance(row)
    if policy == "triad":
        return _triad(row)
    raise ValueError(f"unknown policy: {policy}")


def _rate(flags: Iterable[bool]) -> float:
    values = tuple(bool(value) for value in flags)
    return float("nan") if not values else sum(values) / len(values)


def evaluate_policy(policy: str, world: tuple[SimulatedVisitWindow, ...]) -> MetricSummary:
    paired = tuple((row, decide(policy, row)) for row in world)
    true_visits = tuple(item for item in paired if item[0].visit_truth)
    true_absences = tuple(item for item in paired if not item[0].visit_truth)
    unobservable = tuple(item for item in paired if item[0].support_truth == "unobservable")
    observable = tuple(item for item in paired if item[0].support_truth == "observable")
    observable_visits = tuple(item for item in observable if item[0].visit_truth)

    return MetricSummary(
        policy=policy,
        false_absence_rate_among_true_visits=_rate(
            decision.status is VisitObservationStatus.OBSERVABLE_NONDETECTION
            for _, decision in true_visits
        ),
        false_positive_candidate_rate_among_true_absences=_rate(
            decision.status is VisitObservationStatus.VISIT_CANDIDATE
            for _, decision in true_absences
        ),
        unobservable_denominator_contamination=_rate(
            decision.denominator_eligible for _, decision in unobservable
        ),
        observable_opportunity_retention=_rate(
            decision.denominator_eligible for _, decision in observable
        ),
        observable_true_visit_candidate_recall=_rate(
            decision.status is VisitObservationStatus.VISIT_CANDIDATE
            for _, decision in observable_visits
        ),
        unobservable_censor_recall=_rate(
            decision.status is VisitObservationStatus.CENSORED_UNOBSERVABLE
            for _, decision in unobservable
        ),
    )


def diagnostic_slice(world: tuple[SimulatedVisitWindow, ...], policy: str, name: str) -> dict[str, float]:
    if name == "low_nuisance_unobservable":
        rows = tuple(row for row in world if row.nuisance_mechanism == "clean" and row.support_truth == "unobservable")
    elif name == "high_nuisance_observable":
        rows = tuple(row for row in world if row.nuisance_mechanism in {"mimic", "attribution"} and row.support_truth == "observable")
    elif name == "masking_observable":
        rows = tuple(row for row in world if row.nuisance_mechanism == "mask" and row.support_truth == "observable")
    elif name == "support_loss_low_target":
        rows = tuple(row for row in world if row.nuisance_mechanism == "support_loss" and row.support_truth == "unobservable" and row.visit_truth)
    else:
        raise ValueError(f"unknown diagnostic slice: {name}")

    paired = tuple((row, decide(policy, row)) for row in rows)
    return {
        "n": float(len(paired)),
        "false_absence_rate": _rate(
            decision.status is VisitObservationStatus.OBSERVABLE_NONDETECTION
            for row, decision in paired
            if row.visit_truth
        ),
        "denominator_eligible_rate": _rate(decision.denominator_eligible for _, decision in paired),
        "censor_rate": _rate(
            decision.status is VisitObservationStatus.CENSORED_UNOBSERVABLE
            for _, decision in paired
        ),
        "candidate_rate": _rate(
            decision.status is VisitObservationStatus.VISIT_CANDIDATE
            for _, decision in paired
        ),
    }
