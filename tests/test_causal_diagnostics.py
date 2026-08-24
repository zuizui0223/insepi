from __future__ import annotations

import inspect

import numpy as np
import pytest

from interaction_sensing.causal_diagnostics import (
    TrainingCase,
    diagnose_interventions,
    fit_intervention_model,
    restrict_classes_by_fault_audit,
)
from interaction_sensing.simulation import causal_intervention_v12 as v12


def test_generic_model_accepts_arbitrary_class_and_intervention_names() -> None:
    cases = [
        TrainingCase("alpha", {"poke-x": (1.0, 0.0), "poke-y": (0.2, 0.1)}),
        TrainingCase("alpha", {"poke-x": (0.9, 0.1), "poke-y": (0.1, 0.2)}),
        TrainingCase("beta", {"poke-x": (0.0, 1.0), "poke-y": (0.2, 0.8)}),
        TrainingCase("beta", {"poke-x": (0.1, 0.9), "poke-y": (0.3, 0.7)}),
    ]
    model = fit_intervention_model(cases, classes=("alpha", "beta"), interventions=("poke-x", "poke-y"))
    result = diagnose_interventions(
        model,
        {"poke-x": (1.1, 0.0), "poke-y": (0.0, 0.1)},
        budget=1,
    )
    assert result.predicted_class == "alpha"
    assert set(result.intervention_order) == {"poke-x", "poke-y"}


def test_fault_audit_restricts_hypothesis_set_without_revealing_cause() -> None:
    classes = ("event", "no_fault", "risk", "shared")
    assert restrict_classes_by_fault_audit(
        classes, audit_available=False, fault_present=None, no_fault_label="no_fault"
    ) == classes
    assert restrict_classes_by_fault_audit(
        classes, audit_available=True, fault_present=False, no_fault_label="no_fault"
    ) == ("no_fault",)
    assert restrict_classes_by_fault_audit(
        classes, audit_available=True, fault_present=True, no_fault_label="no_fault"
    ) == ("event", "risk", "shared")


def test_generic_diagnosis_signature_has_no_truth_label_argument() -> None:
    names = set(inspect.signature(diagnose_interventions).parameters)
    assert "true_class" not in names
    assert "failure_class" not in names
    assert "mechanism" not in names


def _v12_training(replicates: int = 40):
    episodes = [
        v12.generate_episode("development", label, intensity, rep)
        for label in v12.CLASSES
        for intensity in (0.35, 0.65, 0.95)
        for rep in range(replicates)
    ]
    generic = [
        TrainingCase(ep.failure_class, {name: ep.observed.responses[name] for name in v12.ACTIVE_INTERVENTIONS})
        for ep in episodes
    ]
    return episodes, generic


def test_generic_dual_model_matches_v12_centroids() -> None:
    episodes, generic_cases = _v12_training()
    specific = v12.fit_model(episodes, "interventional_dual_observer")
    generic = fit_intervention_model(
        generic_cases,
        classes=v12.CLASSES,
        interventions=v12.ACTIVE_INTERVENTIONS,
    )
    for intervention in v12.ACTIVE_INTERVENTIONS:
        assert np.allclose(generic.means[intervention], specific.means[intervention], atol=0.0, rtol=0.0)
        assert np.allclose(generic.scales[intervention], specific.scales[intervention], atol=0.0, rtol=0.0)
        for label in v12.CLASSES:
            assert np.allclose(
                generic.centroids[label][intervention],
                specific.centroids[label][intervention],
                atol=0.0,
                rtol=0.0,
            )


def test_generic_dual_api_has_exact_v12_intervention_and_diagnosis_parity() -> None:
    episodes, generic_cases = _v12_training()
    specific = v12.fit_model(episodes, "interventional_dual_observer")
    generic = fit_intervention_model(
        generic_cases,
        classes=v12.CLASSES,
        interventions=v12.ACTIVE_INTERVENTIONS,
    )
    checked = 0
    for label in v12.CLASSES:
        for intensity in (0.35, 0.65, 0.95):
            for rep in range(12):
                ep = v12.generate_episode("heldout", label, intensity, rep)
                specific_result = v12.diagnose(specific, ep.observed, budget=2)
                allowed = restrict_classes_by_fault_audit(
                    v12.CLASSES,
                    audit_available=ep.observed.audit_available,
                    fault_present=ep.observed.audit_fault_present,
                    no_fault_label="no_fault",
                )
                generic_result = diagnose_interventions(
                    generic,
                    ep.observed.responses,
                    budget=2,
                    allowed_classes=allowed,
                )
                assert generic_result.predicted_class == specific_result.predicted_class
                assert generic_result.intervention_order == specific_result.intervention_order
                assert generic_result.predictions_by_prefix == specific_result.predictions_by_prefix
                assert generic_result.full_battery_prediction == specific_result.full_battery_prediction
                checked += 1
    assert checked == 4 * 3 * 12


def test_linear_scalar_projection_can_destroy_interventional_identifiability() -> None:
    # Two classes have distinct mirrored two-channel signatures but identical
    # 50/50 scalar projections under every intervention.
    dual_cases = [
        TrainingCase("left", {"i1": (1.0, 0.0), "i2": (0.8, 0.2)}),
        TrainingCase("left", {"i1": (0.98, 0.02), "i2": (0.78, 0.22)}),
        TrainingCase("right", {"i1": (0.0, 1.0), "i2": (0.2, 0.8)}),
        TrainingCase("right", {"i1": (0.02, 0.98), "i2": (0.22, 0.78)}),
    ]
    dual = fit_intervention_model(dual_cases, classes=("left", "right"), interventions=("i1", "i2"))
    dual_result = diagnose_interventions(dual, {"i1": (0.99, 0.01), "i2": (0.79, 0.21)}, budget=1)
    assert dual_result.predicted_class == "left"

    scalar_cases = [
        TrainingCase(case.label, {name: ((values[0] + values[1]) / 2.0,) for name, values in case.responses.items()})
        for case in dual_cases
    ]
    scalar = fit_intervention_model(scalar_cases, classes=("left", "right"), interventions=("i1", "i2"))
    for intervention in ("i1", "i2"):
        assert np.allclose(scalar.centroids["left"][intervention], scalar.centroids["right"][intervention])


def test_input_validation_rejects_missing_intervention_and_bad_audit_contract() -> None:
    with pytest.raises(ValueError):
        fit_intervention_model(
            [TrainingCase("a", {"x": (1.0,)}), TrainingCase("b", {"y": (2.0,)})],
            classes=("a", "b"),
            interventions=("x", "y"),
        )
    with pytest.raises(ValueError):
        restrict_classes_by_fault_audit(
            ("a", "no_fault"), audit_available=False, fault_present=True, no_fault_label="no_fault"
        )
