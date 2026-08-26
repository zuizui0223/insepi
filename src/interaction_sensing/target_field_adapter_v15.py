"""V15-v2 field adapter for PolliPi's ordinal target-evidence contract.

This adapter intentionally carries only *positive target evidence* into InsePi.
It does not import PolliPi at runtime and it never interprets a low score as
biological target absence, nuisance truth, observability, or confirmed visitation.

The accepted mapping mirrors the PolliPi main-branch ``target_evidence.py``
contract frozen in the accompanying V15 artifact:

- ``no_activity`` -> 0.0
- ``environmental_noise`` -> 0.0
- ``uncertain_local_activity`` -> 0.5
- ``strong_visitation_candidate`` -> 1.0

The coupled target-response route is deliberately not inferred here. It remains a
separate measurement/attribution path in :mod:`interaction_sensing.target_routes`.
"""
from __future__ import annotations

from dataclasses import dataclass

from .target_routes import TargetRouteEvidence


POLLIPI_ORDINAL_TARGET_SCALE = "ordinal-v14-reference"
POLLIPI_TARGET_EVIDENCE_MAPPING: dict[str, float] = {
    "no_activity": 0.0,
    "environmental_noise": 0.0,
    "uncertain_local_activity": 0.5,
    "strong_visitation_candidate": 1.0,
}


@dataclass(frozen=True, slots=True)
class PolliPiTargetEvidenceInput:
    """Dependency-free representation of PolliPi's portable target evidence."""

    source_state: str
    score: float
    scale: str = POLLIPI_ORDINAL_TARGET_SCALE
    confirmed_visit: bool = False

    def __post_init__(self) -> None:
        if self.source_state not in POLLIPI_TARGET_EVIDENCE_MAPPING:
            raise ValueError(f"unsupported PolliPi target-evidence state: {self.source_state!r}")
        expected = POLLIPI_TARGET_EVIDENCE_MAPPING[self.source_state]
        if float(self.score) != expected:
            raise ValueError(
                f"PolliPi state {self.source_state!r} requires frozen ordinal score {expected}"
            )
        if self.scale != POLLIPI_ORDINAL_TARGET_SCALE:
            raise ValueError("unsupported PolliPi target-evidence scale")
        if self.confirmed_visit:
            raise ValueError("PolliPi ordinal target evidence cannot certify visitation")


@dataclass(frozen=True, slots=True)
class V15DirectTargetFieldEvidence:
    """Positive-only direct route emitted to the V15 target-side interface."""

    direct_target_score: float
    source_state: str
    source_scale: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.direct_target_score <= 1.0:
            raise ValueError("direct_target_score must lie in [0, 1]")

    def to_target_routes(self) -> TargetRouteEvidence:
        """Create a direct-only route without inventing coupled evidence."""

        return TargetRouteEvidence(
            direct_insect_score=self.direct_target_score,
            coupled_response_score=0.0,
            target_link_confidence=0.0,
            source_state=f"pollipi:{self.source_state}",
        )


def adapt_pollipi_target_evidence(record: PolliPiTargetEvidenceInput) -> V15DirectTargetFieldEvidence:
    """Carry PolliPi ordinal evidence into V15 without negative inversion."""

    return V15DirectTargetFieldEvidence(
        direct_target_score=float(record.score),
        source_state=record.source_state,
        source_scale=record.scale,
    )
