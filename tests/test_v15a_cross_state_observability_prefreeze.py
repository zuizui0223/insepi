from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from interaction_sensing.cross_state_observability_v15a import (
    CrossStateDecisionReason,
    CrossStateDecisionState,
    apply_observation_layer,
    prefrozen_support_profiles,
    support_profile_specifications,
    validate_v15a_protocol,
)
from interaction_sensing.observation_triad import ObservationAvailability
from interaction_sensing.support_estimation import PrimaryStreamSupportEstimator

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "benchmarks/v15a_cross_state_observability_protocol.json"
SUMMARY_PATH = ROOT / "benchmarks/v14b_frozen_ternary_phase_surface_result.json"
V15_CONTRACT_PATH = ROOT / "benchmarks/v15_observability_estimator_contract.json"
V14B_CLOSEOUT_PATH = ROOT / "benchmarks/v14b_prefield_programming_closeout.json"


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _sources() -> dict[str, dict[str, object]]:
    return {
        "protocol": _read(PROTOCOL_PATH),
        "locked_summary": _read(SUMMARY_PATH),
        "v15_observability_contract": _read(V15_CONTRACT_PATH),
        "v14b_closeout": _read(V14B_CLOSEOUT_PATH),
    }


def test_protocol_and_all_parent_identities_are_prefrozen() -> None:
    validate_v15a_protocol(**_sources())


def test_support_lattice_crosses_every_component_without_physical_inputs() -> None:
    profiles = prefrozen_support_profiles()
    estimator = PrimaryStreamSupportEstimator()
    estimates = [estimator.estimate(profile.measurements()) for profile in profiles]

    assert len(profiles) == 11
    assert [estimate.availability for estimate in estimates].count(
        ObservationAvailability.OBSERVABLE
    ) == 1
    assert [estimate.availability for estimate in estimates].count(
        ObservationAvailability.COMPROMISED
    ) == 5
    assert [estimate.availability for estimate in estimates].count(
        ObservationAvailability.UNOBSERVABLE
    ) == 5
    assert (
        support_profile_specifications()
        == _sources()["protocol"]["support_factor"]["profiles"]
    )


@pytest.mark.parametrize("base_state", ["baseline", "target", "nuisance"])
def test_unobservable_is_censored_for_every_determined_physical_output(
    base_state: str,
) -> None:
    decision = apply_observation_layer(
        base_state=base_state,
        base_reason="none",
        availability=ObservationAvailability.UNOBSERVABLE,
    )

    assert decision.state is CrossStateDecisionState.CENSORED
    assert decision.reason is CrossStateDecisionReason.OBSERVATION_UNAVAILABLE
    assert decision.base_state == base_state


def test_quiet_observable_is_retained_but_quiet_compromised_is_u() -> None:
    observable = apply_observation_layer(
        base_state="baseline",
        base_reason="none",
        availability=ObservationAvailability.OBSERVABLE,
    )
    compromised = apply_observation_layer(
        base_state="baseline",
        base_reason="none",
        availability=ObservationAvailability.COMPROMISED,
    )

    assert observable.state is CrossStateDecisionState.BASELINE
    assert observable.reason is CrossStateDecisionReason.NONE
    assert compromised.state is CrossStateDecisionState.UNDETERMINED
    assert compromised.reason is CrossStateDecisionReason.OBSERVATION_COMPROMISED


def test_observable_preserves_each_existing_u_reason() -> None:
    for reason in ("information_absent", "overlap_or_attribution"):
        decision = apply_observation_layer(
            base_state="undetermined",
            base_reason=reason,
            availability=ObservationAvailability.OBSERVABLE,
        )
        assert decision.state is CrossStateDecisionState.UNDETERMINED
        assert decision.reason.value == reason


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda source: source["support_factor"].__setitem__(
                "observable_threshold", 0.71
            ),
            "observable threshold changed",
        ),
        (
            lambda source: source["decision_layer"].__setitem__(
                "unobservable_is_target_absence", True
            ),
            "decision layer changed",
        ),
        (
            lambda source: source["retained_parent_freeze"].__setitem__(
                "familywise_alpha", 0.10
            ),
            "retained parent freeze changed",
        ),
    ],
)
def test_protocol_changes_fail_closed(mutation, message: str) -> None:
    sources = _sources()
    protocol = deepcopy(sources["protocol"])
    mutation(protocol)
    sources["protocol"] = protocol

    with pytest.raises(ValueError, match=message):
        validate_v15a_protocol(**sources)
