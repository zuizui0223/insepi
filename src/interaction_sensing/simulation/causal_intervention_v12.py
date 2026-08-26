"""V12 controlled causal-intervention development benchmark.

V11 showed that static raw/quadrant contradiction features did not identify
causal failure class under mechanism-subtype shift. V12 changes the experiment,
not the V11 classifier: every strategy gets the same controlled interventions,
the same intervention budget and the same diagnostic algorithm. Only the
observer representation differs (E only, O only, early scalar fusion, or the
unfused paired E/O response).
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import mean
from typing import Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_PATH = ROOT / "benchmarks" / "v12_causal_intervention_protocol.json"
SCHEMA = "interaction-sensing-v12-causal-intervention-result-v1"
CLASSES = ("event_module", "no_fault", "observability_module", "shared_representation")
STRATEGIES = ("event_only", "observability_only", "early_scalar_fusion", "interventional_dual_observer")
ACTIVE_INTERVENTIONS = ("event_restore", "observability_restore", "shared_restore")


@dataclass(frozen=True, slots=True)
class ObservableEpisode:
    responses: Mapping[str, tuple[float, float]]
    audit_available: bool
    audit_fault_present: bool | None


@dataclass(frozen=True, slots=True)
class CausalEpisode:
    split: str
    failure_class: str
    mechanism: str
    intensity: float
    replicate: int
    observed: ObservableEpisode


@dataclass(frozen=True, slots=True)
class StrategyModel:
    strategy: str
    means: Mapping[str, np.ndarray]
    scales: Mapping[str, np.ndarray]
    centroids: Mapping[str, Mapping[str, np.ndarray]]


@dataclass(frozen=True, slots=True)
class Diagnosis:
    predicted_class: str
    intervention_order: tuple[str, ...]
    predictions_by_prefix: tuple[str, ...]
    full_battery_prediction: str


def load_protocol() -> dict[str, object]:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def protocol_sha256() -> str:
    return hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()


def _seed(domain: str, *parts: object) -> int:
    text = "|".join((domain, *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def _audit_assignment(split: str, failure_class: str, intensity: float, replicate: int) -> bool:
    protocol = load_protocol()
    domain = str(protocol["protected_random_audit"]["domain"])
    text = f"{domain}|{split}|{failure_class}|{intensity:.2f}|{replicate}"
    return hashlib.sha256(text.encode("utf-8")).digest()[0] < 64


def _mechanism(split: str, failure_class: str) -> str:
    protocol = load_protocol()
    return str(protocol["mechanism_subtypes"][split][failure_class])


def generate_episode(split: str, failure_class: str, intensity: float, replicate: int) -> CausalEpisode:
    if split not in {"development", "heldout"}:
        raise ValueError(split)
    if failure_class not in CLASSES:
        raise ValueError(failure_class)
    protocol = load_protocol()
    mechanism = _mechanism(split, failure_class)
    topology = protocol["causal_response_topology"][split][failure_class]
    multiplier = float(intensity) if split == "development" else sqrt(float(intensity))
    noise_sd = float(protocol["simulation"]["paired_response_noise_sd"])
    rho = float(protocol["simulation"]["paired_channel_noise_correlation"])
    domain = str(protocol["simulation"]["seed_domain"])
    responses: dict[str, tuple[float, float]] = {}
    for intervention in ACTIVE_INTERVENTIONS:
        mu_e, mu_o = map(float, topology[intervention])
        rng = np.random.default_rng(
            _seed(domain, split, mechanism, f"{intensity:.2f}", replicate, intervention)
        )
        common = float(rng.normal())
        eps_e = float(rng.normal())
        eps_o = float(rng.normal())
        noise_e = noise_sd * (sqrt(rho) * common + sqrt(1.0 - rho) * eps_e)
        noise_o = noise_sd * (sqrt(rho) * common + sqrt(1.0 - rho) * eps_o)
        responses[intervention] = (mu_e * multiplier + noise_e, mu_o * multiplier + noise_o)
    audited = _audit_assignment(split, failure_class, float(intensity), int(replicate))
    observed = ObservableEpisode(
        responses=responses,
        audit_available=audited,
        audit_fault_present=(failure_class != "no_fault") if audited else None,
    )
    return CausalEpisode(split, failure_class, mechanism, float(intensity), int(replicate), observed)


def representation(response: tuple[float, float], strategy: str) -> np.ndarray:
    delta_e, delta_o = map(float, response)
    if strategy == "event_only":
        return np.asarray([delta_e], dtype=float)
    if strategy == "observability_only":
        return np.asarray([delta_o], dtype=float)
    if strategy == "early_scalar_fusion":
        return np.asarray([0.5 * delta_e + 0.5 * delta_o], dtype=float)
    if strategy == "interventional_dual_observer":
        return np.asarray([delta_e, delta_o], dtype=float)
    raise ValueError(strategy)


def fit_model(episodes: Sequence[CausalEpisode], strategy: str) -> StrategyModel:
    if strategy not in STRATEGIES:
        raise ValueError(strategy)
    means: dict[str, np.ndarray] = {}
    scales: dict[str, np.ndarray] = {}
    centroids: dict[str, dict[str, np.ndarray]] = {label: {} for label in CLASSES}
    for intervention in ACTIVE_INTERVENTIONS:
        x = np.vstack([representation(ep.observed.responses[intervention], strategy) for ep in episodes])
        mu = x.mean(axis=0)
        scale = x.std(axis=0)
        scale = np.where(scale > 1e-12, scale, 1.0)
        z = (x - mu) / scale
        means[intervention] = mu
        scales[intervention] = scale
        for label in CLASSES:
            indices = [index for index, ep in enumerate(episodes) if ep.failure_class == label]
            centroids[label][intervention] = z[indices].mean(axis=0)
    return StrategyModel(strategy, means, scales, centroids)


def _allowed_classes(observed: ObservableEpisode) -> tuple[str, ...]:
    if not observed.audit_available:
        return CLASSES
    if observed.audit_fault_present is False:
        return ("no_fault",)
    return tuple(label for label in CLASSES if label != "no_fault")


def _z_response(model: StrategyModel, observed: ObservableEpisode, intervention: str) -> np.ndarray:
    raw = representation(observed.responses[intervention], model.strategy)
    return (raw - model.means[intervention]) / model.scales[intervention]


def _class_distance(
    model: StrategyModel,
    observed: ObservableEpisode,
    selected: Sequence[str],
    label: str,
) -> float:
    return float(sum(
        np.sum((_z_response(model, observed, intervention) - model.centroids[label][intervention]) ** 2)
        for intervention in selected
    ))


def _predict(
    model: StrategyModel,
    observed: ObservableEpisode,
    selected: Sequence[str],
) -> str:
    allowed = _allowed_classes(observed)
    if len(allowed) == 1:
        return allowed[0]
    if not selected:
        return sorted(allowed)[0]
    scored = sorted(
        ((_class_distance(model, observed, selected, label), label) for label in allowed),
        key=lambda item: (item[0], item[1]),
    )
    return scored[0][1]


def _centroid_separation(model: StrategyModel, intervention: str, a: str, b: str) -> float:
    return float(np.linalg.norm(model.centroids[a][intervention] - model.centroids[b][intervention]))


def _choose_first(model: StrategyModel, observed: ObservableEpisode, remaining: Sequence[str]) -> str:
    classes = _allowed_classes(observed)
    if len(classes) <= 1:
        raise RuntimeError("no intervention is needed after a decisive protected audit")
    scored: list[tuple[float, str]] = []
    for intervention in remaining:
        pairwise = [
            _centroid_separation(model, intervention, a, b)
            for i, a in enumerate(classes)
            for b in classes[i + 1 :]
        ]
        scored.append((min(pairwise), intervention))
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][1]


def _choose_next(
    model: StrategyModel,
    observed: ObservableEpisode,
    selected: Sequence[str],
    remaining: Sequence[str],
) -> str:
    classes = _allowed_classes(observed)
    ranked = sorted(
        ((_class_distance(model, observed, selected, label), label) for label in classes),
        key=lambda item: (item[0], item[1]),
    )
    if len(ranked) < 2:
        raise RuntimeError("no second intervention is needed for a single remaining class")
    a, b = ranked[0][1], ranked[1][1]
    scored = [(_centroid_separation(model, intervention, a, b), intervention) for intervention in remaining]
    return sorted(scored, key=lambda item: (-item[0], item[1]))[0][1]


def diagnose(model: StrategyModel, observed: ObservableEpisode, budget: int = 2) -> Diagnosis:
    if budget not in {1, 2, 3}:
        raise ValueError(budget)
    allowed = _allowed_classes(observed)
    if len(allowed) == 1:
        prediction = allowed[0]
        return Diagnosis(prediction, (), (prediction,), prediction)

    remaining = list(ACTIVE_INTERVENTIONS)
    selected: list[str] = []
    predictions: list[str] = []
    while len(selected) < budget:
        intervention = (
            _choose_first(model, observed, remaining)
            if not selected
            else _choose_next(model, observed, selected, remaining)
        )
        selected.append(intervention)
        remaining.remove(intervention)
        predictions.append(_predict(model, observed, selected))

    full_selected = list(selected)
    full_remaining = list(remaining)
    full_predictions = list(predictions)
    while full_remaining:
        intervention = _choose_next(model, observed, full_selected, full_remaining)
        full_selected.append(intervention)
        full_remaining.remove(intervention)
        full_predictions.append(_predict(model, observed, full_selected))
    return Diagnosis(
        predicted_class=predictions[-1],
        intervention_order=tuple(full_selected),
        predictions_by_prefix=tuple(full_predictions),
        full_battery_prediction=full_predictions[-1],
    )


def _repair_fraction(true_class: str, predicted_class: str, protocol: Mapping[str, object]) -> float:
    repair = protocol["repair_evaluation"]
    if true_class == "no_fault":
        return 0.0
    if predicted_class == true_class:
        return float(repair["correct_module_repair_fraction"])
    single = {"event_module", "observability_module"}
    if true_class in single and predicted_class == "shared_representation":
        return float(repair["shared_repair_on_single_module_fraction"])
    if true_class == "shared_representation" and predicted_class in single:
        return float(repair["single_module_repair_on_shared_fraction"])
    if predicted_class == "no_fault":
        return 0.0
    return -float(repair["wrong_unrelated_repair_penalty_fraction"])


def _repair_outcome(ep: CausalEpisode, predicted_class: str) -> tuple[float, float]:
    protocol = load_protocol()
    fraction = _repair_fraction(ep.failure_class, predicted_class, protocol)
    domain = str(protocol["simulation"]["repair_seed_domain"])
    rng = np.random.default_rng(
        _seed(domain, ep.split, ep.mechanism, f"{ep.intensity:.2f}", ep.replicate, predicted_class)
    )
    pre = max(0.01, ep.intensity + 0.02 * float(rng.normal()))
    post = max(0.01, ep.intensity * (1.0 - fraction) + 0.02 * float(rng.normal()))
    return float(pre), float(post)


def _claim(summaries: Mapping[str, Mapping[str, float]]) -> tuple[str, str]:
    dual = summaries["interventional_dual_observer"]
    comparator_best = max(
        summaries[name]["heldout_localisation_accuracy_budget2"]
        for name in STRATEGIES
        if name != "interventional_dual_observer"
    )
    if (
        dual["heldout_localisation_accuracy_budget2"] < comparator_best - 0.05
        or dual["shared_representation_recall_budget2"] < 0.50
    ):
        return "D", "no_general_interventional_identification_advantage"
    if (
        dual["heldout_localisation_accuracy_budget2"] >= comparator_best + 0.10
        and dual["shared_representation_recall_budget2"] >= 0.80
        and dual["wrong_module_intervention_rate_budget2"] <= 0.20
        and dual["heldout_repair_positive_transfer_rate"] >= 0.75
        and dual["heldout_full_battery_localisation_accuracy"] >= 0.85
    ):
        return "A", "material_causal_identification_advantage"
    if (
        dual["heldout_localisation_accuracy_budget2"] >= comparator_best
        and dual["shared_representation_recall_budget2"] >= 0.65
        and dual["heldout_repair_positive_transfer_rate"] >= 0.60
    ):
        return "B", "conditional_causal_identification_advantage"
    return "C", "mixed_or_mechanism_specific_interventional_value"


def run_v12(
    development_replicates: int = 300,
    heldout_replicates: int = 300,
) -> dict[str, object]:
    protocol = load_protocol()
    intensities = tuple(map(float, protocol["simulation"]["intensity_tiers"]))
    development = [
        generate_episode("development", label, intensity, replicate)
        for label in CLASSES
        for intensity in intensities
        for replicate in range(development_replicates)
    ]
    heldout = [
        generate_episode("heldout", label, intensity, replicate)
        for label in CLASSES
        for intensity in intensities
        for replicate in range(heldout_replicates)
    ]

    summaries: dict[str, dict[str, float]] = {}
    class_accuracy: dict[str, dict[str, float]] = {}
    choice_distribution: dict[str, dict[str, dict[str, int]]] = {}
    audit_stratified: dict[str, dict[str, float]] = {}

    for strategy in STRATEGIES:
        model = fit_model(development, strategy)
        diagnoses = [diagnose(model, ep.observed, budget=2) for ep in heldout]
        predictions = [d.predicted_class for d in diagnoses]
        full_predictions = [d.full_battery_prediction for d in diagnoses]
        correct = [pred == ep.failure_class for pred, ep in zip(predictions, heldout, strict=True)]
        full_correct = [pred == ep.failure_class for pred, ep in zip(full_predictions, heldout, strict=True)]
        fault_indices = [i for i, ep in enumerate(heldout) if ep.failure_class != "no_fault"]
        shared_indices = [i for i, ep in enumerate(heldout) if ep.failure_class == "shared_representation"]
        no_fault_indices = [i for i, ep in enumerate(heldout) if ep.failure_class == "no_fault"]

        stable_lengths: list[int] = []
        repair_positive: list[bool] = []
        repair_relative: list[float] = []
        one_correct: list[bool] = []
        first_counts = {name: 0 for name in (*ACTIVE_INTERVENTIONS, "audit_stop")}
        second_counts = {name: 0 for name in (*ACTIVE_INTERVENTIONS, "audit_stop")}

        for ep, diagnosis in zip(heldout, diagnoses, strict=True):
            if not diagnosis.intervention_order:
                first_counts["audit_stop"] += 1
                second_counts["audit_stop"] += 1
                one_correct.append(diagnosis.predicted_class == ep.failure_class)
                stable_lengths.append(0 if diagnosis.predicted_class == ep.failure_class else 4)
            else:
                first_counts[diagnosis.intervention_order[0]] += 1
                one_pred = diagnosis.predictions_by_prefix[0]
                one_correct.append(one_pred == ep.failure_class)
                if len(diagnosis.intervention_order) >= 2:
                    second_counts[diagnosis.intervention_order[1]] += 1
                preds = diagnosis.predictions_by_prefix
                stable = 4
                for k in range(1, len(preds) + 1):
                    if all(pred == ep.failure_class for pred in preds[k - 1 :]):
                        stable = k
                        break
                stable_lengths.append(stable)

            if ep.failure_class != "no_fault":
                pre, post = _repair_outcome(ep, diagnosis.predicted_class)
                repair_positive.append(post < pre)
                repair_relative.append((pre - post) / pre)

        summaries[strategy] = {
            "heldout_localisation_accuracy_budget2": sum(correct) / len(correct),
            "heldout_full_battery_localisation_accuracy": sum(full_correct) / len(full_correct),
            "shared_representation_recall_budget2": sum(
                predictions[i] == "shared_representation" for i in shared_indices
            ) / len(shared_indices),
            "no_fault_false_intervention_rate_budget2": sum(
                predictions[i] != "no_fault" for i in no_fault_indices
            ) / len(no_fault_indices),
            "wrong_module_intervention_rate_budget2": sum(not correct[i] for i in fault_indices) / len(fault_indices),
            "mean_active_interventions_to_stable_correct_diagnosis": float(mean(stable_lengths)),
            "heldout_repair_positive_transfer_rate": sum(repair_positive) / len(repair_positive),
            "heldout_repair_relative_loss_reduction": float(mean(repair_relative)),
            "accuracy_after_one_intervention": sum(one_correct) / len(one_correct),
        }
        class_accuracy[strategy] = {
            label: sum(
                predictions[i] == label
                for i, ep in enumerate(heldout)
                if ep.failure_class == label
            ) / sum(ep.failure_class == label for ep in heldout)
            for label in CLASSES
        }
        choice_distribution[strategy] = {"first": first_counts, "second": second_counts}
        for audited in (False, True):
            indices = [i for i, ep in enumerate(heldout) if ep.observed.audit_available is audited]
            audit_stratified[f"{strategy}:{'audited' if audited else 'unaudited'}"] = {
                "n": float(len(indices)),
                "accuracy": sum(correct[i] for i in indices) / len(indices),
            }

    level, label = _claim(summaries)
    return {
        "schema": SCHEMA,
        "protocol_sha256": protocol_sha256(),
        "development_episode_count": len(development),
        "heldout_episode_count": len(heldout),
        "strategies": summaries,
        "class_accuracy": class_accuracy,
        "intervention_choice_distribution": choice_distribution,
        "protected_audit_stratified": audit_stratified,
        "claim": {"level": level, "label": label},
        "historical_results_retained": {
            "v7": {"gate": "FAIL", "claim_level": "C"},
            "v11": {
                "claim_level": "D",
                "result_sha256": "654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1"
            }
        },
        "v6_weights_changed": False,
        "v10_changed": False,
    }


def write_v12(path: str | Path, **kwargs: int) -> Path:
    payload = run_v12(**kwargs)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return output
