"""Prefrozen V15a crossing of physical state and observation support.

V15a does not regenerate or retune the frozen V14b observers.  It takes the
locked V14b global counts and retained regime rates, then crosses each physical
regime with an independent, synthetic primary-stream support lattice.  This
isolates the epistemic effect of observation support from the physical target
and nuisance processes.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .observation_triad import ObservationAvailability
from .prefield_programming_closeout import (
    FROZEN_CANONICAL_JSON_SHA256,
    FROZEN_FAMILYWISE_ALPHA,
    FROZEN_NUISANCE_THRESHOLD,
    FROZEN_V14B_PHASE_SURFACE_SHA256,
    canonical_json_sha256,
)
from .support_estimation import (
    PrimaryStreamSupportEstimate,
    PrimaryStreamSupportEstimator,
    PrimaryStreamSupportMeasurements,
    SupportComponentMeasurement,
    SupportMeasurementProvenance,
)

V15_OBSERVABILITY_CONTRACT_SHA256 = (
    "1c20e595af1ffc22ac2558d080e38390572cc32ca9ed91798b13624bd7d87248"
)
V14B_CLOSEOUT_SHA256 = (
    "ad5b3a60b2f82d1f079076a73acc7aa55a53dc33b9703a5a3625762c5e3646f6"
)
V15A_PROTOCOL_CANONICAL_SHA256 = (
    "7a24df2016b54aaaf002414e86d7c51104104258f5541b73e2efca130fd8df1d"
)

PHYSICAL_REGIMES = (
    "baseline",
    "target_only",
    "nuisance_only",
    "target_coupled",
    "target_nuisance_superposed",
    "target_nuisance_coupled",
)
TARGET_PRESENT_REGIMES = (
    "target_only",
    "target_coupled",
    "target_nuisance_superposed",
    "target_nuisance_coupled",
)
SUPPORT_COMPONENTS = (
    "target_zone_coverage",
    "target_zone_visibility",
    "spatial_resolution",
    "photometric_sufficiency",
    "temporal_continuity",
)
BASE_STATES = ("baseline", "target", "nuisance", "undetermined")


class CrossStateDecisionState(str, Enum):
    """Final epistemic state after the independent O layer is applied."""

    BASELINE = "baseline"
    TARGET = "target"
    NUISANCE = "nuisance"
    UNDETERMINED = "undetermined"
    CENSORED = "censored"


class CrossStateDecisionReason(str, Enum):
    NONE = "none"
    INFORMATION_ABSENT = "information_absent"
    OVERLAP_OR_ATTRIBUTION = "overlap_or_attribution"
    OBSERVATION_COMPROMISED = "observation_compromised"
    OBSERVATION_UNAVAILABLE = "observation_unavailable"


@dataclass(frozen=True, slots=True)
class SyntheticSupportProfile:
    """One prefrozen member of the synthetic observation-support lattice."""

    name: str
    limiting_component: str | None
    limiting_score: float
    other_score: float = 0.90

    def measurements(self) -> PrimaryStreamSupportMeasurements:
        values = {
            component: (
                self.limiting_score
                if component == self.limiting_component
                else self.other_score
            )
            for component in SUPPORT_COMPONENTS
        }

        def measurement(component: str) -> SupportComponentMeasurement:
            return SupportComponentMeasurement(
                score=values[component],
                provenance=(
                    SupportMeasurementProvenance.OTHER_PRIMARY_STREAM_MEASUREMENT
                ),
                method="prefrozen synthetic support-factor level; not field data",
            )

        return PrimaryStreamSupportMeasurements(
            target_zone_coverage=measurement("target_zone_coverage"),
            target_zone_visibility=measurement("target_zone_visibility"),
            spatial_resolution=measurement("spatial_resolution"),
            photometric_sufficiency=measurement("photometric_sufficiency"),
            temporal_continuity=measurement("temporal_continuity"),
        )


@dataclass(frozen=True, slots=True)
class CrossStateDecision:
    state: CrossStateDecisionState
    reason: CrossStateDecisionReason
    base_state: str
    base_reason: str
    availability: ObservationAvailability


def prefrozen_support_profiles() -> tuple[SyntheticSupportProfile, ...]:
    """Return the complete 1 + 5 + 5 support-profile lattice."""

    profiles = [
        SyntheticSupportProfile(
            name="observable_all_adequate",
            limiting_component=None,
            limiting_score=0.90,
        )
    ]
    profiles.extend(
        SyntheticSupportProfile(
            name=f"compromised_{component}",
            limiting_component=component,
            limiting_score=0.50,
        )
        for component in SUPPORT_COMPONENTS
    )
    profiles.extend(
        SyntheticSupportProfile(
            name=f"unobservable_{component}",
            limiting_component=component,
            limiting_score=0.10,
        )
        for component in SUPPORT_COMPONENTS
    )
    return tuple(profiles)


def support_profile_specifications() -> list[dict[str, Any]]:
    """Serialize the exact profile lattice for protocol identity checks."""

    estimator = PrimaryStreamSupportEstimator()
    rows: list[dict[str, Any]] = []
    for profile in prefrozen_support_profiles():
        estimate = estimator.estimate(profile.measurements())
        rows.append(
            {
                "name": profile.name,
                "limiting_component": profile.limiting_component,
                "limiting_score": profile.limiting_score,
                "other_component_score": profile.other_score,
                "expected_availability": estimate.availability.value,
            }
        )
    return rows


def apply_observation_layer(
    *,
    base_state: str,
    base_reason: str,
    availability: ObservationAvailability,
) -> CrossStateDecision:
    """Apply O without changing the frozen V14b physical/observer output.

    Observable profiles retain the exact V14b state and U reason.  Compromised
    profiles are reason-tagged U.  Unobservable profiles are censored rather
    than converted to target absence or to another physical state.
    """

    if base_state not in BASE_STATES:
        raise ValueError(f"unknown frozen base state: {base_state}")
    allowed_base_reasons = {
        "none",
        "information_absent",
        "overlap_or_attribution",
    }
    if base_reason not in allowed_base_reasons:
        raise ValueError(f"unknown frozen base reason: {base_reason}")
    if base_state == "undetermined" and base_reason == "none":
        raise ValueError("undetermined base state requires a reason")
    if base_state != "undetermined" and base_reason != "none":
        raise ValueError("determined base state cannot carry an U reason")

    if availability is ObservationAvailability.COMPROMISED:
        return CrossStateDecision(
            state=CrossStateDecisionState.UNDETERMINED,
            reason=CrossStateDecisionReason.OBSERVATION_COMPROMISED,
            base_state=base_state,
            base_reason=base_reason,
            availability=availability,
        )
    if availability is ObservationAvailability.UNOBSERVABLE:
        return CrossStateDecision(
            state=CrossStateDecisionState.CENSORED,
            reason=CrossStateDecisionReason.OBSERVATION_UNAVAILABLE,
            base_state=base_state,
            base_reason=base_reason,
            availability=availability,
        )

    return CrossStateDecision(
        state=CrossStateDecisionState(base_state),
        reason=CrossStateDecisionReason(base_reason),
        base_state=base_state,
        base_reason=base_reason,
        availability=availability,
    )


def _mapping(parent: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = parent.get(name)
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be an object")
    return value


def _sequence(parent: Mapping[str, Any], name: str) -> Sequence[Any]:
    value = parent.get(name)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an array")
    return value


def validate_v15a_protocol(
    *,
    protocol: Mapping[str, Any],
    locked_summary: Mapping[str, Any],
    v15_observability_contract: Mapping[str, Any],
    v14b_closeout: Mapping[str, Any],
) -> None:
    """Fail closed if any prefrozen parent or V15a rule changed."""

    if protocol.get("schema") != "insepi-v15a-cross-state-observability-protocol-v1":
        raise ValueError("wrong V15a protocol schema")
    if protocol.get("status") != "prefrozen-before-first-expansion":
        raise ValueError("V15a protocol is not prefrozen")
    if (
        locked_summary.get("schema")
        != "insepi-v14b-frozen-ternary-phase-surface-locked-summary-v1"
    ):
        raise ValueError("wrong V14b locked summary schema")
    if (
        v15_observability_contract.get("schema")
        != "insepi-v15-primary-stream-observability-estimator-v1"
    ):
        raise ValueError("wrong V15 observability contract schema")
    if v14b_closeout.get("status") != "closed-pre-field-programming-result":
        raise ValueError("V14b pre-field result is not closed")

    parents = _mapping(protocol, "parent_identity")
    expected_parents = {
        "v14b_locked_summary_canonical_sha256": FROZEN_CANONICAL_JSON_SHA256[
            "locked_summary"
        ],
        "v14b_phase_surface_sha256": FROZEN_V14B_PHASE_SURFACE_SHA256,
        "v14b_prefield_closeout_canonical_sha256": V14B_CLOSEOUT_SHA256,
        "v15_observability_contract_canonical_sha256": (
            V15_OBSERVABILITY_CONTRACT_SHA256
        ),
    }
    if dict(parents) != expected_parents:
        raise ValueError("V15a parent identity declaration changed")
    if (
        canonical_json_sha256(locked_summary)
        != FROZEN_CANONICAL_JSON_SHA256["locked_summary"]
    ):
        raise ValueError("V14b locked summary identity changed")
    if (
        canonical_json_sha256(v15_observability_contract)
        != V15_OBSERVABILITY_CONTRACT_SHA256
    ):
        raise ValueError("V15 observability contract identity changed")
    if canonical_json_sha256(v14b_closeout) != V14B_CLOSEOUT_SHA256:
        raise ValueError("V14b closeout identity changed")

    support = _mapping(protocol, "support_factor")
    if support.get("observable_threshold") != 0.70:
        raise ValueError("V15a observable threshold changed")
    if support.get("unobservable_threshold") != 0.30:
        raise ValueError("V15a unobservable threshold changed")
    if list(_sequence(support, "components")) != list(SUPPORT_COMPONENTS):
        raise ValueError("V15a support components changed")
    if list(_sequence(support, "profiles")) != support_profile_specifications():
        raise ValueError("V15a support profile lattice changed")

    if list(_sequence(protocol, "physical_regimes")) != list(PHYSICAL_REGIMES):
        raise ValueError("V15a physical regimes changed")
    parent_freeze = _mapping(protocol, "retained_parent_freeze")
    expected_freeze = {
        "familywise_alpha": FROZEN_FAMILYWISE_ALPHA,
        "nuisance_threshold": FROZEN_NUISANCE_THRESHOLD,
        "observer_retuning": False,
        "parent_world_regeneration": False,
    }
    if dict(parent_freeze) != expected_freeze:
        raise ValueError("V15a retained parent freeze changed")

    decision = _mapping(protocol, "decision_layer")
    if dict(decision) != {
        "observable": "retain_exact_v14b_state_and_reason",
        "compromised": "undetermined_with_observation_compromised_reason",
        "unobservable": "censored_with_observation_unavailable_reason",
        "unobservable_is_target_absence": False,
        "unobservable_is_a_physical_process": False,
    }:
        raise ValueError("V15a decision layer changed")

    rules = _mapping(protocol, "freeze_rules")
    required_true = (
        "profile_lattice_changes_forbidden",
        "decision_mapping_changes_forbidden",
        "parent_observer_changes_forbidden",
        "parent_threshold_changes_forbidden",
        "measurement_results_cannot_trigger_retuning",
        "first_result_must_be_retained",
    )
    if not all(rules.get(name) is True for name in required_true):
        raise ValueError("V15a freeze rules are incomplete")
    audit_locked_regime_rates(locked_summary)
    if canonical_json_sha256(protocol) != V15A_PROTOCOL_CANONICAL_SHA256:
        raise ValueError("V15a protocol identity changed")


def _counts_from_rates(section: Mapping[str, Any], total: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for state in BASE_STATES:
        rate_name = (
            "undetermined_total_rate" if state == "undetermined" else f"{state}_rate"
        )
        expected = float(section[rate_name]) * total
        rounded = round(expected)
        if abs(expected - rounded) > 1e-6:
            raise ValueError(f"{state} rate does not resolve to an integer count")
        counts[state] = rounded
    if sum(counts.values()) != total:
        raise ValueError("base state counts do not sum to the locked world count")
    return counts


def _reason_counts_from_rates(
    section: Mapping[str, Any], total: int, undetermined_count: int
) -> dict[str, int]:
    counts = {}
    for reason in ("information_absent", "overlap_or_attribution"):
        expected = float(section[f"undetermined_{reason}_rate"]) * total
        rounded = round(expected)
        if abs(expected - rounded) > 1e-6:
            raise ValueError(f"{reason} rate does not resolve to an integer count")
        counts[reason] = rounded
    if sum(counts.values()) != undetermined_count:
        raise ValueError("base U reason counts do not sum to base U")
    return counts


def _state_rates(section: Mapping[str, Any]) -> dict[str, float]:
    rates = {
        state: float(
            section[
                "undetermined_total_rate"
                if state == "undetermined"
                else f"{state}_rate"
            ]
        )
        for state in BASE_STATES
    }
    if any(rate < 0.0 or rate > 1.0 for rate in rates.values()):
        raise ValueError("base state rate lies outside [0, 1]")
    return rates


def _reason_rates(
    section: Mapping[str, Any], undetermined_rate: float
) -> dict[str, float]:
    rates = {
        reason: float(section[f"undetermined_{reason}_rate"])
        for reason in ("information_absent", "overlap_or_attribution")
    }
    if abs(sum(rates.values()) - undetermined_rate) > 1e-12:
        raise ValueError("base U reason rates do not sum to base U")
    return rates


def audit_locked_regime_rates(
    locked_summary: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Expose parent regime-rate residuals without normalising or repairing them."""

    regime_means = _mapping(locked_summary, "regime_means")
    if set(regime_means) != set(PHYSICAL_REGIMES):
        raise ValueError("locked physical regimes changed")
    audit: dict[str, dict[str, Any]] = {}
    for regime in PHYSICAL_REGIMES:
        section = _mapping(regime_means, regime)
        state_rates = _state_rates(section)
        reason_rates = _reason_rates(section, state_rates["undetermined"])
        state_rate_sum = sum(state_rates.values())
        audit[regime] = {
            "state_rate_sum": state_rate_sum,
            "one_minus_state_rate_sum": 1.0 - state_rate_sum,
            "undetermined_reason_rate_sum": sum(reason_rates.values()),
            "normalised_or_repaired": False,
        }
    return audit


def _zero_state_counts() -> dict[str, int]:
    return {state.value: 0 for state in CrossStateDecisionState}


def _zero_reason_counts() -> dict[str, int]:
    return {
        reason.value: 0 for reason in CrossStateDecisionReason if reason.value != "none"
    }


def _profile_counts(
    *,
    availability: ObservationAvailability,
    base_counts: Mapping[str, int],
    base_reason_counts: Mapping[str, int],
) -> tuple[dict[str, int], dict[str, int]]:
    states = _zero_state_counts()
    reasons = _zero_reason_counts()
    total = sum(base_counts.values())
    if availability is ObservationAvailability.OBSERVABLE:
        for state, count in base_counts.items():
            states[state] = count
        for reason, count in base_reason_counts.items():
            reasons[reason] = count
    elif availability is ObservationAvailability.COMPROMISED:
        states[CrossStateDecisionState.UNDETERMINED.value] = total
        reasons[CrossStateDecisionReason.OBSERVATION_COMPROMISED.value] = total
    else:
        states[CrossStateDecisionState.CENSORED.value] = total
        reasons[CrossStateDecisionReason.OBSERVATION_UNAVAILABLE.value] = total
    return states, reasons


def _profile_rates(
    *,
    availability: ObservationAvailability,
    base_rates: Mapping[str, float],
    base_reason_rates: Mapping[str, float],
) -> tuple[dict[str, float], dict[str, float]]:
    states = {state.value: 0.0 for state in CrossStateDecisionState}
    reasons = {
        reason.value: 0.0
        for reason in CrossStateDecisionReason
        if reason.value != "none"
    }
    if availability is ObservationAvailability.OBSERVABLE:
        for state, rate in base_rates.items():
            states[state] = rate
        for reason, rate in base_reason_rates.items():
            reasons[reason] = rate
    elif availability is ObservationAvailability.COMPROMISED:
        states[CrossStateDecisionState.UNDETERMINED.value] = 1.0
        reasons[CrossStateDecisionReason.OBSERVATION_COMPROMISED.value] = 1.0
    else:
        states[CrossStateDecisionState.CENSORED.value] = 1.0
        reasons[CrossStateDecisionReason.OBSERVATION_UNAVAILABLE.value] = 1.0
    return states, reasons


def _rates(counts: Mapping[str, int], total: int) -> dict[str, float]:
    return {name: count / total for name, count in counts.items()}


def _add_counts(target: dict[str, int], source: Mapping[str, int]) -> None:
    for name, count in source.items():
        target[name] += count


def build_v15a_cross_state_result(
    *,
    protocol: Mapping[str, Any],
    locked_summary: Mapping[str, Any],
    v15_observability_contract: Mapping[str, Any],
    v14b_closeout: Mapping[str, Any],
    prefreeze_commit: str,
) -> dict[str, Any]:
    """Execute the deterministic full-factorial V15a expansion."""

    validate_v15a_protocol(
        protocol=protocol,
        locked_summary=locked_summary,
        v15_observability_contract=v15_observability_contract,
        v14b_closeout=v14b_closeout,
    )
    if re.fullmatch(r"[0-9a-f]{40}", prefreeze_commit) is None:
        raise ValueError("prefreeze_commit must be a full lowercase Git SHA")

    global_summary = _mapping(locked_summary, "global_summary")
    base_world_count = int(global_summary["world_count"])
    if base_world_count != 5_880_000:
        raise ValueError("V14b locked world count changed")
    if global_summary.get("observer_retuned") is not False:
        raise ValueError("V14b observer_retuned must remain false")

    base_counts = _counts_from_rates(global_summary, base_world_count)
    base_reason_counts = _reason_counts_from_rates(
        global_summary,
        base_world_count,
        base_counts["undetermined"],
    )
    estimator = PrimaryStreamSupportEstimator()
    profile_rows: list[dict[str, Any]] = []
    expanded_states = _zero_state_counts()
    expanded_reasons = _zero_reason_counts()
    availability_profile_counts = {
        availability.value: 0 for availability in ObservationAvailability
    }
    for profile in prefrozen_support_profiles():
        estimate: PrimaryStreamSupportEstimate = estimator.estimate(
            profile.measurements()
        )
        states, reasons = _profile_counts(
            availability=estimate.availability,
            base_counts=base_counts,
            base_reason_counts=base_reason_counts,
        )
        _add_counts(expanded_states, states)
        _add_counts(expanded_reasons, reasons)
        availability_profile_counts[estimate.availability.value] += 1
        profile_rows.append(
            {
                "name": profile.name,
                "availability": estimate.availability.value,
                "limiting_component": estimate.limiting_component,
                "support_ceiling": estimate.support_ceiling,
                "base_worlds": base_world_count,
                "final_state_counts": states,
                "reason_counts": reasons,
            }
        )

    profile_count = len(profile_rows)
    expanded_world_count = base_world_count * profile_count
    if sum(expanded_states.values()) != expanded_world_count:
        raise AssertionError("expanded state counts do not sum to expanded worlds")

    regime_means = _mapping(locked_summary, "regime_means")
    if set(regime_means) != set(PHYSICAL_REGIMES):
        raise ValueError("locked physical regimes changed")
    if base_world_count % len(PHYSICAL_REGIMES) != 0:
        raise ValueError("locked worlds are not balanced over physical regimes")
    worlds_per_regime = base_world_count // len(PHYSICAL_REGIMES)
    regime_rate_audit = audit_locked_regime_rates(locked_summary)
    regime_matrix: dict[str, Any] = {}
    for regime in PHYSICAL_REGIMES:
        regime_section = _mapping(regime_means, regime)
        regime_base_rates = _state_rates(regime_section)
        regime_reason_rates = _reason_rates(
            regime_section, regime_base_rates["undetermined"]
        )
        by_availability: dict[str, Any] = {}
        for availability in ObservationAvailability:
            multiplicity = availability_profile_counts[availability.value]
            states, reasons = _profile_rates(
                availability=availability,
                base_rates=regime_base_rates,
                base_reason_rates=regime_reason_rates,
            )
            by_availability[availability.value] = {
                "profile_count": multiplicity,
                "final_state_rates": states,
                "reason_rates": reasons,
            }
        regime_matrix[regime] = {
            "locked_regime_mean_rates": regime_base_rates,
            "locked_state_rate_sum": regime_rate_audit[regime]["state_rate_sum"],
            "one_minus_locked_state_rate_sum": regime_rate_audit[regime][
                "one_minus_state_rate_sum"
            ],
            "by_availability": by_availability,
        }

    global_rates = _state_rates(global_summary)
    equal_regime_mean_rates = {
        state: sum(
            regime_matrix[regime]["locked_regime_mean_rates"][state]
            for regime in PHYSICAL_REGIMES
        )
        / len(PHYSICAL_REGIMES)
        for state in BASE_STATES
    }
    parent_summary_consistency = {
        "global_rates": global_rates,
        "equal_mean_of_locked_regime_rates": equal_regime_mean_rates,
        "global_minus_equal_regime_mean": {
            state: global_rates[state] - equal_regime_mean_rates[state]
            for state in BASE_STATES
        },
        "within_regime_rate_sum_audit": regime_rate_audit,
        "regime_rates_coerced_to_integer_counts": False,
        "regime_rates_normalised_or_repaired": False,
        "interpretation": (
            "locked global counts are authoritative for global expansion; "
            "locked regime means are retained as rates and any discrepancy is "
            "reported without repair"
        ),
    }

    target_present_base_worlds = worlds_per_regime * len(TARGET_PRESENT_REGIMES)
    observable_false_negative_count = round(
        float(global_summary["forced_binary_false_negative_rate"])
        * target_present_base_worlds
    )
    false_negative_by_availability = {
        "observable": {
            "profile_count": 1,
            "target_present_worlds": target_present_base_worlds,
            "false_negative_count": observable_false_negative_count,
            "false_negative_rate": float(
                global_summary["forced_binary_false_negative_rate"]
            ),
        },
        "compromised": {
            "profile_count": 5,
            "target_present_worlds": target_present_base_worlds * 5,
            "false_negative_count": target_present_base_worlds * 5,
            "false_negative_rate": 1.0,
        },
        "unobservable": {
            "profile_count": 5,
            "target_present_worlds": target_present_base_worlds * 5,
            "false_negative_count": target_present_base_worlds * 5,
            "false_negative_rate": 1.0,
        },
    }
    total_target_present = target_present_base_worlds * profile_count
    total_forced_false_negatives = sum(
        row["false_negative_count"] for row in false_negative_by_availability.values()
    )

    observable_width = float(global_summary["mean_partial_identification_width"])
    lattice_weighted_width = (observable_width + 5.0 + 5.0) / profile_count
    quiet_cross = regime_matrix["baseline"]["by_availability"]

    measurement_payload = {
        "support_profile_results": profile_rows,
        "expanded_global": {
            "base_world_count": base_world_count,
            "support_profile_count": profile_count,
            "expanded_world_count": expanded_world_count,
            "availability_profile_counts": availability_profile_counts,
            "final_state_counts": expanded_states,
            "final_state_rates": _rates(expanded_states, expanded_world_count),
            "reason_counts": expanded_reasons,
            "reason_rates": _rates(expanded_reasons, expanded_world_count),
        },
        "physical_regime_by_observation_availability": regime_matrix,
        "parent_summary_consistency": parent_summary_consistency,
        "quiet_baseline_cross": {
            "physical_regime": "baseline",
            "observable": quiet_cross["observable"],
            "compromised": quiet_cross["compromised"],
            "unobservable": quiet_cross["unobservable"],
        },
        "forced_binary_comparator": {
            "unsafe_mapping": (
                "target=>present; baseline/nuisance/undetermined/censored=>absent"
            ),
            "target_present_regimes": list(TARGET_PRESENT_REGIMES),
            "by_availability": false_negative_by_availability,
            "lattice_weighted_false_negative_count": (total_forced_false_negatives),
            "lattice_weighted_target_present_worlds": total_target_present,
            "lattice_weighted_false_negative_rate": (
                total_forced_false_negatives / total_target_present
            ),
            "false_positive_rate": 0.0,
            "warning": (
                "the lattice weighting is a designed factorial weighting, not "
                "field prevalence; the comparator is deliberately unsafe"
            ),
        },
        "partial_identification": {
            "width_definition": (
                "baseline + undetermined + censored probability under each "
                "prefrozen support profile"
            ),
            "observable_width": observable_width,
            "compromised_width": 1.0,
            "unobservable_width": 1.0,
            "lattice_weighted_width": lattice_weighted_width,
        },
    }
    measurement_digest = canonical_json_sha256(measurement_payload)

    return {
        "schema": "insepi-v15a-cross-state-observability-result-v1",
        "status": "locked-first-deterministic-expansion",
        "provenance": {
            "prefreeze_commit": prefreeze_commit,
            "protocol_canonical_sha256": canonical_json_sha256(protocol),
            "v14b_locked_summary_canonical_sha256": (
                FROZEN_CANONICAL_JSON_SHA256["locked_summary"]
            ),
            "v14b_phase_surface_sha256": FROZEN_V14B_PHASE_SURFACE_SHA256,
            "v15_observability_contract_canonical_sha256": (
                V15_OBSERVABILITY_CONTRACT_SHA256
            ),
            "measurement_payload_canonical_sha256": measurement_digest,
            "observer_retuned": False,
            "parent_worlds_regenerated": False,
        },
        "estimand": (
            "final epistemic state conditional on frozen physical regime and "
            "independently assigned primary-stream observation support"
        ),
        "measurement": measurement_payload,
        "locked_interpretation": {
            "supported": (
                "across every frozen physical regime, including quiet baseline, "
                "observation compromise creates reason-tagged U and unavailable "
                "observation creates censorship rather than target absence"
            ),
            "third_world": (
                "censored observation is an epistemic state of the same universe, "
                "not a third physical cause and not evidence of biological absence"
            ),
            "forced_binary_result": (
                "coercing U and censored cases to absence makes false-negative "
                "risk a direct function of the designed observation condition"
            ),
            "not_supported": (
                "field prevalence, calibrated field observability, animal intent, "
                "or superiority over every possible binary classifier"
            ),
        },
        "claim_ceiling": (
            "Deterministic closed-world expansion of already locked V14b counts "
            "under prefrozen synthetic V15 support profiles; software-semantic "
            "evidence only, with no new pixels, field calibration, or observer "
            "performance claim."
        ),
    }
