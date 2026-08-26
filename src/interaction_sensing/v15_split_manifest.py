"""Fail-closed split/blinding manifest validation for V15-v2.

The validator does not invent a development/held-out allocation. It validates a
realised manifest before scoring and prevents frame-level leakage across the same
biological recording structure.

V15-v2 requires held-out data to come from new recording days *and* new focal
scenes/flowers. The independent cluster unit is retained explicitly. Each truth
layer must have at least 20% independently double-annotated windows within every
realised cluster, selected in the manifest before model scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TRUTH_LAYERS: tuple[str, ...] = (
    "biological_event",
    "target_coupled_response",
    "nuisance",
    "observation_support",
)


class V15Split(str, Enum):
    DEVELOPMENT = "development"
    HELD_OUT = "held_out"


@dataclass(frozen=True, slots=True)
class V15ManifestWindow:
    window_id: str
    cluster_id: str
    recording_day: str
    focal_scene_id: str
    split: V15Split
    primary_clip_sha256: str
    reference_clip_sha256: str
    double_annotation_layers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("window_id", self.window_id),
            ("cluster_id", self.cluster_id),
            ("recording_day", self.recording_day),
            ("focal_scene_id", self.focal_scene_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} cannot be empty")
        if not isinstance(self.split, V15Split):
            raise TypeError("split must be a V15Split")
        if _SHA256_RE.fullmatch(self.primary_clip_sha256) is None:
            raise ValueError("primary_clip_sha256 must be lowercase 64-hex")
        if _SHA256_RE.fullmatch(self.reference_clip_sha256) is None:
            raise ValueError("reference_clip_sha256 must be lowercase 64-hex")
        unknown = sorted(set(self.double_annotation_layers) - set(TRUTH_LAYERS))
        if unknown:
            raise ValueError(f"unknown double-annotation truth layers: {unknown}")
        if len(set(self.double_annotation_layers)) != len(self.double_annotation_layers):
            raise ValueError("double_annotation_layers cannot contain duplicates")


@dataclass(frozen=True, slots=True)
class V15SplitManifestSummary:
    n_windows: int
    n_clusters: int
    development_windows: int
    held_out_windows: int
    development_clusters: int
    held_out_clusters: int
    minimum_double_annotation_fraction: float


def validate_v15_split_manifest(
    rows: list[V15ManifestWindow],
    *,
    minimum_double_annotation_fraction: float = 0.20,
) -> V15SplitManifestSummary:
    """Validate one realised V15 development/held-out manifest.

    Hard rules:
    - window IDs are unique;
    - each cluster belongs to exactly one split;
    - development and held-out recording days are disjoint;
    - development and held-out focal scenes/flowers are disjoint;
    - each realised cluster has >=20% independently double-annotated windows in
      each of the four truth layers;
    - both splits are non-empty.

    Passing this validator is necessary but not sufficient for held-out readiness:
    the validated manifest itself must still be committed and SHA-registered in
    the prefreeze registry.
    """

    if not 0.0 < minimum_double_annotation_fraction <= 1.0:
        raise ValueError("minimum_double_annotation_fraction must lie in (0, 1]")
    if not rows:
        raise ValueError("split manifest cannot be empty")

    window_ids = [row.window_id for row in rows]
    if len(set(window_ids)) != len(window_ids):
        raise ValueError("window_id values must be unique")

    by_cluster: dict[str, list[V15ManifestWindow]] = {}
    for row in rows:
        by_cluster.setdefault(row.cluster_id, []).append(row)

    for cluster_id, cluster_rows in by_cluster.items():
        splits = {row.split for row in cluster_rows}
        if len(splits) != 1:
            raise ValueError(f"cluster crosses development/held-out split: {cluster_id}")

        n = len(cluster_rows)
        for layer in TRUTH_LAYERS:
            selected = sum(layer in row.double_annotation_layers for row in cluster_rows)
            fraction = selected / n
            if fraction + 1e-15 < minimum_double_annotation_fraction:
                raise ValueError(
                    f"cluster {cluster_id} truth layer {layer} has double-annotation "
                    f"fraction {fraction:.6f} below {minimum_double_annotation_fraction:.6f}"
                )

    development = [row for row in rows if row.split is V15Split.DEVELOPMENT]
    held_out = [row for row in rows if row.split is V15Split.HELD_OUT]
    if not development or not held_out:
        raise ValueError("both development and held_out splits must contain windows")

    development_days = {row.recording_day for row in development}
    held_out_days = {row.recording_day for row in held_out}
    overlap_days = sorted(development_days & held_out_days)
    if overlap_days:
        raise ValueError(f"held-out recording days must be entirely new: {overlap_days}")

    development_scenes = {row.focal_scene_id for row in development}
    held_out_scenes = {row.focal_scene_id for row in held_out}
    overlap_scenes = sorted(development_scenes & held_out_scenes)
    if overlap_scenes:
        raise ValueError(f"held-out focal scenes must be entirely new: {overlap_scenes}")

    development_cluster_ids = {row.cluster_id for row in development}
    held_out_cluster_ids = {row.cluster_id for row in held_out}
    if development_cluster_ids & held_out_cluster_ids:
        raise AssertionError("cluster split leakage should have been rejected above")

    return V15SplitManifestSummary(
        n_windows=len(rows),
        n_clusters=len(by_cluster),
        development_windows=len(development),
        held_out_windows=len(held_out),
        development_clusters=len(development_cluster_ids),
        held_out_clusters=len(held_out_cluster_ids),
        minimum_double_annotation_fraction=minimum_double_annotation_fraction,
    )
