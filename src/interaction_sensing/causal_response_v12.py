"""Factorial causal-response contrasts for V12 physical validation.

The estimator keeps biological-evidence and observability-risk outcomes separate.
It consumes intervention truth only after observer outputs have already been
emitted and joined by trial_id. It does not construct a winner score or infer a
failure label from raw observer agreement/disagreement.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Mapping, Sequence

from interaction_sensing.physical_validation_v12 import Trial


@dataclass(frozen=True, slots=True)
class ObserverOutput:
    trial_id: str
    evidence: float
    observability: float

    def __post_init__(self) -> None:
        for name, value in (("evidence", self.evidence), ("observability", self.observability)):
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must lie in [0,1]")


@dataclass(frozen=True, slots=True)
class FactorialResponse:
    split: str
    block_id: str
    disturbance_family: str
    intensity_label: str
    replicates_per_cell: int
    evidence_cell_means: Mapping[str, float]
    observability_cell_means: Mapping[str, float]
    event_effect_on_evidence: float
    disturbance_effect_on_evidence: float
    interaction_on_evidence: float
    event_effect_on_observability: float
    disturbance_effect_on_observability: float
    interaction_on_observability: float

    @property
    def response_matrix(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return (
            (self.event_effect_on_evidence, self.disturbance_effect_on_evidence),
            (self.event_effect_on_observability, self.disturbance_effect_on_observability),
        )

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["response_matrix"] = [list(row) for row in self.response_matrix]
        return payload


def _cell_key(event: int, disturbance: int) -> str:
    return f"E{int(event)}D{int(disturbance)}"


def _effects(cells: Mapping[str, float]) -> tuple[float, float, float]:
    y00 = float(cells["E0D0"])
    y10 = float(cells["E1D0"])
    y01 = float(cells["E0D1"])
    y11 = float(cells["E1D1"])
    event = 0.5 * ((y10 - y00) + (y11 - y01))
    disturbance = 0.5 * ((y01 - y00) + (y11 - y10))
    interaction = y11 - y10 - y01 + y00
    return event, disturbance, interaction


def estimate_factorial_responses(
    trials: Sequence[Trial],
    outputs: Sequence[ObserverOutput],
) -> tuple[FactorialResponse, ...]:
    """Estimate block-level factorial contrasts after truth/output join.

    Each block × disturbance family × intensity must contain an exactly balanced
    2x2 treatment with the same number of replicates in every cell.  Frames are
    not accepted here; one observer output row corresponds to one physical trial.
    """
    if not trials:
        raise ValueError("trials cannot be empty")
    trial_by_id = {trial.trial_id: trial for trial in trials}
    if len(trial_by_id) != len(trials):
        raise ValueError("trial ids must be unique")
    output_by_id = {row.trial_id: row for row in outputs}
    if len(output_by_id) != len(outputs):
        raise ValueError("observer output trial ids must be unique")
    if set(trial_by_id) != set(output_by_id):
        raise ValueError("truth and observer outputs must have identical trial ids")

    grouped: dict[tuple[str, str, str, str], list[tuple[Trial, ObserverOutput]]] = {}
    for trial in trials:
        key = (trial.split, trial.block_id, trial.disturbance_family, trial.intensity_label)
        grouped.setdefault(key, []).append((trial, output_by_id[trial.trial_id]))

    rows: list[FactorialResponse] = []
    for (split, block_id, family, intensity), members in sorted(grouped.items()):
        evidence_cells: dict[str, list[float]] = {_cell_key(e, d): [] for e in (0, 1) for d in (0, 1)}
        observability_cells: dict[str, list[float]] = {_cell_key(e, d): [] for e in (0, 1) for d in (0, 1)}
        for trial, output in members:
            key = _cell_key(trial.event_intervention, trial.disturbance_intervention)
            evidence_cells[key].append(float(output.evidence))
            observability_cells[key].append(float(output.observability))
        counts = {len(values) for values in evidence_cells.values()}
        if len(counts) != 1 or 0 in counts:
            raise RuntimeError(
                f"unbalanced or incomplete V12 factorial cell in {block_id}/{family}/{intensity}: "
                f"{ {key: len(values) for key, values in evidence_cells.items()} }"
            )
        replicates = counts.pop()
        e_means = {key: mean(values) for key, values in evidence_cells.items()}
        o_means = {key: mean(values) for key, values in observability_cells.items()}
        event_e, disturbance_e, interaction_e = _effects(e_means)
        event_o, disturbance_o, interaction_o = _effects(o_means)
        rows.append(
            FactorialResponse(
                split=split,
                block_id=block_id,
                disturbance_family=family,
                intensity_label=intensity,
                replicates_per_cell=replicates,
                evidence_cell_means=e_means,
                observability_cell_means=o_means,
                event_effect_on_evidence=event_e,
                disturbance_effect_on_evidence=disturbance_e,
                interaction_on_evidence=interaction_e,
                event_effect_on_observability=event_o,
                disturbance_effect_on_observability=disturbance_o,
                interaction_on_observability=interaction_o,
            )
        )
    return tuple(rows)
