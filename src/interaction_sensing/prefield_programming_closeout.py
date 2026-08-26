"""Reproducible synthesis of the frozen V14b pre-field programming result.

The closeout layer reads already locked JSON evidence.  It never regenerates a
world, invokes an observer, changes a threshold, or creates a new scientific
acceptance gate.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from statistics import fmean
from typing import Any

FROZEN_V14B_PHASE_SURFACE_SHA256 = (
    "1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34"
)
FROZEN_FAMILYWISE_ALPHA = 0.05
FROZEN_NUISANCE_THRESHOLD = 4.33898869355123e-06
FROZEN_CANONICAL_JSON_SHA256 = {
    "world_protocol": "d6d1a2cffa979d4861091b9781e604a4fe82f1b8315e3bf218a74ea501728d27",
    "ternary_protocol": "d1cae09fef9d6698409660094bddd48b0d1edbaeea043f0951d50db275ad7581",
    "locked_summary": "14af819a27e78c4175e076d2ad27499c4cc35d7763babb615c26eef1327c1b45",
    "figure_data": "dfca13da6792ced1a0c486a567bc652f352f2e304b38b17081cfb33abbbf59e4",
}


def canonical_json_sha256(document: Mapping[str, Any]) -> str:
    """Hash JSON semantics independently of checkout newline conventions."""

    payload = json.dumps(
        document,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = parent.get(name)
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be an object")
    return value


def _numbers(parent: Mapping[str, Any], name: str) -> tuple[float, ...]:
    value = parent.get(name)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an array")
    numbers = tuple(float(item) for item in value)
    if not numbers:
        raise ValueError(f"{name} cannot be empty")
    return numbers


def _range(values: Sequence[float]) -> dict[str, float]:
    minimum = min(values)
    maximum = max(values)
    return {
        "minimum": minimum,
        "maximum": maximum,
        "range": maximum - minimum,
    }


def _axis_summary(values_by_coordinate: Mapping[str, Any]) -> dict[str, Any]:
    coordinates = tuple(float(value) for value in values_by_coordinate)
    rates = tuple(float(values_by_coordinate[key]) for key in values_by_coordinate)
    maximum = max(rates)
    return {
        **_range(rates),
        "maximum_coordinate": coordinates[rates.index(maximum)],
        "values_by_coordinate": {
            str(key): float(value) for key, value in values_by_coordinate.items()
        },
    }


def build_v14b_prefield_programming_closeout(
    *,
    world_protocol: Mapping[str, Any],
    ternary_protocol: Mapping[str, Any],
    locked_summary: Mapping[str, Any],
    figure_data: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a descriptive closeout from frozen evidence with identity checks."""

    if world_protocol.get("schema") != "insepi-v14a2-spatiotemporal-world-protocol-v1":
        raise ValueError("wrong V14a2 world protocol schema")
    if (
        ternary_protocol.get("schema")
        != "insepi-v14b-frozen-ternary-phase-surface-protocol-v1"
    ):
        raise ValueError("wrong V14b ternary protocol schema")
    if (
        locked_summary.get("schema")
        != "insepi-v14b-frozen-ternary-phase-surface-locked-summary-v1"
    ):
        raise ValueError("wrong V14b locked summary schema")
    if figure_data.get("schema") != "insepi-v14b-frozen-ternary-phase-figure-data-v1":
        raise ValueError("wrong V14b figure-data schema")

    provenance = _mapping(locked_summary, "provenance")
    figure_source = _mapping(figure_data, "source")
    surface_sha = provenance.get("phase_surface_sha256")
    if surface_sha != FROZEN_V14B_PHASE_SURFACE_SHA256:
        raise ValueError("locked phase-surface identity changed")
    if figure_source.get("phase_surface_sha256") != surface_sha:
        raise ValueError("figure data does not reference the locked phase surface")
    if provenance.get("scientific_contract_unchanged") is not True:
        raise ValueError("scientific contract was not retained")

    if ternary_protocol.get("alpha") != FROZEN_FAMILYWISE_ALPHA:
        raise ValueError("family-wise alpha changed")
    if ternary_protocol.get("frozen_nuisance_threshold") != FROZEN_NUISANCE_THRESHOLD:
        raise ValueError("frozen nuisance threshold changed")
    freeze_rules = _mapping(ternary_protocol, "freeze_rules")
    if not all(
        freeze_rules.get(name) is True
        for name in (
            "observer_changes_forbidden",
            "threshold_changes_forbidden",
            "alpha_changes_forbidden",
            "measurement_results_cannot_trigger_retuning",
        )
    ):
        raise ValueError("V14b freeze rules are incomplete")

    global_summary = _mapping(locked_summary, "global_summary")
    if global_summary.get("observer_retuned") is not False:
        raise ValueError("observer_retuned must remain false")
    if global_summary.get("world_count") != 5_880_000:
        raise ValueError("locked world count changed")

    descriptives = _mapping(locked_summary, "key_dimensionless_descriptives")
    pi1 = _mapping(descriptives, "pi1_total_U_deviation_worlds")
    pi2 = _mapping(descriptives, "pi2_total_U_deviation_worlds")
    pi6 = _mapping(descriptives, "pi6_total_U_deviation_worlds")

    panels = _mapping(figure_data, "panels")
    direct_panel = _mapping(panels, "pi3_target_truth_lines")
    pi3_values = _numbers(direct_panel, "pi3")
    u_values = _numbers(direct_panel, "undetermined_total_rate")
    fn_values = _numbers(direct_panel, "forced_binary_false_negative_rate")
    width_values = _numbers(
        direct_panel,
        "visit_presence_partial_identification_width",
    )
    if not (
        len(pi3_values) == len(u_values) == len(fn_values) == len(width_values)
        and pi3_values[0] == 0.0
        and all(value > 0.0 for value in pi3_values[1:])
    ):
        raise ValueError("Pi3 direct-channel panel shape changed")

    positive_u = fmean(u_values[1:])
    positive_fn = fmean(fn_values[1:])
    positive_width = fmean(width_values[1:])
    undetermined = float(global_summary["undetermined_total_rate"])
    information_absent = float(global_summary["undetermined_information_absent_rate"])
    overlap = float(global_summary["undetermined_overlap_or_attribution_rate"])
    if abs((information_absent + overlap) - undetermined) > 1e-12:
        raise ValueError("reason-tagged U rates do not sum to total U")

    canonical_hashes = {
        "world_protocol": canonical_json_sha256(world_protocol),
        "ternary_protocol": canonical_json_sha256(ternary_protocol),
        "locked_summary": canonical_json_sha256(locked_summary),
        "figure_data": canonical_json_sha256(figure_data),
    }
    for source_name, expected in FROZEN_CANONICAL_JSON_SHA256.items():
        if canonical_hashes[source_name] != expected:
            raise ValueError(f"{source_name.replace('_', ' ')} identity changed")

    return {
        "schema": "insepi-v14b-prefield-programming-closeout-v1",
        "status": "closed-pre-field-programming-result",
        "source_identity": {
            "world_protocol_canonical_sha256": canonical_hashes["world_protocol"],
            "ternary_protocol_canonical_sha256": canonical_hashes["ternary_protocol"],
            "locked_summary_canonical_sha256": canonical_hashes["locked_summary"],
            "figure_data_canonical_sha256": canonical_hashes["figure_data"],
            "phase_surface_sha256": surface_sha,
            "world_count": global_summary["world_count"],
            "observer_retuned": False,
        },
        "one_universe": {
            "physical_states": [
                "baseline",
                "target_only",
                "nuisance_only",
                "target_coupled",
                "target_nuisance_superposed",
                "target_nuisance_coupled",
            ],
            "interaction_directed_target_process": (
                "a localized entry-dwell-exit actor process, optionally followed "
                "by a target-caused local scene response"
            ),
            "exogenous_nuisance_process": (
                "a stationary mean-reverting spatiotemporal field that is not "
                "conditioned on the target interaction"
            ),
            "observation_layer": (
                "observation support is conceptually separate from physical "
                "state; unavailable observation is not a third physical cause"
            ),
            "v14b_measurement_boundary": (
                "the frozen surface measures deviation-side U; baseline remains "
                "no-query and contributes to partial-identification width rather "
                "than being crossed with an explicit unavailable-O factor"
            ),
            "animal_intention_inferred": False,
        },
        "estimand": {
            "primary": "R_U(pi,z) = Pr(decision is U | Pi1..Pi6, latent regime z)",
            "frozen_marginal": (
                "R_U(pi) under the prefrozen equal weighting of regimes and seeds"
            ),
            "reason_decomposition": [
                "U_information_absent",
                "U_overlap_or_attribution",
            ],
            "partial_identification_width": "baseline rate + total U rate",
            "forced_binary_comparator": (
                "the prefrozen coercion mapping U and baseline to target-absent"
            ),
        },
        "frozen_measurement": {
            "global_undetermined_rate": undetermined,
            "global_information_absent_rate": information_absent,
            "global_overlap_or_attribution_rate": overlap,
            "overlap_share_of_undetermined": overlap / undetermined,
            "information_absent_share_of_undetermined": (
                information_absent / undetermined
            ),
            "forced_binary_false_positive_rate": global_summary[
                "forced_binary_false_positive_rate"
            ],
            "forced_binary_false_negative_rate": global_summary[
                "forced_binary_false_negative_rate"
            ],
            "mean_partial_identification_width": global_summary[
                "mean_partial_identification_width"
            ],
        },
        "observation_condition_dependence": {
            "pi1_observation_window": _axis_summary(pi1),
            "pi2_nuisance_to_target_timescale": _axis_summary(pi2),
            "pi6_samples_per_target_timescale": _axis_summary(pi6),
            "direct_actor_channel_boundary_on_target_truth": {
                "pi3_zero": {
                    "undetermined_rate": u_values[0],
                    "forced_binary_false_negative_rate": fn_values[0],
                    "partial_identification_width": width_values[0],
                },
                "pi3_positive_mean": {
                    "undetermined_rate": positive_u,
                    "forced_binary_false_negative_rate": positive_fn,
                    "partial_identification_width": positive_width,
                },
                "zero_minus_positive": {
                    "undetermined_rate": round(u_values[0] - positive_u, 15),
                    "forced_binary_false_negative_rate": round(
                        fn_values[0] - positive_fn,
                        15,
                    ),
                    "partial_identification_width": round(
                        width_values[0] - positive_width,
                        15,
                    ),
                },
            },
        },
        "locked_interpretation": {
            "supported": (
                "U is a reason-tagged, observation-condition-dependent estimand "
                "in this frozen closed-world generator and must not be silently "
                "recoded as target absence"
            ),
            "dominant_boundary": (
                "structural direct actor-channel absence (Pi3=0 versus Pi3>0)"
            ),
            "retained_negative_result": (
                "Pi2 has only a shallow nonmonotonic U maximum near one, not the "
                "predicted dominant narrow critical ridge"
            ),
            "not_supported": (
                "that every rejection is desirable or that no rejection can be "
                "caused by model inadequacy"
            ),
        },
        "synthesis_boundary": {
            "prefrozen_surface_estimand": True,
            "post_result_interaction_directed_wording": True,
            "explicit_cross_state_observation_factor_measured": False,
            "new_acceptance_threshold_added": False,
            "scientific_simulation_rerun": False,
        },
        "claim_ceiling": (
            "Closed-world simulation evidence for observation-conditioned "
            "rejection geometry; no animal-intention recognition, field "
            "prevalence, field accuracy, universal threshold, or superiority "
            "over every possible binary classifier; V14b also does not provide "
            "a fully crossed baseline-by-observation-availability experiment."
        ),
    }
