#!/usr/bin/env python3
"""Generate the V14a dimensionless closed-world phase surface.

Scientific prediction checks are descriptive and never change the process model or
make the workflow fail. Implementation/provenance errors fail closed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
from collections import defaultdict
from pathlib import Path

from interaction_sensing.simulation.dimensionless_observability_v14 import (
    DimensionlessPoint,
    IndeterminacyReason,
    LatentRegime,
    VisitInference,
    analyse_phase_point,
)


REGIME_BY_NAME = {item.value: item for item in LatentRegime}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mean(rows: list[dict[str, float]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows) if rows else float("nan")


def _selected(rows: list[dict[str, float]], predicate) -> list[dict[str, float]]:
    return [row for row in rows if predicate(row)]


def run(
    protocol_path: Path,
    output_dir: Path,
    *,
    limit_coordinates: int | None = None,
    replicates_override: int | None = None,
) -> dict[str, object]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["schema"] != "insepi-v14-dimensionless-world-protocol-v3":
        raise ValueError("unexpected V14 protocol schema")

    sweep = protocol["sweep"]
    values = [
        sweep["pi1_values"],
        sweep["pi2_values"],
        sweep["pi3_values"],
        sweep["pi4_values"],
    ]
    coordinates = list(itertools.product(*values))
    if limit_coordinates is not None:
        coordinates = coordinates[:limit_coordinates]
    regimes = [REGIME_BY_NAME[name] for name in sweep["latent_deviation_regimes"]]
    reps = int(replicates_override or sweep["replicates_per_coordinate_regime"])
    samples = int(sweep["samples_per_window"])

    aggregate: dict[tuple[float, float, float, float, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    total_worlds = 0

    for coord_index, (pi1, pi2, pi3, pi4) in enumerate(coordinates):
        point = DimensionlessPoint(float(pi1), float(pi2), float(pi3), float(pi4))
        for regime_index, regime in enumerate(regimes):
            key = (point.pi1, point.pi2, point.pi3, point.pi4, regime.value)
            bucket = aggregate[key]
            for replicate in range(reps):
                seed = coord_index * 100_000 + regime_index * 1_000 + replicate
                result = analyse_phase_point(point, regime, seed=seed, samples=samples)
                total_worlds += 1
                bucket["n"] += 1
                bucket["undetermined"] += result.inference is VisitInference.UNDETERMINED
                bucket["present"] += result.inference is VisitInference.PRESENT
                bucket["absent"] += result.inference is VisitInference.ABSENT
                bucket["information_absent"] += (
                    result.indeterminacy_reason is IndeterminacyReason.INFORMATION_ABSENT
                )
                bucket["essential_ambiguity"] += (
                    result.indeterminacy_reason is IndeterminacyReason.ESSENTIAL_AMBIGUITY
                )
                bucket["model_uncertainty"] += (
                    result.indeterminacy_reason is IndeterminacyReason.MODEL_UNCERTAINTY
                )
                bucket["both_supported"] += result.both_target_and_nuisance_supported
                bucket["indirect_rescue"] += result.indirect_target_rescue
                bucket["target_support"] += result.target_support
                bucket["nuisance_support"] += result.exogenous_nuisance_support
                bucket["observation_support"] += result.observation_support
                bucket["identifiability_margin"] += result.identifiability_margin
                bucket["direct_route"] += result.direct_target_route
                bucket["indirect_route"] += result.indirect_target_route

    rows: list[dict[str, float | str]] = []
    for key in sorted(aggregate):
        pi1, pi2, pi3, pi4, regime = key
        bucket = aggregate[key]
        n = bucket["n"]
        row: dict[str, float | str] = {
            "pi1": pi1,
            "pi2": pi2,
            "pi3": pi3,
            "pi4": pi4,
            "regime": regime,
            "n": int(n),
        }
        for source, output in (
            ("undetermined", "undetermined_rate"),
            ("present", "present_rate"),
            ("absent", "absent_rate"),
            ("information_absent", "information_absence_rate"),
            ("essential_ambiguity", "essential_ambiguity_rate"),
            ("model_uncertainty", "model_uncertainty_rate"),
            ("both_supported", "both_supported_rate"),
            ("indirect_rescue", "indirect_rescue_rate"),
        ):
            row[output] = bucket[source] / n
        for source, output in (
            ("target_support", "mean_target_support"),
            ("nuisance_support", "mean_exogenous_nuisance_support"),
            ("observation_support", "mean_observation_support"),
            ("identifiability_margin", "mean_identifiability_margin"),
            ("direct_route", "mean_direct_route"),
            ("indirect_route", "mean_indirect_route"),
        ):
            row[output] = bucket[source] / n
        rows.append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "v14_dimensionless_phase_surface.csv"
    fields = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (f"{value:.12g}" if isinstance(value, float) else value)
                    for key, value in row.items()
                }
            )

    # Descriptive checks of predictions fixed before the canonical sweep. These
    # booleans are evidence about the model; they are never CI pass conditions.
    numeric_rows = [dict(row) for row in rows]  # type: ignore[arg-type]
    min_pi1 = min(sweep["pi1_values"])
    max_pi1 = max(sweep["pi1_values"])
    max_pi3 = max(sweep["pi3_values"])
    max_pi4 = max(sweep["pi4_values"])

    target_regimes = {
        "target_only",
        "target_coupled",
        "target_nuisance_superposed",
        "target_nuisance_coupled",
    }
    low_pi1 = _selected(numeric_rows, lambda r: r["regime"] in target_regimes and r["pi1"] == min_pi1)
    high_pi1 = _selected(numeric_rows, lambda r: r["regime"] in target_regimes and r["pi1"] == max_pi1)

    weak_sep = _selected(
        numeric_rows,
        lambda r: r["pi3"] <= 0.31622776601683794 and r["pi4"] <= 0.31622776601683794,
    )
    pi2_near = _selected(weak_sep, lambda r: r["pi2"] == 1.0)
    pi2_far = _selected(weak_sep, lambda r: r["pi2"] in {min(sweep["pi2_values"]), max(sweep["pi2_values"])})

    low_direct_coupled = _selected(
        numeric_rows,
        lambda r: r["regime"] == "target_coupled" and r["pi3"] <= 0.1,
    )
    no_coupling = _selected(low_direct_coupled, lambda r: r["pi4"] == 0.0)
    high_coupling = _selected(low_direct_coupled, lambda r: r["pi4"] == max_pi4)

    pi3_zero = _selected(
        numeric_rows,
        lambda r: r["regime"] in target_regimes and r["pi3"] == 0.0,
    )
    pi3_high = _selected(
        numeric_rows,
        lambda r: r["regime"] in target_regimes and r["pi3"] == max_pi3,
    )

    prediction_checks = {
        "P1_short_window_more_information_absence": _mean(low_pi1, "information_absence_rate")
        > _mean(high_pi1, "information_absence_rate"),
        "P2_low_pi3_weaker_direct_route": _mean(pi3_zero, "mean_direct_route")
        < _mean(pi3_high, "mean_direct_route"),
        "P3_pi2_near_one_more_ambiguity_when_other_separation_weak": _mean(
            pi2_near, "essential_ambiguity_rate"
        )
        > _mean(pi2_far, "essential_ambiguity_rate"),
        "P4_high_pi4_more_indirect_rescue_at_low_pi3": _mean(
            high_coupling, "indirect_rescue_rate"
        )
        > _mean(no_coupling, "indirect_rescue_rate"),
    }

    summary: dict[str, object] = {
        "schema": "insepi-v14-dimensionless-phase-result-v1",
        "canonical": limit_coordinates is None and replicates_override is None,
        "protocol_sha256": _sha256(protocol_path),
        "coordinate_count": len(coordinates),
        "regime_count": len(regimes),
        "replicates_per_coordinate_regime": reps,
        "world_count": total_worlds,
        "surface_row_count": len(rows),
        "overall": {
            "mean_undetermined_rate": _mean(numeric_rows, "undetermined_rate"),
            "mean_information_absence_rate": _mean(numeric_rows, "information_absence_rate"),
            "mean_essential_ambiguity_rate": _mean(numeric_rows, "essential_ambiguity_rate"),
            "mean_both_supported_rate": _mean(numeric_rows, "both_supported_rate"),
            "mean_indirect_rescue_rate": _mean(numeric_rows, "indirect_rescue_rate"),
        },
        "prediction_checks_descriptive_not_gates": prediction_checks,
        "claim_boundary": "development phase geometry only; no field accuracy, no physical transition claim, no observer optimisation",
    }
    summary_path = output_dir / "v14_dimensionless_phase_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema": "insepi-v14-dimensionless-phase-receipt-v1",
        "protocol_sha256": _sha256(protocol_path),
        "surface_sha256": _sha256(csv_path),
        "summary_sha256": _sha256(summary_path),
        "canonical": summary["canonical"],
    }
    receipt_path = output_dir / "v14_dimensionless_phase_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", default="benchmarks/v14_dimensionless_world_protocol.json")
    parser.add_argument("--output-dir", default=".v14/phase")
    parser.add_argument("--limit-coordinates", type=int)
    parser.add_argument("--replicates", type=int)
    args = parser.parse_args()
    summary = run(
        Path(args.protocol),
        Path(args.output_dir),
        limit_coordinates=args.limit_coordinates,
        replicates_override=args.replicates,
    )
    print("V14_PHASE_CANONICAL", str(summary["canonical"]).lower())
    print("V14_PHASE_WORLDS", summary["world_count"])
    print("V14_PHASE_ROWS", summary["surface_row_count"])
    for key, value in summary["prediction_checks_descriptive_not_gates"].items():
        print(key, str(value).lower())


if __name__ == "__main__":
    main()
