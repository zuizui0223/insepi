"""Pre-scoring manifest binding for V15 nuisance reference zones.

The nuisance field measurement is only a safe pre-heldout adapter if reference
regions cannot be chosen after target/nuisance outcomes are visible.  This module
binds every focal/reference geometry to a concrete primary-stream clip SHA-256
before model scoring.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .domain import BBox
from .nuisance_field_measurement_v15 import NuisanceReferenceLayout


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class NuisanceReferenceManifestEntry:
    window_id: str
    primary_clip_sha256: str
    focal_zone: BBox
    reference_zones: tuple[BBox, ...]
    selection_method: str
    selected_before_model_scoring: bool = True
    used_target_observer_output: bool = False
    used_nuisance_observer_output: bool = False
    used_biological_or_nuisance_truth: bool = False

    def __post_init__(self) -> None:
        if not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        if _SHA256_RE.fullmatch(self.primary_clip_sha256) is None:
            raise ValueError("primary_clip_sha256 must be lowercase 64-hex")
        if not self.reference_zones:
            raise ValueError("at least one reference zone is required")
        if not self.selection_method.strip():
            raise ValueError("selection_method cannot be empty")
        if not self.selected_before_model_scoring:
            raise ValueError("reference zones must be selected before model scoring")
        if self.used_target_observer_output:
            raise ValueError("reference-zone selection cannot use target observer output")
        if self.used_nuisance_observer_output:
            raise ValueError("reference-zone selection cannot use nuisance observer output")
        if self.used_biological_or_nuisance_truth:
            raise ValueError("reference-zone selection cannot use biological/nuisance truth")
        for index, zone in enumerate(self.reference_zones):
            if self.focal_zone.intersection_area(zone) > 0.0:
                raise ValueError(f"reference_zone[{index}] must be spatially disjoint from focal_zone")

    def to_reference_layout(self) -> NuisanceReferenceLayout:
        return NuisanceReferenceLayout(
            reference_zones=self.reference_zones,
            method=self.selection_method,
        )


def validate_nuisance_reference_manifest(
    entries: list[NuisanceReferenceManifestEntry],
) -> tuple[NuisanceReferenceManifestEntry, ...]:
    """Validate uniqueness and return a deterministic window-id ordering."""

    if not entries:
        raise ValueError("nuisance reference manifest cannot be empty")
    ids = [entry.window_id for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("nuisance reference manifest window_id values must be unique")
    clip_hashes = [entry.primary_clip_sha256 for entry in entries]
    if len(set(zip(ids, clip_hashes))) != len(entries):
        raise ValueError("duplicate window/clip provenance entry")
    return tuple(sorted(entries, key=lambda entry: entry.window_id))
