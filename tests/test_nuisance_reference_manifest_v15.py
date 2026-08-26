import pytest

from interaction_sensing.domain import BBox
from interaction_sensing.nuisance_reference_manifest_v15 import (
    NuisanceReferenceManifestEntry,
    validate_nuisance_reference_manifest,
)


HEX = "a" * 64


def entry(window_id: str = "w1") -> NuisanceReferenceManifestEntry:
    return NuisanceReferenceManifestEntry(
        window_id=window_id,
        primary_clip_sha256=HEX,
        focal_zone=BBox(10, 10, 20, 20),
        reference_zones=(BBox(0, 0, 8, 8), BBox(22, 22, 30, 30)),
        selection_method="geometry_prefrozen_neighbor_context_v1",
    )


def test_manifest_binds_disjoint_reference_zones_before_scoring() -> None:
    row = entry()
    layout = row.to_reference_layout()
    assert layout.reference_zones == row.reference_zones
    assert layout.method == "geometry_prefrozen_neighbor_context_v1"
    assert validate_nuisance_reference_manifest([row]) == (row,)


def test_manifest_rejects_post_scoring_or_output_guided_reference_selection() -> None:
    kwargs = dict(
        window_id="w1",
        primary_clip_sha256=HEX,
        focal_zone=BBox(10, 10, 20, 20),
        reference_zones=(BBox(0, 0, 8, 8),),
        selection_method="bad",
    )
    with pytest.raises(ValueError, match="before model scoring"):
        NuisanceReferenceManifestEntry(**kwargs, selected_before_model_scoring=False)
    with pytest.raises(ValueError, match="target observer output"):
        NuisanceReferenceManifestEntry(**kwargs, used_target_observer_output=True)
    with pytest.raises(ValueError, match="nuisance observer output"):
        NuisanceReferenceManifestEntry(**kwargs, used_nuisance_observer_output=True)
    with pytest.raises(ValueError, match="biological/nuisance truth"):
        NuisanceReferenceManifestEntry(**kwargs, used_biological_or_nuisance_truth=True)


def test_manifest_rejects_reference_overlap_bad_hash_and_duplicate_window_ids() -> None:
    with pytest.raises(ValueError, match="spatially disjoint"):
        NuisanceReferenceManifestEntry(
            window_id="w1",
            primary_clip_sha256=HEX,
            focal_zone=BBox(10, 10, 20, 20),
            reference_zones=(BBox(15, 15, 25, 25),),
            selection_method="overlap",
        )
    with pytest.raises(ValueError, match="64-hex"):
        NuisanceReferenceManifestEntry(
            window_id="w1",
            primary_clip_sha256="not-a-hash",
            focal_zone=BBox(10, 10, 20, 20),
            reference_zones=(BBox(0, 0, 8, 8),),
            selection_method="bad-hash",
        )
    with pytest.raises(ValueError, match="window_id values must be unique"):
        validate_nuisance_reference_manifest([entry("w1"), entry("w1")])
