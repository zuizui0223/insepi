import numpy as np
import pytest

from interaction_sensing.coupled_field_measurement_v15 import (
    CoupledAttributionSource,
    CoupledResponseReferenceLayout,
    IndependentAttributionCue,
    measure_field_coupled_response,
)
from interaction_sensing.domain import BBox


HEX_A = "a" * 64
HEX_B = "b" * 64


def _frames(*, focal_only: bool) -> np.ndarray:
    frames = np.zeros((6, 8, 8), dtype=np.float64)
    # Focal region 0:4 x 0:4 changes through time.
    for t in range(frames.shape[0]):
        frames[t, 0:4, 0:4] = float(t * 20)
        if not focal_only:
            frames[t, 4:8, 4:8] = float(t * 20)
    return frames


def _layout() -> CoupledResponseReferenceLayout:
    return CoupledResponseReferenceLayout(
        reference_zones=(BBox(4, 4, 8, 8),),
        method="geometry_prebound_neighbour",
    )


def _cue(window_id: str = "w1", score: float = 0.8) -> IndependentAttributionCue:
    return IndependentAttributionCue(
        window_id=window_id,
        score=score,
        source=CoupledAttributionSource.CONTACT_GEOMETRY,
        source_id="contact-geometry-v1",
        evidence_sha256=HEX_A,
        calibration_sha256=HEX_B,
    )


def test_local_focal_response_without_independent_attribution_remains_unusable() -> None:
    result = measure_field_coupled_response(
        _frames(focal_only=True),
        window_id="w1",
        focal_zone=BBox(0, 0, 4, 4),
        reference_layout=_layout(),
    )
    assert result.coupled_response_score > 0.0
    assert result.local_response_excess > 0.0
    assert result.target_link_confidence == 0.0
    assert result.usable_coupled_target_score == 0.0
    assert result.to_target_routes().coupled_target_score == 0.0


def test_independent_attribution_cue_unlocks_only_the_multiplicative_coupled_route() -> None:
    result = measure_field_coupled_response(
        _frames(focal_only=True),
        window_id="w1",
        focal_zone=BBox(0, 0, 4, 4),
        reference_layout=_layout(),
        attribution_cue=_cue(score=0.8),
    )
    assert result.coupled_response_score > 0.0
    assert result.target_link_confidence == 0.8
    assert result.usable_coupled_target_score == pytest.approx(result.coupled_response_score * 0.8)
    routes = result.to_target_routes(direct_target_score=0.5)
    assert routes.direct_insect_score == 0.5
    assert routes.coupled_target_score == pytest.approx(result.usable_coupled_target_score)


def test_shared_scene_motion_is_not_promoted_to_local_coupled_response() -> None:
    result = measure_field_coupled_response(
        _frames(focal_only=False),
        window_id="w1",
        focal_zone=BBox(0, 0, 4, 4),
        reference_layout=_layout(),
        attribution_cue=_cue(),
    )
    assert result.local_response_excess == pytest.approx(0.0)
    assert result.coupled_response_score == pytest.approx(0.0)
    assert result.usable_coupled_target_score == pytest.approx(0.0)


def test_attribution_cue_must_match_window_and_have_prevalidated_source_contract() -> None:
    with pytest.raises(ValueError, match="window_id"):
        measure_field_coupled_response(
            _frames(focal_only=True),
            window_id="w1",
            focal_zone=BBox(0, 0, 4, 4),
            reference_layout=_layout(),
            attribution_cue=_cue(window_id="w2"),
        )

    with pytest.raises(TypeError, match="CoupledAttributionSource"):
        IndependentAttributionCue(
            window_id="w1",
            score=0.5,
            source="pollipi",  # type: ignore[arg-type]
            source_id="forbidden-copy",
            evidence_sha256=HEX_A,
            calibration_sha256=HEX_B,
        )
