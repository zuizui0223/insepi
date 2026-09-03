from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


EXPECTED_CLIP_COUNT = 720


@dataclass(frozen=True)
class Stage:
    number: int
    name: str
    required_paths: tuple[str, ...]
    next_action: str


STAGES = (
    Stage(
        1,
        "private_randomisation",
        (
            "PRIVATE_V13_PLAN/v13_private_truth_ledger.csv",
            "PRIVATE_V13_PLAN/v13_observer_plan.csv",
            "PRIVATE_V13_PLAN/v13_protected_qc_plan.csv",
            "PRIVATE_V13_PLAN/v13_randomisation_commitment.json",
        ),
        "Generate the private V13 randomisation and preserve its commitment before acquisition.",
    ),
    Stage(
        2,
        "capture_templates",
        (
            "V13_CAPTURE_LOGS/v13_block_capture_log.csv",
            "V13_CAPTURE_LOGS/v13_phase_capture_log.csv",
            "V13_QC_ANNOTATION_TEMPLATE.csv",
        ),
        "Create the capture-log and protected-QC templates from the committed observer-safe plan.",
    ),
    Stage(
        4,
        "capture_validation",
        ("V13_CAPTURE_LOGS/v13_capture_validation.json",),
        "Complete acquisition, then pass the capture-log gate before any observer execution.",
    ),
    Stage(
        5,
        "field_byte_validation",
        ("V13_FIELD_BYTE_RECEIPT.json",),
        "Validate the byte-complete 720-clip field bundle in the private operator environment.",
    ),
    Stage(
        6,
        "truth_free_pixels",
        (
            "V13_PIXELS/v13_frames.npy",
            "V13_PIXELS/v13_backgrounds.npy",
            "V13_PIXELS/v13_safe_registry.json",
            "V13_PIXELS/v13_pixel_receipt.json",
        ),
        "Materialise the canonical truth-free pixel artifact with the frozen decoder contract.",
    ),
    Stage(
        8,
        "observer_traces",
        (
            "V13_TRACES/pollipi_v13_trace.jsonl",
            "V13_TRACES/insepi_v13_trace.jsonl",
        ),
        "Run the exact frozen observer smoke gates, then emit both truth-free observer traces.",
    ),
    Stage(
        9,
        "block_responses",
        (
            "V13_RESPONSES/v13_safe_block_responses.csv",
            "V13_RESPONSES/v13_response_receipt.json",
        ),
        "Summarise the two observer traces into truth-free block responses.",
    ),
    Stage(
        10,
        "private_truth_split",
        (
            "PRIVATE_V13_TRUTH_SPLIT/v13_development_labels.csv",
            "PRIVATE_V13_TRUTH_SPLIT/v13_heldout_truth_SEALED.csv",
            "PRIVATE_V13_TRUTH_SPLIT/v13_truth_split_receipt.json",
        ),
        "Split truth privately; transfer development labels only and keep held-out truth sealed.",
    ),
    Stage(
        11,
        "blinded_prediction",
        ("V13_PREDICTIONS/v13_predictions.json",),
        "Fit on development labels only and emit blinded held-out predictions.",
    ),
    Stage(
        12,
        "prediction_commitment",
        ("V13_PREDICTIONS/v13_prediction_commitment.json",),
        "Commit prediction bytes and ledger hashes before any held-out truth is unsealed.",
    ),
    Stage(
        13,
        "protected_qc",
        ("V13_QC_ANNOTATIONS.csv",),
        "Complete blinded protected QC without observer outputs or predicted classes.",
    ),
    Stage(
        14,
        "locked_evaluation",
        ("V13_RESULT/v13_report.json",),
        "Unseal held-out truth only now and run the frozen evaluator.",
    ),
)


def _path_state(root: Path, stage: Stage) -> tuple[int, int]:
    present = sum((root / rel).exists() for rel in stage.required_paths)
    return present, len(stage.required_paths)


def _clip_count(root: Path) -> int:
    clip_dir = root / "V13_CLIPS"
    if not clip_dir.exists():
        return 0
    return sum(1 for path in clip_dir.rglob("*.mp4") if path.is_file())


def inspect_workspace(root: Path) -> dict[str, object]:
    root = root.resolve()
    violations: list[str] = []
    stage_rows: list[dict[str, object]] = []

    clips = _clip_count(root)
    if clips > EXPECTED_CLIP_COUNT:
        violations.append(
            f"V13_CLIPS contains {clips} MP4 files; the frozen protocol requires exactly {EXPECTED_CLIP_COUNT}."
        )

    stage_complete: list[bool] = []
    for stage in STAGES:
        present, total = _path_state(root, stage)
        complete = present == total
        partial = 0 < present < total
        if partial:
            violations.append(
                f"stage {stage.number} ({stage.name}) has a partial artifact set: {present}/{total} required paths present."
            )
        stage_complete.append(complete)
        stage_rows.append(
            {
                "stage": stage.number,
                "name": stage.name,
                "present": present,
                "required": total,
                "complete": complete,
            }
        )

    # Physical acquisition sits between template creation (stage 2) and capture validation (stage 4).
    acquisition_complete = clips == EXPECTED_CLIP_COUNT
    acquisition_started = clips > 0

    ordered_flags: list[tuple[str, bool]] = []
    ordered_flags.extend((f"stage_{stage.number}_{stage.name}", complete) for stage, complete in zip(STAGES[:2], stage_complete[:2]))
    ordered_flags.append(("stage_3_physical_acquisition", acquisition_complete))
    ordered_flags.extend((f"stage_{stage.number}_{stage.name}", complete) for stage, complete in zip(STAGES[2:], stage_complete[2:]))

    first_incomplete_index = next((i for i, (_, complete) in enumerate(ordered_flags) if not complete), len(ordered_flags))
    for later_name, later_complete in ordered_flags[first_incomplete_index + 1 :]:
        if later_complete:
            violations.append(
                f"{later_name} is complete while an earlier required V13 stage is incomplete; do not skip the frozen execution order."
            )

    if not stage_complete[1] and acquisition_started:
        violations.append("physical clips exist before the complete stage-2 capture/QC template set.")
    if not acquisition_complete and stage_complete[2]:
        violations.append("capture validation exists before exactly 720 physical clips are present.")

    if first_incomplete_index == len(ordered_flags):
        next_stage = "complete"
        next_action = "V13 locked evaluation artifact is present. Preserve the result and do not retune this generation."
    else:
        missing_name = ordered_flags[first_incomplete_index][0]
        if missing_name == "stage_3_physical_acquisition":
            next_stage = "stage_3_physical_acquisition"
            if clips == 0:
                next_action = "Acquire the frozen 180 blocks / 720 phase clips while completing capture logs."
            else:
                next_action = f"Continue frozen physical acquisition: {clips}/{EXPECTED_CLIP_COUNT} MP4 clips are present."
        else:
            stage = next(stage for stage in STAGES if missing_name.startswith(f"stage_{stage.number}_"))
            next_stage = missing_name
            next_action = stage.next_action

    return {
        "schema": "interaction-sensing-v13-pipeline-status-v1",
        "workspace": str(root),
        "valid": not violations,
        "clip_count": clips,
        "expected_clip_count": EXPECTED_CLIP_COUNT,
        "acquisition_started": acquisition_started,
        "acquisition_complete": acquisition_complete,
        "stages": stage_rows,
        "next_stage": next_stage,
        "next_action": next_action,
        "violations": violations,
        "privacy_boundary": "artifact presence only; private truth contents are never read",
    }


def _print_human(status: dict[str, object]) -> None:
    state = "PASS" if status["valid"] else "BLOCKED"
    print(f"V13_PIPELINE_STATUS {state}")
    print(f"clips {status['clip_count']}/{status['expected_clip_count']}")
    print(f"next_stage {status['next_stage']}")
    print(f"next_action {status['next_action']}")
    violations = status["violations"]
    if violations:
        for item in violations:
            print(f"violation {item}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report the next fail-closed V13 execution step without reading private truth contents."
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    status = inspect_workspace(args.workspace)
    if args.as_json:
        print(json.dumps(status, sort_keys=True, indent=2))
    else:
        _print_human(status)
    if not status["valid"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
