from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict[str, object]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def test_v10_protocol_is_pre_result_and_observer_blocked() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    assert protocol["schema"] == "interaction-sensing-v10-real-video-protocol-v1"
    assert "pre-result-frozen" in str(protocol["status"])
    assert protocol["observers"]["pollipi_required_exact_v5_commit"] == "d58d0a86034a6c2d53f90efbe4245370fd7cd2e9"
    assert protocol["observers"]["insepi_required_exact_v5_commit"] == "980813bab996909020140fad5bd83b055eb3db9c"
    assert protocol["observers"]["execution_before_both_exact_commits_reachable"] == "forbidden"
    assert protocol["non_interference"]["observer_outputs_seen_before_protocol_freeze"] is False


def test_v10_source_and_container_contracts_align() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    source = load("benchmarks/v10_real_video_source_lock.json")
    container = load("benchmarks/v10_container_metadata_summary.json")
    annotations = load("benchmarks/v10_annotation_provenance_audit.json")
    decoder = load("benchmarks/v10_decoder_freeze.json")

    assert source["selected_video_count"] == protocol["source"]["video_count"] == 7
    assert [row["sha256"] for row in source["videos"]] == protocol["source"]["video_sha256"]
    assert container["common"]["fps"] == protocol["source"]["native_fps"] == 60
    assert container["common"]["width"] == protocol["source"]["native_width"] == 1920
    assert container["common"]["height"] == protocol["source"]["native_height"] == 1080
    assert container["total_frames"] == protocol["source"]["native_total_frames"] == 22260
    assert container["total_duration_seconds"] == protocol["source"]["native_total_duration_seconds"] == 371
    assert annotations["decision"]["use_experiment_1_hydat_csv_as_ground_truth"] is False
    assert annotations["decision"]["use_experiment_1_yolo_csv_as_ground_truth"] is False
    assert decoder["executable_sha256"] == protocol["decoder"]["ffmpeg_sha256"]


def test_v10_window_and_condition_cardinality_is_fixed() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    windows = protocol["base_windows"]
    conditions = protocol["conditions"]
    assert windows["per_video_window_count"] == [58, 48, 59, 46, 57, 70, 26]
    assert sum(windows["per_video_window_count"]) == windows["total_base_windows"] == 364
    assert conditions["families"] == [
        "shadow",
        "occlusion",
        "blur",
        "sensor_banding",
        "glare",
        "framing_drift",
    ]
    assert conditions["intensity_tiers"] == [0.45, 0.80, 1.15]
    assert conditions["variants_per_base_window"] == 19
    assert windows["total_base_windows"] * conditions["variants_per_base_window"] == conditions["total_condition_count"] == 6916


def test_v10_canonicalisation_preserves_v7_lattice_contract() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    canonical = protocol["canonicalisation"]
    assert canonical["output_shape"] == [96, 128]
    assert canonical["output_dtype"] == "uint8"
    assert "15x15" in canonical["downsample"]
    assert "12 rows" in canonical["pad"]
    assert protocol["decoder"]["filter"] == "select='not(mod(n,60))'"
    assert protocol["decoder"]["output_pixel_format"] == "rgb24"


def test_v10_allocation_panels_are_predefined_and_balanced() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    allocation = protocol["allocation_transfer"]
    assert allocation["panel_count"] == 18
    assert allocation["windows_per_panel"] == 364
    assert allocation["disturbance_prevalence"] == 0.5
    assert allocation["disturbed_windows_per_panel"] == 182
    assert allocation["budgets"] == [0.10, 0.25, 0.50]
    assert allocation["selection_replicates"] == 200
    assert [row["name"] for row in allocation["policies"]] == [
        "uniform",
        "guarded_v6",
        "guarded_e_only",
        "guarded_o_only",
        "guarded_fused_20_80",
        "guarded_max",
    ]


def test_v10_never_uses_algorithm_tracks_as_truth_or_claims_field_accuracy() -> None:
    protocol = load("benchmarks/v10_real_video_protocol.json")
    truth = protocol["truth_and_labels"]
    ceiling = protocol["claim_ceiling"]
    assert truth["hydat_csv_as_truth"] is False
    assert truth["yolo_csv_as_truth"] is False
    assert truth["experiment1_results_as_frame_truth"] is False
    forbidden = ceiling["never_allowed_from_v10"]
    assert "field biological-event detection accuracy" in forbidden
    assert "universal optimality of 50/10/40" in forbidden
    assert "use of V10 to rescue or reinterpret V7" in forbidden


def test_v10_protocol_hash_is_stable_for_current_file_bytes() -> None:
    payload = (ROOT / "benchmarks/v10_real_video_protocol.json").read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    assert len(digest) == 64
    assert digest != "0" * 64
