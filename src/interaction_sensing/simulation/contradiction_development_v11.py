"""V11 contradiction-guided development benchmark.

This generation evaluates a *development protocol*, not an allocation score.
It preserves two epistemically distinct channels (biological evidence and
observability risk), gives every compared strategy the same probe schedule and
protected-audit assignments, trains only on development mechanism subtypes, and
scores localisation/repair on held-out mechanism subtypes.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import mean
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEMA = "interaction-sensing-v11-contradiction-development-result-v1"
PROTOCOL_PATH = "benchmarks/v11_contradiction_development_protocol.json"
CLASSES = ("event_module", "no_fault", "observability_module", "shared_representation")
STRATEGIES = ("event_only", "observability_only", "early_scalar_fusion", "contradiction_guided")
INTENSITIES = (0.35, 0.65, 0.95)
PROBES = (
    ("clean_absence", 0, 0, True),
    ("clean_event", 1, 0, True),
    ("nuisance_only", 0, 1, True),
    ("event_plus_nuisance", 1, 1, True),
    ("blind_natural_a", None, None, False),
    ("blind_natural_b", None, None, False),
)
DEV_MECHANISM = {
    "event_module": "event_contrast_loss",
    "observability_module": "glare_risk_blind",
    "shared_representation": "occlusion_shared_blind",
    "no_fault": "clean_control_dev",
}
TEST_MECHANISM = {
    "event_module": "event_scale_shift",
    "observability_module": "shadow_risk_blind",
    "shared_representation": "blur_shared_blind",
    "no_fault": "clean_control_test",
}
SEED_DOMAIN = "interaction-sensing-v11-development-world-v1"
AUDIT_DOMAIN = "interaction-sensing-v11-protected-audit-v1"
NOISE_SD = 0.08
RHO = 0.35


@dataclass(frozen=True, slots=True)
class ProbeObservation:
    probe: str
    event: int
    disturbance: int
    truth_known: bool
    protected_audit: bool
    evidence: float
    observability: float


@dataclass(frozen=True, slots=True)
class Episode:
    split: str
    failure_class: str
    mechanism: str
    intensity: float
    replicate: int
    probes: tuple[ProbeObservation, ...]


def _seed(*parts: object) -> int:
    text = "|".join((SEED_DOMAIN, *(str(part) for part in parts)))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _audit(split: str, mechanism: str, intensity: float, replicate: int, probe: str) -> bool:
    text = f"{AUDIT_DOMAIN}|{split}|{mechanism}|{intensity:.2f}|{replicate}|{probe}"
    return hashlib.sha256(text.encode()).digest()[0] < 128


def _clip(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def _base_scores(event: int, disturbance: int) -> tuple[float, float]:
    # Different targets by construction: E represents event evidence; O represents
    # observation-process risk. Disturbance modestly suppresses event visibility.
    evidence = 0.12 + 0.78 * event - 0.10 * event * disturbance + 0.05 * disturbance * (1 - event)
    observability = 0.10 + 0.80 * disturbance
    return evidence, observability


def _apply_fault(
    evidence: float,
    observability: float,
    *,
    mechanism: str,
    event: int,
    disturbance: int,
    intensity: float,
    repair_action: str | None,
) -> tuple[float, float]:
    true_class = (
        "event_module" if mechanism in {"event_contrast_loss", "event_scale_shift"}
        else "observability_module" if mechanism in {"glare_risk_blind", "shadow_risk_blind"}
        else "shared_representation" if mechanism in {"occlusion_shared_blind", "blur_shared_blind"}
        else "no_fault"
    )

    # A correct repair removes 85% of the latent fault. A shared repair can partly
    # repair a single-channel fault; a single-channel repair can partly repair only
    # its side of a shared fault. Wrong unrelated interventions are not made helpful.
    e_intensity = intensity
    o_intensity = intensity
    if repair_action == true_class and true_class != "no_fault":
        e_intensity *= 0.15
        o_intensity *= 0.15
    elif repair_action == "shared_representation" and true_class in {"event_module", "observability_module"}:
        e_intensity *= 0.65
        o_intensity *= 0.65
    elif true_class == "shared_representation" and repair_action == "event_module":
        e_intensity *= 0.45
    elif true_class == "shared_representation" and repair_action == "observability_module":
        o_intensity *= 0.45

    if mechanism == "event_contrast_loss":
        evidence -= 0.54 * e_intensity * event
    elif mechanism == "event_scale_shift":
        evidence = 0.5 + (evidence - 0.5) * (1.0 - 0.58 * e_intensity)
    elif mechanism == "glare_risk_blind":
        observability -= 0.58 * o_intensity * disturbance
    elif mechanism == "shadow_risk_blind":
        observability = 0.5 + (observability - 0.5) * (1.0 - 0.60 * o_intensity)
    elif mechanism == "occlusion_shared_blind":
        if disturbance:
            observability -= (0.22 + 0.28 * event) * o_intensity
        if event and disturbance:
            evidence -= 0.48 * e_intensity
    elif mechanism == "blur_shared_blind":
        if disturbance:
            observability -= (0.18 + 0.24 * event) * o_intensity
        if event and disturbance:
            evidence = 0.5 + (evidence - 0.5) * (1.0 - 0.50 * e_intensity)

    # Unrelated wrong intervention produces a small calibration cost. This term is
    # symmetric around the correct truth and can hurt rather than being clipped away.
    if repair_action not in (None, "no_fault", true_class):
        if repair_action == "event_module" and true_class not in {"event_module", "shared_representation"}:
            evidence += 0.04 if event == 0 else -0.04
        elif repair_action == "observability_module" and true_class not in {"observability_module", "shared_representation"}:
            observability += 0.04 if disturbance == 0 else -0.04
    return _clip(evidence), _clip(observability)


def generate_episode(
    split: str,
    failure_class: str,
    intensity: float,
    replicate: int,
    *,
    repair_action: str | None = None,
) -> Episode:
    if split not in {"development", "heldout"}:
        raise ValueError(split)
    if failure_class not in CLASSES:
        raise ValueError(failure_class)
    mechanism = (DEV_MECHANISM if split == "development" else TEST_MECHANISM)[failure_class]
    rng = np.random.default_rng(_seed(split, mechanism, f"{intensity:.2f}", replicate))
    rows: list[ProbeObservation] = []
    for probe, fixed_event, fixed_disturbance, known_by_design in PROBES:
        event = int(rng.integers(0, 2)) if fixed_event is None else int(fixed_event)
        disturbance = int(rng.integers(0, 2)) if fixed_disturbance is None else int(fixed_disturbance)
        evidence, observability = _base_scores(event, disturbance)
        evidence, observability = _apply_fault(
            evidence,
            observability,
            mechanism=mechanism,
            event=event,
            disturbance=disturbance,
            intensity=float(intensity),
            repair_action=repair_action,
        )
        common = float(rng.normal())
        independent_e = float(rng.normal())
        independent_o = float(rng.normal())
        evidence = _clip(evidence + NOISE_SD * (sqrt(RHO) * common + sqrt(1 - RHO) * independent_e))
        observability = _clip(observability + NOISE_SD * (sqrt(RHO) * common + sqrt(1 - RHO) * independent_o))
        audit = (not known_by_design) and _audit(split, mechanism, intensity, replicate, probe)
        rows.append(ProbeObservation(
            probe=probe,
            event=event,
            disturbance=disturbance,
            truth_known=bool(known_by_design or audit),
            protected_audit=bool(audit),
            evidence=evidence,
            observability=observability,
        ))
    return Episode(split, failure_class, mechanism, float(intensity), int(replicate), tuple(rows))


def diagnostic_state(evidence: float, observability: float) -> tuple[float, float, float, float]:
    e = evidence >= 0.5
    o = observability >= 0.5
    # Fixed one-hot order: E-high/O-low, E-low/O-high, both-high, both-low.
    return (
        float(e and not o),
        float((not e) and o),
        float(e and o),
        float((not e) and (not o)),
    )


def _known_truth(row: ProbeObservation) -> tuple[float, float, float]:
    if row.truth_known:
        return 1.0, float(row.event), float(row.disturbance)
    return 0.0, 0.0, 0.0


def features(episode: Episode, strategy: str, prefix: int = 6) -> np.ndarray:
    if strategy not in STRATEGIES:
        raise ValueError(strategy)
    if not 1 <= prefix <= len(PROBES):
        raise ValueError(prefix)
    values: list[float] = []
    for row in episode.probes[:prefix]:
        known, event_truth, disturbance_truth = _known_truth(row)
        if strategy == "event_only":
            values.extend((row.evidence, known, abs(row.evidence - event_truth) if known else 0.0))
        elif strategy == "observability_only":
            values.extend((row.observability, known, abs(row.observability - disturbance_truth) if known else 0.0))
        elif strategy == "early_scalar_fusion":
            fused = 0.5 * row.evidence + 0.5 * row.observability
            target = max(event_truth, disturbance_truth)
            values.extend((fused, known, abs(fused - target) if known else 0.0))
        else:
            values.extend((row.evidence, row.observability, *diagnostic_state(row.evidence, row.observability)))
            values.extend((known, abs(row.evidence - event_truth) if known else 0.0, abs(row.observability - disturbance_truth) if known else 0.0))
            shared_miss = float(
                known
                and row.event == 1
                and row.disturbance == 1
                and row.evidence < 0.5
                and row.observability < 0.5
            )
            values.append(shared_miss)
    return np.asarray(values, dtype=float)


@dataclass(frozen=True, slots=True)
class CentroidModel:
    strategy: str
    prefix: int
    mean: np.ndarray
    scale: np.ndarray
    centroids: Mapping[str, np.ndarray]

    def predict(self, episode: Episode) -> str:
        x = (features(episode, self.strategy, self.prefix) - self.mean) / self.scale
        scored = sorted(
            ((float(np.sum((x - centroid) ** 2)), label) for label, centroid in self.centroids.items()),
            key=lambda item: (item[0], item[1]),
        )
        return scored[0][1]


def fit_centroid_model(episodes: Sequence[Episode], strategy: str, prefix: int) -> CentroidModel:
    x = np.vstack([features(ep, strategy, prefix) for ep in episodes])
    mu = x.mean(axis=0)
    scale = x.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    z = (x - mu) / scale
    centroids: dict[str, np.ndarray] = {}
    for label in CLASSES:
        indices = [i for i, ep in enumerate(episodes) if ep.failure_class == label]
        centroids[label] = z[indices].mean(axis=0)
    return CentroidModel(strategy, prefix, mu, scale, centroids)


def _loss(episode: Episode) -> float:
    terms: list[float] = []
    for row in episode.probes:
        terms.append((row.evidence - row.event) ** 2)
        terms.append((row.observability - row.disturbance) ** 2)
    return float(mean(terms))


def _claim(strategy_summary: Mapping[str, Mapping[str, float]]) -> tuple[str, str]:
    cg = strategy_summary["contradiction_guided"]
    comparator_best = max(strategy_summary[name]["heldout_failure_localisation_accuracy"] for name in STRATEGIES[:-1])
    if (
        cg["heldout_failure_localisation_accuracy"] < comparator_best - 0.05
        or cg["shared_blindspot_discovery_rate"] < 0.50
    ):
        return "D", "no_general_localisation_advantage"
    if (
        cg["heldout_failure_localisation_accuracy"] >= comparator_best + 0.10
        and cg["shared_blindspot_discovery_rate"] >= 0.80
        and cg["wrong_module_intervention_rate"] <= 0.20
        and cg["heldout_repair_positive_transfer_rate"] >= 0.75
        and cg["no_fault_false_intervention_rate"] <= 0.20
    ):
        return "A", "material_failure_localisation_and_repair_advantage"
    if (
        cg["heldout_failure_localisation_accuracy"] >= comparator_best
        and cg["shared_blindspot_discovery_rate"] >= 0.65
        and cg["heldout_repair_positive_transfer_rate"] >= 0.60
    ):
        return "B", "conditional_contradiction_guided_advantage"
    return "C", "mixed_or_mechanism_specific_value"


def run_v11(
    *,
    development_replicates: int = 300,
    heldout_replicates: int = 300,
) -> dict[str, object]:
    development = [
        generate_episode("development", label, intensity, rep)
        for label in CLASSES
        for intensity in INTENSITIES
        for rep in range(development_replicates)
    ]
    heldout = [
        generate_episode("heldout", label, intensity, rep)
        for label in CLASSES
        for intensity in INTENSITIES
        for rep in range(heldout_replicates)
    ]

    summaries: dict[str, dict[str, float]] = {}
    class_accuracy: dict[str, dict[str, float]] = {}
    for strategy in STRATEGIES:
        models = {k: fit_centroid_model(development, strategy, k) for k in range(1, 7)}
        final = models[6]
        final_predictions = [final.predict(ep) for ep in heldout]
        correct = [prediction == ep.failure_class for prediction, ep in zip(final_predictions, heldout, strict=True)]
        non_null = [i for i, ep in enumerate(heldout) if ep.failure_class != "no_fault"]
        shared = [i for i, ep in enumerate(heldout) if ep.failure_class == "shared_representation"]
        no_fault = [i for i, ep in enumerate(heldout) if ep.failure_class == "no_fault"]

        stable_lengths: list[int] = []
        positive_repairs: list[bool] = []
        relative_repairs: list[float] = []
        for index, ep in enumerate(heldout):
            preds = [models[k].predict(ep) for k in range(1, 7)]
            stable = 7
            for k in range(1, 7):
                if all(pred == ep.failure_class for pred in preds[k - 1 :]):
                    stable = k
                    break
            stable_lengths.append(stable)
            if ep.failure_class != "no_fault":
                action = final_predictions[index]
                baseline = _loss(ep)
                repaired = generate_episode(
                    "heldout", ep.failure_class, ep.intensity, ep.replicate, repair_action=action
                )
                post = _loss(repaired)
                positive_repairs.append(post < baseline)
                relative_repairs.append((baseline - post) / max(baseline, 1e-12))

        summaries[strategy] = {
            "heldout_failure_localisation_accuracy": sum(correct) / len(correct),
            "wrong_module_intervention_rate": sum(not correct[i] for i in non_null) / len(non_null),
            "shared_blindspot_discovery_rate": sum(final_predictions[i] == "shared_representation" for i in shared) / len(shared),
            "no_fault_false_intervention_rate": sum(final_predictions[i] != "no_fault" for i in no_fault) / len(no_fault),
            "experiments_to_stable_falsification": float(mean(stable_lengths)),
            "heldout_repair_positive_transfer_rate": sum(positive_repairs) / len(positive_repairs),
            "heldout_repair_relative_loss_reduction": float(mean(relative_repairs)),
        }
        class_accuracy[strategy] = {
            label: sum(
                final_predictions[i] == label
                for i, ep in enumerate(heldout)
                if ep.failure_class == label
            ) / sum(ep.failure_class == label for ep in heldout)
            for label in CLASSES
        }

    level, label = _claim(summaries)
    protocol_bytes = Path(PROTOCOL_PATH).read_bytes()
    return {
        "schema": SCHEMA,
        "protocol_sha256": hashlib.sha256(protocol_bytes).hexdigest(),
        "development_episode_count": len(development),
        "heldout_episode_count": len(heldout),
        "strategies": summaries,
        "class_accuracy": class_accuracy,
        "claim": {"level": level, "label": label},
        "v7_locked_result_retained": {"gate": "FAIL", "claim_level": "C"},
        "v6_weights_changed": False,
        "v10_changed": False,
    }


def write_v11(path: str | Path, **kwargs: int) -> Path:
    result = run_v11(**kwargs)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return output
