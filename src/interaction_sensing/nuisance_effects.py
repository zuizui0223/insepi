"""Causal effect taxonomy for non-target processes in visit sensing.

A nuisance source is not defined by being 'not an insect'. It is defined by how
it can corrupt inference about the focal event. The same physical source may have
several effects, including loss of observation support. The latter is the V14
formalisation of a *censoring nuisance*: a disturbance capable of making the
interaction opportunity unobservable when sufficiently severe.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .noise import NoiseSource


class NuisanceEffect(str, Enum):
    MIMIC_TARGET = "mimic_target"
    MASK_TARGET = "mask_target"
    CORRUPT_ATTRIBUTION = "corrupt_attribution"
    DEGRADE_OBSERVATION_SUPPORT = "degrade_observation_support"


@dataclass(frozen=True, slots=True)
class NuisanceProfile:
    source: NoiseSource
    effects: frozenset[NuisanceEffect]

    @property
    def censoring_capable(self) -> bool:
        return NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT in self.effects


NUISANCE_PROFILES: dict[NoiseSource, NuisanceProfile] = {
    NoiseSource.STABLE_SCENE: NuisanceProfile(NoiseSource.STABLE_SCENE, frozenset()),
    NoiseSource.GLOBAL_CAMERA_SHAKE: NuisanceProfile(
        NoiseSource.GLOBAL_CAMERA_SHAKE,
        frozenset(
            {
                NuisanceEffect.MIMIC_TARGET,
                NuisanceEffect.MASK_TARGET,
                NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT,
            }
        ),
    ),
    NoiseSource.CO_MOVING_FOREGROUND: NuisanceProfile(
        NoiseSource.CO_MOVING_FOREGROUND,
        frozenset({NuisanceEffect.MIMIC_TARGET, NuisanceEffect.CORRUPT_ATTRIBUTION}),
    ),
    NoiseSource.BACKGROUND_VEGETATION_MOTION: NuisanceProfile(
        NoiseSource.BACKGROUND_VEGETATION_MOTION,
        frozenset({NuisanceEffect.MIMIC_TARGET, NuisanceEffect.CORRUPT_ATTRIBUTION}),
    ),
    NoiseSource.ILLUMINATION_TRANSIENT: NuisanceProfile(
        NoiseSource.ILLUMINATION_TRANSIENT,
        frozenset({NuisanceEffect.MIMIC_TARGET, NuisanceEffect.MASK_TARGET}),
    ),
    NoiseSource.SHADOW_TRANSIENT: NuisanceProfile(
        NoiseSource.SHADOW_TRANSIENT,
        frozenset({NuisanceEffect.MIMIC_TARGET, NuisanceEffect.MASK_TARGET}),
    ),
    NoiseSource.OCCLUSION: NuisanceProfile(
        NoiseSource.OCCLUSION,
        frozenset(
            {
                NuisanceEffect.MASK_TARGET,
                NuisanceEffect.CORRUPT_ATTRIBUTION,
                NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT,
            }
        ),
    ),
    NoiseSource.BLUR_OR_FOCUS_LOSS: NuisanceProfile(
        NoiseSource.BLUR_OR_FOCUS_LOSS,
        frozenset({NuisanceEffect.MASK_TARGET, NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT}),
    ),
    NoiseSource.LENS_CONTAMINATION: NuisanceProfile(
        NoiseSource.LENS_CONTAMINATION,
        frozenset({NuisanceEffect.MASK_TARGET, NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT}),
    ),
    NoiseSource.MULTI_OBJECT_CLUTTER: NuisanceProfile(
        NoiseSource.MULTI_OBJECT_CLUTTER,
        frozenset({NuisanceEffect.MIMIC_TARGET, NuisanceEffect.CORRUPT_ATTRIBUTION}),
    ),
    NoiseSource.UNKNOWN: NuisanceProfile(
        NoiseSource.UNKNOWN,
        frozenset(
            {
                NuisanceEffect.MIMIC_TARGET,
                NuisanceEffect.MASK_TARGET,
                NuisanceEffect.CORRUPT_ATTRIBUTION,
            }
        ),
    ),
}


def profile_for(source: NoiseSource) -> NuisanceProfile:
    return NUISANCE_PROFILES[source]
