"""Blinded V13 block-level prediction and post-truth evaluation.

Prediction accepts held-out response vectors but no held-out treatment labels.
Treatment truth and actual physical day/scene clusters are joined only by
``evaluate_predictions`` after the prediction ledger has been emitted/frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np

from interaction_sensing.causal_diagnostics import (
    TrainingCase,
    diagnose_interventions,
    fit_intervention_model,
)

PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "benchmarks" / "v13_physical_intervention_protocol.json"
CLASSES = ("event_side", "no_fault", "nuisance_side", "shared_optical")
STRATEGIES = ("event_only", "observability_only", "early_scalar_fusion", "dual_observer_vector")
INTERVENTIONS = ("event_restore", "observability_restore", "shared_restore")


@dataclass(frozen=True, slots=True)
class BlockResponse:
    block_id: str
    split: str
    responses: Mapping[str, tuple[float, float]]


@dataclass(frozen=True, slots=True)
class DevelopmentLabel:
    block_id: str
    treatment_class: str


@dataclass(frozen=True, slots=True)
class HeldoutPrediction:
    block_id: str
    strategy: str
    predicted_class_budget2: str
    predicted_class_after_one: str
    full_battery_prediction: str
    intervention_order: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HeldoutTruth:
    block_id: str
    treatment_class: str
    recording_date_local: str
    physical_scene_code: str


@dataclass(frozen=True, slots=True)
class QcAnnotation:
    block_id: str
    protected_qc: bool
    gross_protocol_violation: bool


def load_protocol() -> dict[str, object]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def protocol_sha256() -> str:
    return hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()


def _vector(pair: tuple[float, float], strategy: str) -> tuple[float, ...]:
    e, o = map(float, pair)
    if not np.isfinite(e) or not np.isfinite(o):
        raise ValueError("V13 response contains a non-finite value")
    if strategy == "event_only":
        return (e,)
    if strategy == "observability_only":
        return (o,)
    if strategy == "early_scalar_fusion":
        return (0.5 * e + 0.5 * o,)
    if strategy == "dual_observer_vector":
        return (e, o)
    raise ValueError(strategy)


def _validate_response(response: BlockResponse) -> None:
    if response.split not in {"development", "heldout"}:
        raise ValueError(response.split)
    if set(response.responses) != set(INTERVENTIONS):
        raise ValueError("V13 block response lacks exact three-intervention battery")
    for pair in response.responses.values():
        if len(pair) != 2:
            raise ValueError("V13 intervention response must be (delta_evidence, delta_observability)")
        _vector(pair, "dual_observer_vector")


def fit_strategy_models(
    development_responses: Sequence[BlockResponse],
    development_labels: Sequence[DevelopmentLabel],
):
    responses_by_id = {row.block_id: row for row in development_responses}
    if len(responses_by_id) != len(development_responses):
        raise ValueError("duplicate development block response")
    labels_by_id = {row.block_id: row.treatment_class for row in development_labels}
    if len(labels_by_id) != len(development_labels):
        raise ValueError("duplicate development label")
    if set(responses_by_id) != set(labels_by_id):
        raise ValueError("development response/label block ids differ")
    if any(label not in CLASSES for label in labels_by_id.values()):
        raise ValueError("development label outside frozen V13 classes")
    for response in development_responses:
        _validate_response(response)
        if response.split != "development":
            raise ValueError("non-development response supplied to training")

    models = {}
    for strategy in STRATEGIES:
        cases = [
            TrainingCase(
                labels_by_id[block_id],
                {
                    intervention: _vector(response.responses[intervention], strategy)
                    for intervention in INTERVENTIONS
                },
            )
            for block_id, response in sorted(responses_by_id.items())
        ]
        models[strategy] = fit_intervention_model(
            cases,
            classes=CLASSES,
            interventions=INTERVENTIONS,
        )
    return models


def predict_heldout(
    models: Mapping[str, object],
    heldout_responses: Sequence[BlockResponse],
) -> tuple[HeldoutPrediction, ...]:
    """Emit held-out predictions without accepting or reading held-out truth."""
    ids = [row.block_id for row in heldout_responses]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate held-out block response")
    output: list[HeldoutPrediction] = []
    for response in sorted(heldout_responses, key=lambda row: row.block_id):
        _validate_response(response)
        if response.split != "heldout":
            raise ValueError("non-heldout response supplied to heldout prediction")
        for strategy in STRATEGIES:
            model = models[strategy]
            observed = {
                intervention: _vector(response.responses[intervention], strategy)
                for intervention in INTERVENTIONS
            }
            diagnosis = diagnose_interventions(model, observed, budget=2)
            output.append(HeldoutPrediction(
                block_id=response.block_id,
                strategy=strategy,
                predicted_class_budget2=diagnosis.predicted_class,
                predicted_class_after_one=diagnosis.predictions_by_prefix[0],
                full_battery_prediction=diagnosis.full_battery_prediction,
                intervention_order=diagnosis.intervention_order,
            ))
    return tuple(output)


def prediction_ledger_sha256(predictions: Sequence[HeldoutPrediction]) -> str:
    rows = [
        {
            "block_id": row.block_id,
            "strategy": row.strategy,
            "predicted_class_budget2": row.predicted_class_budget2,
            "predicted_class_after_one": row.predicted_class_after_one,
            "full_battery_prediction": row.full_battery_prediction,
            "intervention_order": list(row.intervention_order),
        }
        for row in sorted(predictions, key=lambda row: (row.block_id, row.strategy))
    ]
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _cluster_bootstrap_accuracy(
    cluster_scores: Mapping[tuple[str, str], float],
    *,
    resamples: int,
    seed: int,
) -> tuple[float, float]:
    keys = sorted(cluster_scores)
    values = np.asarray([cluster_scores[key] for key in keys], dtype=float)
    rng = np.random.default_rng(seed)
    draws = np.empty(resamples, dtype=float)
    for index in range(resamples):
        chosen = rng.integers(0, len(values), size=len(values))
        draws[index] = float(values[chosen].mean())
    lo, hi = np.quantile(draws, [0.025, 0.975])
    return float(lo), float(hi)


def _claim(summary: Mapping[str, Mapping[str, float]], gross_qc_violation: bool) -> tuple[str, str]:
    dual = summary["dual_observer_vector"]
    comparators = [name for name in STRATEGIES if name != "dual_observer_vector"]
    best = max(summary[name]["heldout_block_localisation_accuracy_budget2"] for name in comparators)
    if (
        dual["heldout_block_localisation_accuracy_budget2"] < best - 0.05
        or dual["shared_optical_recall_budget2"] < 0.50
        or gross_qc_violation
    ):
        return "D", "physical_intervention_identification_not_established"
    if (
        dual["heldout_block_localisation_accuracy_budget2"] >= 0.80
        and dual["heldout_block_localisation_accuracy_budget2"] >= best + 0.10
        and dual["shared_optical_recall_budget2"] >= 0.75
        and dual["no_fault_false_intervention_rate_budget2"] <= 0.20
        and dual["heldout_min_cluster_localisation_accuracy_budget2"] >= 0.65
    ):
        return "A", "material_physical_distinct_channel_advantage"
    if (
        dual["heldout_block_localisation_accuracy_budget2"] >= best
        and dual["shared_optical_recall_budget2"] >= 0.65
        and dual["heldout_min_cluster_localisation_accuracy_budget2"] >= 0.55
    ):
        return "B", "conditional_physical_causal_identification"
    return "C", "mixed_physical_intervention_transfer"


def evaluate_predictions(
    predictions: Sequence[HeldoutPrediction],
    heldout_truth: Sequence[HeldoutTruth],
    qc_annotations: Sequence[QcAnnotation],
) -> dict[str, object]:
    """Join held-out class truth and actual physical clusters only after prediction emission."""
    truth_by_id = {row.block_id: row for row in heldout_truth}
    if len(truth_by_id) != len(heldout_truth):
        raise ValueError("duplicate held-out truth block id")
    if any(row.treatment_class not in CLASSES for row in heldout_truth):
        raise ValueError("held-out truth contains an unknown treatment class")
    if any(not row.recording_date_local or not row.physical_scene_code for row in heldout_truth):
        raise ValueError("held-out truth lacks actual physical cluster metadata")

    expected_pairs = {(block_id, strategy) for block_id in truth_by_id for strategy in STRATEGIES}
    prediction_pairs = {(row.block_id, row.strategy) for row in predictions}
    if prediction_pairs != expected_pairs or len(predictions) != len(expected_pairs):
        raise ValueError("prediction ledger does not contain exactly four strategies for every held-out block")

    protected = [row for row in qc_annotations if row.protected_qc]
    gross_qc_violation = any(row.gross_protocol_violation for row in protected)
    violation_rate = (
        sum(row.gross_protocol_violation for row in protected) / len(protected)
        if protected else 0.0
    )

    protocol = load_protocol()
    bootstrap = protocol["analysis"]["cluster_bootstrap"]
    summaries: dict[str, dict[str, float]] = {}
    clusters_out: dict[str, dict[str, float]] = {}

    for strategy in STRATEGIES:
        rows = [row for row in predictions if row.strategy == strategy]
        correct: list[bool] = []
        one_correct: list[bool] = []
        full_correct: list[bool] = []
        shared_hits: list[bool] = []
        no_fault_false: list[bool] = []
        fault_wrong: list[bool] = []
        by_cluster: dict[tuple[str, str], list[bool]] = {}
        for row in rows:
            truth = truth_by_id[row.block_id]
            is_correct = row.predicted_class_budget2 == truth.treatment_class
            correct.append(is_correct)
            one_correct.append(row.predicted_class_after_one == truth.treatment_class)
            full_correct.append(row.full_battery_prediction == truth.treatment_class)
            if truth.treatment_class == "shared_optical":
                shared_hits.append(row.predicted_class_budget2 == "shared_optical")
            if truth.treatment_class == "no_fault":
                no_fault_false.append(row.predicted_class_budget2 != "no_fault")
            else:
                fault_wrong.append(not is_correct)
            by_cluster.setdefault(
                (truth.recording_date_local, truth.physical_scene_code), []
            ).append(is_correct)
        cluster_scores = {key: sum(values) / len(values) for key, values in by_cluster.items()}
        if len(cluster_scores) != int(protocol["analysis"]["heldout_cluster_count"]):
            raise ValueError(f"expected six held-out physical day_x_scene clusters, got {len(cluster_scores)}")
        if any(len(values) != 12 for values in by_cluster.values()):
            raise ValueError("each held-out physical day_x_scene cluster must contain exactly 12 blocks")
        ci_lo, ci_hi = _cluster_bootstrap_accuracy(
            cluster_scores,
            resamples=int(bootstrap["resamples"]),
            seed=int(bootstrap["seed"]),
        )
        summaries[strategy] = {
            "heldout_block_localisation_accuracy_budget2": sum(correct) / len(correct),
            "heldout_cluster_mean_localisation_accuracy_budget2": float(mean(cluster_scores.values())),
            "heldout_min_cluster_localisation_accuracy_budget2": min(cluster_scores.values()),
            "heldout_cluster_bootstrap_ci_low": ci_lo,
            "heldout_cluster_bootstrap_ci_high": ci_hi,
            "accuracy_after_one_intervention": sum(one_correct) / len(one_correct),
            "shared_optical_recall_budget2": sum(shared_hits) / len(shared_hits),
            "no_fault_false_intervention_rate_budget2": sum(no_fault_false) / len(no_fault_false),
            "wrong_treatment_class_intervention_rate_budget2": sum(fault_wrong) / len(fault_wrong),
            "full_battery_localisation_accuracy": sum(full_correct) / len(full_correct),
        }
        clusters_out[strategy] = {
            f"{date}|{scene}": score for (date, scene), score in sorted(cluster_scores.items())
        }

    level, label = _claim(summaries, gross_qc_violation)
    return {
        "schema": "interaction-sensing-v13-physical-evaluation-v1",
        "protocol_sha256": protocol_sha256(),
        "prediction_ledger_sha256": prediction_ledger_sha256(predictions),
        "heldout_block_count": len(truth_by_id),
        "cluster_identity_source": "completed capture log: recording_date_local x physical_scene_code",
        "protected_qc_annotation_count": len(protected),
        "protected_qc_protocol_violation_rate": violation_rate,
        "gross_qc_violation": gross_qc_violation,
        "strategies": summaries,
        "per_cluster_accuracy": clusters_out,
        "claim": {"level": level, "label": label},
    }
