#!/usr/bin/env python3
"""Observer-free overlap diagnostics for the 18 frozen V10 disturbance panels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel-registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    panels = json.loads(args.panel_registry.read_text(encoding="utf-8"))
    if not isinstance(panels, list) or len(panels) != 18:
        raise RuntimeError("expected the frozen 18-panel V10 registry")
    sets = [set(map(int, panel["disturbed_base_indices"])) for panel in panels]
    if any(len(indices) != 182 for indices in sets):
        raise RuntimeError("each V10 panel must contain exactly 182 disturbed base windows")

    overlaps: list[int] = []
    phis: list[float] = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            intersection = len(sets[i] & sets[j])
            overlaps.append(intersection)
            # Equal 182/182 margins in N=364 imply n00=n11=intersection.
            phis.append((intersection * intersection - (182 - intersection) ** 2) / (182 * 182))

    exposure = np.zeros(364, dtype=np.int16)
    for indices in sets:
        exposure[list(indices)] += 1

    result = {
        "schema": "interaction-sensing-v10-panel-overlap-qa-v1",
        "status": "post-freeze-descriptive-only-not-a-v10-claim-gate",
        "observer_execution": False,
        "panel_pair_count": len(overlaps),
        "independent_half_assignment_expected_overlap": 91.0,
        "mean_pairwise_overlap": float(np.mean(overlaps)),
        "min_pairwise_overlap": int(min(overlaps)),
        "max_pairwise_overlap": int(max(overlaps)),
        "mean_pairwise_phi": float(np.mean(phis)),
        "min_pairwise_phi": float(min(phis)),
        "max_pairwise_phi": float(max(phis)),
        "window_panel_exposure_mean": float(np.mean(exposure)),
        "window_panel_exposure_min": int(np.min(exposure)),
        "window_panel_exposure_max": int(np.max(exposure)),
        "windows_never_disturbed": int(np.sum(exposure == 0)),
        "windows_always_disturbed": int(np.sum(exposure == 18)),
        "window_panel_exposure_histogram": {
            str(value): int(count) for value, count in enumerate(np.bincount(exposure)) if count
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for key in (
        "mean_pairwise_overlap", "min_pairwise_overlap", "max_pairwise_overlap",
        "mean_pairwise_phi", "min_pairwise_phi", "max_pairwise_phi",
        "window_panel_exposure_min", "window_panel_exposure_max",
    ):
        print("V10_PANEL_OVERLAP_QA", key, result[key])
    print("V10_PANEL_OVERLAP_QA_OBSERVER_EXECUTION false")


if __name__ == "__main__":
    main()
