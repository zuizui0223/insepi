import pytest

from interaction_sensing.v15_split_manifest import (
    TRUTH_LAYERS,
    V15ManifestWindow,
    V15Split,
    validate_v15_split_manifest,
)


HEX_A = "a" * 64
HEX_B = "b" * 64


def row(
    index: int,
    *,
    cluster: str,
    day: str,
    scene: str,
    split: V15Split,
    double: tuple[str, ...] = TRUTH_LAYERS,
) -> V15ManifestWindow:
    return V15ManifestWindow(
        window_id=f"w{index}",
        cluster_id=cluster,
        recording_day=day,
        focal_scene_id=scene,
        split=split,
        primary_clip_sha256=HEX_A,
        reference_clip_sha256=HEX_B,
        double_annotation_layers=double,
    )


def test_valid_manifest_requires_new_days_new_scenes_and_cluster_separation() -> None:
    rows = [
        row(1, cluster="d1-s1", day="d1", scene="s1", split=V15Split.DEVELOPMENT),
        row(2, cluster="d1-s1", day="d1", scene="s1", split=V15Split.DEVELOPMENT),
        row(3, cluster="d2-s2", day="d2", scene="s2", split=V15Split.HELD_OUT),
        row(4, cluster="d2-s2", day="d2", scene="s2", split=V15Split.HELD_OUT),
    ]
    summary = validate_v15_split_manifest(rows)
    assert summary.n_windows == 4
    assert summary.development_clusters == 1
    assert summary.held_out_clusters == 1


def test_cluster_cannot_cross_split() -> None:
    rows = [
        row(1, cluster="c1", day="d1", scene="s1", split=V15Split.DEVELOPMENT),
        row(2, cluster="c1", day="d2", scene="s2", split=V15Split.HELD_OUT),
    ]
    with pytest.raises(ValueError, match="cluster crosses"):
        validate_v15_split_manifest(rows)


def test_heldout_day_and_scene_must_both_be_new() -> None:
    rows_day_leak = [
        row(1, cluster="c1", day="d1", scene="s1", split=V15Split.DEVELOPMENT),
        row(2, cluster="c2", day="d1", scene="s2", split=V15Split.HELD_OUT),
    ]
    with pytest.raises(ValueError, match="recording days"):
        validate_v15_split_manifest(rows_day_leak)

    rows_scene_leak = [
        row(3, cluster="c3", day="d3", scene="shared", split=V15Split.DEVELOPMENT),
        row(4, cluster="c4", day="d4", scene="shared", split=V15Split.HELD_OUT),
    ]
    with pytest.raises(ValueError, match="focal scenes"):
        validate_v15_split_manifest(rows_scene_leak)


def test_each_truth_layer_needs_twenty_percent_double_annotation_within_each_cluster() -> None:
    rows = [
        row(
            i,
            cluster="dev",
            day="d1",
            scene="s1",
            split=V15Split.DEVELOPMENT,
            double=TRUTH_LAYERS if i == 1 else (),
        )
        for i in range(1, 6)
    ] + [
        row(
            i,
            cluster="held",
            day="d2",
            scene="s2",
            split=V15Split.HELD_OUT,
            double=TRUTH_LAYERS if i == 6 else (),
        )
        for i in range(6, 11)
    ]
    validate_v15_split_manifest(rows)

    broken = list(rows)
    broken[0] = row(
        1,
        cluster="dev",
        day="d1",
        scene="s1",
        split=V15Split.DEVELOPMENT,
        double=tuple(layer for layer in TRUTH_LAYERS if layer != "nuisance"),
    )
    with pytest.raises(ValueError, match="nuisance.*below"):
        validate_v15_split_manifest(broken)


def test_duplicate_window_and_unknown_annotation_layer_fail_closed() -> None:
    with pytest.raises(ValueError, match="unknown double-annotation"):
        row(
            1,
            cluster="c1",
            day="d1",
            scene="s1",
            split=V15Split.DEVELOPMENT,
            double=("invented",),
        )

    rows = [
        row(1, cluster="c1", day="d1", scene="s1", split=V15Split.DEVELOPMENT),
        V15ManifestWindow(
            window_id="w1",
            cluster_id="c2",
            recording_day="d2",
            focal_scene_id="s2",
            split=V15Split.HELD_OUT,
            primary_clip_sha256=HEX_A,
            reference_clip_sha256=HEX_B,
            double_annotation_layers=TRUTH_LAYERS,
        ),
    ]
    with pytest.raises(ValueError, match="window_id values must be unique"):
        validate_v15_split_manifest(rows)
