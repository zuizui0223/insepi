"""Deterministic V13 physical-phase measurement helpers.

This module contains no physical treatment truth and no observer implementation.
It defines how already-decoded native frames and already-emitted observer outputs
become block-level paired causal responses.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping, Sequence

import numpy as np

from interaction_sensing.simulation.real_video_v10 import canonicalize_rgb24

SAMPLE_NATIVE_FRAME_INDICES = (75, 105, 135, 165, 195, 225, 255, 285)
CANONICAL_SHAPE = (96, 128)
EVIDENCE_SCORE = {
    "strong_visitation_candidate": 1.0,
    "uncertain_local_activity": 0.7,
    "environmental_noise": 0.0,
    "no_activity": 0.0,
}


@dataclass(frozen=True, slots=True)
class PhaseSummary:
    evidence: float
    observability: float
    sample_count: int


@dataclass(frozen=True, slots=True)
class PairedResponse:
    delta_evidence: float
    delta_observability: float


def canonicalize_sampled_rgb24(frames: Sequence[np.ndarray]) -> tuple[np.ndarray, ...]:
    if len(frames) != len(SAMPLE_NATIVE_FRAME_INDICES):
        raise ValueError(f"V13 phase requires exactly 8 sampled frames, got {len(frames)}")
    return tuple(canonicalize_rgb24(frame) for frame in frames)


def placebo_background(placebo_frames: Sequence[np.ndarray]) -> np.ndarray:
    if len(placebo_frames) != 8:
        raise ValueError("V13 placebo background requires exactly eight canonical frames")
    stack = np.stack([np.asarray(frame) for frame in placebo_frames], axis=0)
    if stack.shape != (8, 96, 128) or stack.dtype != np.uint8:
        raise ValueError(f"expected eight 96x128 uint8 placebo frames, got {stack.shape} {stack.dtype}")
    ordered = np.sort(stack, axis=0)
    lower = ordered[3].astype(np.uint16)
    upper = ordered[4].astype(np.uint16)
    median = ((lower + upper + 1) // 2).astype(np.uint8)
    if median.shape != CANONICAL_SHAPE:
        raise AssertionError("V13 background shape changed")
    return median


def background_sha256(background: np.ndarray) -> str:
    array = np.asarray(background)
    if array.shape != CANONICAL_SHAPE or array.dtype != np.uint8:
        raise ValueError("V13 background hash requires 96x128 uint8")
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def evidence_score(pollipi_state: str) -> float:
    try:
        return float(EVIDENCE_SCORE[str(pollipi_state)])
    except KeyError as exc:
        raise ValueError(f"unknown frozen biological-evidence state: {pollipi_state}") from exc


def observability_risk(
    false_event_risk: float,
    missed_event_risk: float,
    attribution_risk: float,
) -> float:
    values = tuple(map(float, (false_event_risk, missed_event_risk, attribution_risk)))
    if any((not np.isfinite(value) or value < 0.0 or value > 1.0) for value in values):
        raise ValueError(f"invalid observability risk tuple: {values}")
    return max(values)


def phase_summary(
    pollipi_rows: Sequence[Mapping[str, object]],
    insepi_rows: Sequence[Mapping[str, object]],
) -> PhaseSummary:
    if len(pollipi_rows) != 8 or len(insepi_rows) != 8:
        raise ValueError("V13 phase summary requires eight rows from each observer")
    evidence = [evidence_score(str(row["pollipi_state"])) for row in pollipi_rows]
    observability = [
        observability_risk(
            float(row["false_event_risk"]),
            float(row["missed_event_risk"]),
            float(row["attribution_risk"]),
        )
        for row in insepi_rows
    ]
    return PhaseSummary(
        evidence=float(np.median(np.asarray(evidence, dtype=float))),
        observability=float(np.median(np.asarray(observability, dtype=float))),
        sample_count=8,
    )


def paired_response(placebo: PhaseSummary, active: PhaseSummary) -> PairedResponse:
    if placebo.sample_count != 8 or active.sample_count != 8:
        raise ValueError("V13 paired response requires complete eight-sample phase summaries")
    return PairedResponse(
        delta_evidence=float(active.evidence - placebo.evidence),
        delta_observability=float(active.observability - placebo.observability),
    )


def build_block_responses(
    phase_summaries: Mapping[str, PhaseSummary],
) -> dict[str, tuple[float, float]]:
    required = {"placebo", "event_restore", "observability_restore", "shared_restore"}
    if set(phase_summaries) != required:
        raise ValueError(f"V13 block must contain exactly {sorted(required)}")
    placebo = phase_summaries["placebo"]
    output: dict[str, tuple[float, float]] = {}
    for intervention in ("event_restore", "observability_restore", "shared_restore"):
        delta = paired_response(placebo, phase_summaries[intervention])
        output[intervention] = (delta.delta_evidence, delta.delta_observability)
    return output
