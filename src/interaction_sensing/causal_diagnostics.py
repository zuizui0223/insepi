"""Generic intervention-response diagnosis utilities.

The API is intentionally observer-agnostic.  A caller supplies, for each
training case, a class label and a vector response for each named intervention.
The model preserves those response dimensions, chooses interventions by
centroid separation, and diagnoses by distance to development centroids.

This module does not know PolliPi, InsePi, V12, event truth, disturbance truth,
or any ecological failure family.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True, slots=True)
class TrainingCase:
    label: str
    responses: Mapping[str, Sequence[float]]


@dataclass(frozen=True, slots=True)
class DiagnosticModel:
    classes: tuple[str, ...]
    interventions: tuple[str, ...]
    means: Mapping[str, np.ndarray]
    scales: Mapping[str, np.ndarray]
    centroids: Mapping[str, Mapping[str, np.ndarray]]


@dataclass(frozen=True, slots=True)
class DiagnosticResult:
    predicted_class: str
    intervention_order: tuple[str, ...]
    predictions_by_prefix: tuple[str, ...]
    full_battery_prediction: str


def fit_intervention_model(
    cases: Sequence[TrainingCase],
    *,
    classes: Sequence[str],
    interventions: Sequence[str],
) -> DiagnosticModel:
    class_tuple = tuple(classes)
    intervention_tuple = tuple(interventions)
    if not cases:
        raise ValueError("at least one training case is required")
    if len(set(class_tuple)) != len(class_tuple) or not class_tuple:
        raise ValueError("classes must be non-empty and unique")
    if len(set(intervention_tuple)) != len(intervention_tuple) or not intervention_tuple:
        raise ValueError("interventions must be non-empty and unique")
    if any(case.label not in class_tuple for case in cases):
        raise ValueError("training case contains a label outside classes")
    missing = [label for label in class_tuple if not any(case.label == label for case in cases)]
    if missing:
        raise ValueError(f"training data lack classes: {missing}")

    means: dict[str, np.ndarray] = {}
    scales: dict[str, np.ndarray] = {}
    centroids: dict[str, dict[str, np.ndarray]] = {label: {} for label in class_tuple}

    for intervention in intervention_tuple:
        rows: list[np.ndarray] = []
        dimension: int | None = None
        for case in cases:
            if intervention not in case.responses:
                raise ValueError(f"missing intervention response: {intervention}")
            vector = np.asarray(case.responses[intervention], dtype=float)
            if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
                raise ValueError("each intervention response must be a finite one-dimensional vector")
            if dimension is None:
                dimension = int(vector.size)
            elif vector.size != dimension:
                raise ValueError("response dimension changed within an intervention")
            rows.append(vector)

        x = np.vstack(rows)
        mu = x.mean(axis=0)
        scale = x.std(axis=0)
        scale = np.where(scale > 1e-12, scale, 1.0)
        z = (x - mu) / scale
        means[intervention] = mu
        scales[intervention] = scale
        for label in class_tuple:
            indices = [index for index, case in enumerate(cases) if case.label == label]
            centroids[label][intervention] = z[indices].mean(axis=0)

    return DiagnosticModel(class_tuple, intervention_tuple, means, scales, centroids)


def restrict_classes_by_fault_audit(
    classes: Sequence[str],
    *,
    audit_available: bool,
    fault_present: bool | None,
    no_fault_label: str = "no_fault",
) -> tuple[str, ...]:
    class_tuple = tuple(classes)
    if no_fault_label not in class_tuple:
        raise ValueError("no_fault_label is not present in classes")
    if not audit_available:
        if fault_present is not None:
            raise ValueError("fault_present must be None when audit is unavailable")
        return class_tuple
    if fault_present is None:
        raise ValueError("an available audit must provide fault_present")
    if fault_present is False:
        return (no_fault_label,)
    return tuple(label for label in class_tuple if label != no_fault_label)


def _validate_observed(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
) -> None:
    for intervention in model.interventions:
        if intervention not in observed:
            raise ValueError(f"missing observed response for intervention {intervention}")
        vector = np.asarray(observed[intervention], dtype=float)
        if vector.ndim != 1 or vector.shape != model.means[intervention].shape:
            raise ValueError(f"response shape mismatch for {intervention}")
        if not np.all(np.isfinite(vector)):
            raise ValueError("observed response contains a non-finite value")


def _z_response(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
    intervention: str,
) -> np.ndarray:
    raw = np.asarray(observed[intervention], dtype=float)
    return (raw - model.means[intervention]) / model.scales[intervention]


def class_distance(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
    selected: Sequence[str],
    label: str,
) -> float:
    if label not in model.classes:
        raise ValueError(label)
    return float(sum(
        np.sum((_z_response(model, observed, intervention) - model.centroids[label][intervention]) ** 2)
        for intervention in selected
    ))


def predict_class(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
    selected: Sequence[str],
    *,
    allowed_classes: Sequence[str] | None = None,
) -> str:
    allowed = tuple(model.classes if allowed_classes is None else allowed_classes)
    if not allowed or any(label not in model.classes for label in allowed):
        raise ValueError("allowed_classes must be a non-empty subset of model classes")
    if len(allowed) == 1:
        return allowed[0]
    if not selected:
        return sorted(allowed)[0]
    scored = sorted(
        ((class_distance(model, observed, selected, label), label) for label in allowed),
        key=lambda item: (item[0], item[1]),
    )
    return scored[0][1]


def centroid_separation(
    model: DiagnosticModel,
    intervention: str,
    a: str,
    b: str,
) -> float:
    return float(np.linalg.norm(model.centroids[a][intervention] - model.centroids[b][intervention]))


def choose_first_intervention(
    model: DiagnosticModel,
    remaining: Sequence[str],
    *,
    allowed_classes: Sequence[str] | None = None,
) -> str:
    allowed = tuple(model.classes if allowed_classes is None else allowed_classes)
    if len(allowed) <= 1:
        raise ValueError("a causal intervention is unnecessary for one remaining class")
    choices = tuple(remaining)
    if not choices:
        raise ValueError("no interventions remain")
    if any(name not in model.interventions for name in choices):
        raise ValueError("remaining contains an unknown intervention")
    scored: list[tuple[float, str]] = []
    for intervention in choices:
        pairwise = [
            centroid_separation(model, intervention, a, b)
            for index, a in enumerate(allowed)
            for b in allowed[index + 1 :]
        ]
        scored.append((min(pairwise), intervention))
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][1]


def choose_next_intervention(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
    selected: Sequence[str],
    remaining: Sequence[str],
    *,
    allowed_classes: Sequence[str] | None = None,
) -> str:
    allowed = tuple(model.classes if allowed_classes is None else allowed_classes)
    if len(allowed) <= 1:
        raise ValueError("a causal intervention is unnecessary for one remaining class")
    if not selected:
        return choose_first_intervention(model, remaining, allowed_classes=allowed)
    ranked = sorted(
        ((class_distance(model, observed, selected, label), label) for label in allowed),
        key=lambda item: (item[0], item[1]),
    )
    a, b = ranked[0][1], ranked[1][1]
    scored = [(centroid_separation(model, intervention, a, b), intervention) for intervention in remaining]
    if not scored:
        raise ValueError("no interventions remain")
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][1]


def diagnose_interventions(
    model: DiagnosticModel,
    observed: Mapping[str, Sequence[float]],
    *,
    budget: int,
    allowed_classes: Sequence[str] | None = None,
) -> DiagnosticResult:
    _validate_observed(model, observed)
    if not 1 <= budget <= len(model.interventions):
        raise ValueError("budget must be between one and the number of interventions")
    allowed = tuple(model.classes if allowed_classes is None else allowed_classes)
    if len(allowed) == 1:
        prediction = allowed[0]
        return DiagnosticResult(prediction, (), (prediction,), prediction)

    remaining = list(model.interventions)
    selected: list[str] = []
    predictions: list[str] = []
    while len(selected) < budget:
        intervention = (
            choose_first_intervention(model, remaining, allowed_classes=allowed)
            if not selected
            else choose_next_intervention(
                model,
                observed,
                selected,
                remaining,
                allowed_classes=allowed,
            )
        )
        selected.append(intervention)
        remaining.remove(intervention)
        predictions.append(predict_class(model, observed, selected, allowed_classes=allowed))

    full_order = list(selected)
    full_predictions = list(predictions)
    while remaining:
        intervention = choose_next_intervention(
            model,
            observed,
            full_order,
            remaining,
            allowed_classes=allowed,
        )
        full_order.append(intervention)
        remaining.remove(intervention)
        full_predictions.append(predict_class(model, observed, full_order, allowed_classes=allowed))

    return DiagnosticResult(
        predicted_class=predictions[-1],
        intervention_order=tuple(full_order),
        predictions_by_prefix=tuple(full_predictions),
        full_battery_prediction=full_predictions[-1],
    )
