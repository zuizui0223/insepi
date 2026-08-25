from interaction_sensing.noise import NoiseSource
from interaction_sensing.nuisance_effects import NuisanceEffect, profile_for


def test_stable_context_is_not_nuisance_by_definition() -> None:
    profile = profile_for(NoiseSource.STABLE_SCENE)
    assert profile.effects == frozenset()
    assert profile.censoring_capable is False


def test_background_motion_can_be_nuisance_without_being_censoring_capable() -> None:
    profile = profile_for(NoiseSource.BACKGROUND_VEGETATION_MOTION)
    assert NuisanceEffect.MIMIC_TARGET in profile.effects
    assert NuisanceEffect.CORRUPT_ATTRIBUTION in profile.effects
    assert profile.censoring_capable is False


def test_occlusion_is_censoring_capable_but_not_automatically_unobservable() -> None:
    profile = profile_for(NoiseSource.OCCLUSION)
    assert NuisanceEffect.MASK_TARGET in profile.effects
    assert NuisanceEffect.DEGRADE_OBSERVATION_SUPPORT in profile.effects
    assert profile.censoring_capable is True


def test_blur_and_lens_contamination_are_support_degrading_nuisances() -> None:
    for source in (NoiseSource.BLUR_OR_FOCUS_LOSS, NoiseSource.LENS_CONTAMINATION):
        profile = profile_for(source)
        assert profile.censoring_capable is True
        assert NuisanceEffect.MASK_TARGET in profile.effects
