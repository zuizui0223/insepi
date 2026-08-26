"""V14b nuisance-side observer with target observer frozen.

The V14a2 nuisance route had perfect rank ordering but a severe score-scale mismatch
because process evidence and observation support were multiplied into one scalar.
This generation restores the conceptual separation: nuisance process evidence is
built only from positive spatial/temporal process signatures, while sampling/window
support remains an independent observability quantity.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from .simulation.dimensionless_observability_v14a2 import SpatiotemporalSignature


@dataclass(frozen=True, slots=True)
class NuisanceObservationV14b:
    spatial_process_support: float
    temporal_process_support: float
    nuisance_process_support: float
    nuisance_observation_support: float

    def __post_init__(self) -> None:
        for value in (
            self.spatial_process_support,
            self.temporal_process_support,
            self.nuisance_process_support,
            self.nuisance_observation_support,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("all nuisance observation components must lie in [0,1]")


def observe_nuisance_v14b(signature: SpatiotemporalSignature) -> NuisanceObservationV14b:
    """Return positive nuisance-process evidence without folding in observability.

    Spatial coherence and restorative/stationary temporal structure are both
    positive nuisance-process properties. Their geometric mean keeps both required
    while avoiding the arbitrary shrinkage caused by multiplying a third,
    conceptually independent observation-support term into the nuisance score.
    """
    spatial = float(signature.spatial_coherence)
    temporal = float(max(signature.restoration_score, signature.spectral_concentration))
    process = sqrt(max(0.0, spatial * temporal))
    observation = float(min(signature.nuisance_sampling_support, signature.nuisance_window_support))
    return NuisanceObservationV14b(
        spatial_process_support=spatial,
        temporal_process_support=temporal,
        nuisance_process_support=process,
        nuisance_observation_support=observation,
    )
