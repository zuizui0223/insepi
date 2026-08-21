"""Generic InsePi adapter for a canonical V7 pixel artifact.

The exact frozen InsePi observer is injected as a two-image decision function.
This I/O layer never receives latent truth as a decision input, so it can be
applied unchanged to the eventual reachable V5-frozen method generation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Callable, Mapping

import numpy as np

from interaction_sensing.simulation.v7_artifact import read_world_artifact


TRACE_SCHEMA = "pollipi-insepi-v7-insepi-trace-v1"
DecisionFn = Callable[[np.ndarray, np.ndarray], Mapping[str, object]]


@dataclass(frozen=True, slots=True)
class InsePiV7Result:
    schema: str
    condition_id: str
    family: str
    tier: int
    replicate: int
    true_visit: bool
    event_visibility: float
    intensity: float
    inferred_noise_source: str
    observability_state: str
    false_event_risk: float
    missed_event_risk: float
    attribution_risk: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_insepi_v7_artifact(
    npz_path: str | Path,
    manifest_path: str | Path,
    *,
    decision_fn: DecisionFn,
) -> tuple[object, list[InsePiV7Result]]:
    manifest, backgrounds, frames, metadata = read_world_artifact(npz_path, manifest_path)
    rows: list[InsePiV7Result] = []
    for index, meta in enumerate(metadata):
        # The decision function receives only pixels.  Latent labels are attached
        # below after inference and cannot affect the observer decision.
        decision = decision_fn(frames[index], backgrounds[index])
        required = (
            "inferred_noise_source",
            "observability_state",
            "false_event_risk",
            "missed_event_risk",
            "attribution_risk",
        )
        missing = [key for key in required if key not in decision]
        if missing:
            raise ValueError(f"InsePi V7 decision missing fields: {missing}")
        rows.append(InsePiV7Result(
            schema=TRACE_SCHEMA,
            condition_id=str(meta["condition_id"]),
            family=str(meta["family"]),
            tier=int(meta["tier"]),
            replicate=int(meta["replicate"]),
            true_visit=bool(meta["true_visit"]),
            event_visibility=float(meta["event_visibility"]),
            intensity=float(meta["intensity"]),
            inferred_noise_source=str(decision["inferred_noise_source"]),
            observability_state=str(decision["observability_state"]),
            false_event_risk=float(decision["false_event_risk"]),
            missed_event_risk=float(decision["missed_event_risk"]),
            attribution_risk=float(decision["attribution_risk"]),
        ))
    return manifest, rows


def write_insepi_v7_trace_jsonl(
    npz_path: str | Path,
    manifest_path: str | Path,
    trace_path: str | Path,
    *,
    source_commit: str,
    decision_fn: DecisionFn,
) -> Path:
    if not source_commit:
        raise ValueError("source_commit provenance is required")
    manifest, rows = run_insepi_v7_artifact(
        npz_path,
        manifest_path,
        decision_fn=decision_fn,
    )
    output = Path(trace_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    provenance = {
        "record_type": "provenance",
        "schema": TRACE_SCHEMA,
        "source_commit": source_commit,
        "world_fingerprint": manifest.world_fingerprint,
        "world_spec_sha256": manifest.world_spec_sha256,
        "pixel_artifact_sha256": manifest.npz_sha256,
        "condition_count": manifest.condition_count,
    }
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(provenance, sort_keys=True) + "\n")
        for row in rows:
            payload = row.to_dict()
            payload["record_type"] = "result"
            handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return output
