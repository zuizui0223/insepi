#!/usr/bin/env python3
"""Build deterministic pre-V7 manuscript figures from frozen evidence only.

The script intentionally depends only on the Python standard library. It never
imports the V7 generator, materializer, evaluator, or observer adapters and never
reads V7 lock outputs. This keeps figure preparation downstream of already
inspected V1-V6 evidence and prevents accidental V7 materialisation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
from typing import Iterable

WIDTH = 1200
HEIGHT = 760
FONT = "Arial, Helvetica, sans-serif"
INK = "#202124"
MUTED = "#5f6368"
GRID = "#dadce0"
BLUE = "#1a73e8"
ORANGE = "#f29900"
GREEN = "#188038"
RED = "#d93025"
PURPLE = "#7e57c2"
TEAL = "#00897b"
LIGHT_BLUE = "#e8f0fe"
LIGHT_RED = "#fce8e6"
LIGHT_GREEN = "#e6f4ea"
LIGHT_GRAY = "#f1f3f4"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_header(width: int = WIDTH, height: int = HEIGHT) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]


def text(x: float, y: float, value: object, *, size: int = 24, weight: int = 400, fill: str = INK,
         anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(value)}</text>'
    )


def line(x1: float, y1: float, x2: float, y2: float, *, stroke: str = GRID, width: float = 2,
         dash: str | None = None) -> str:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{width}"{extra}/>'


def rect(x: float, y: float, w: float, h: float, *, fill: str = "none", stroke: str = GRID,
         width: float = 2, rx: float = 12) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'
    )


def circle(cx: float, cy: float, r: float, *, fill: str, stroke: str = "#ffffff", width: float = 3) -> str:
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


def wrap_lines(value: str, max_chars: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join((*current, word))
        if current and len(trial) > max_chars:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def multiline(x: float, y: float, value: str, *, size: int = 22, weight: int = 400,
              fill: str = INK, max_chars: int = 45, line_height: float | None = None,
              anchor: str = "start") -> list[str]:
    if line_height is None:
        line_height = size * 1.25
    return [
        text(x, y + i * line_height, row, size=size, weight=weight, fill=fill, anchor=anchor)
        for i, row in enumerate(wrap_lines(value, max_chars))
    ]


def write_svg(path: Path, rows: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join((*rows, "</svg>", "")), encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fig1_generation_timeline(data: dict, output: Path) -> None:
    rows = svg_header()
    rows += [
        text(60, 60, "Figure 1. Contradiction-guided method generations", size=32, weight=700),
        text(60, 96, "Negative generations remain part of the method history rather than being hidden.", size=19, fill=MUTED),
    ]
    ledger = data["generation_ledger"]
    x0, x1, y = 95, 1105, 330
    rows.append(line(x0, y, x1, y, stroke=INK, width=3))
    spacing = (x1 - x0) / (len(ledger) - 1)
    status_color = {
        "development": BLUE,
        "negative": ORANGE,
        "locked fail": RED,
        "frozen candidate": GREEN,
        "unexecuted": MUTED,
    }
    for i, item in enumerate(ledger):
        x = x0 + i * spacing
        color = status_color[item["status"]]
        rows.append(circle(x, y, 23, fill=color))
        rows.append(text(x, y + 8, item["generation"], size=18, weight=700, fill="#ffffff", anchor="middle"))
        up = i % 2 == 0
        box_y = 145 if up else 405
        box_h = 135
        rows.append(line(x, y - (23 if up else -23), x, box_y + (box_h if up else 0), stroke=color, width=2))
        rows.append(rect(x - 90, box_y, 180, box_h, fill="#ffffff", stroke=color, width=2, rx=10))
        rows.append(text(x, box_y + 28, item["status"].upper(), size=15, weight=700, fill=color, anchor="middle"))
        rows.extend(multiline(x, box_y + 56, item["question"], size=15, max_chars=24, anchor="middle"))
    rows.extend([
        rect(80, 620, 1040, 82, fill=LIGHT_GRAY, stroke=GRID, width=1, rx=12),
        text(105, 654, "Key transition", size=18, weight=700),
        text(260, 654, "V5 falsified the allocation rule; V6 changed the policy class instead of retuning the failed scalar score.", size=18),
        text(105, 684, "V7 remains unexecuted in all pre-V7 figures.", size=16, fill=MUTED),
    ])
    write_svg(output, rows)


def fig2_v3_equal_budget(data: dict, output: Path, csv_output: Path) -> None:
    rows = svg_header()
    rows += [
        text(60, 58, "Figure 2. Direct disagreement did not dominate equal-budget allocation", size=31, weight=700),
        text(60, 93, "V3, 25% audit budget; paired Monte Carlo worlds.", size=19, fill=MUTED),
    ]
    policies = data["v3_equal_budget"]["policies"]
    left, top, chart_w, chart_h = 120, 160, 980, 400
    rows.append(line(left, top + chart_h, left + chart_w, top + chart_h, stroke=INK, width=2))
    for tick in range(0, 8):
        value = tick / 10
        y = top + chart_h - (value / 0.70) * chart_h
        rows.append(line(left, y, left + chart_w, y, stroke=GRID, width=1))
        rows.append(text(left - 18, y + 6, f"{value:.1f}", size=14, fill=MUTED, anchor="end"))
    group_w = chart_w / len(policies)
    bar_w = 32
    metric_colors = [("event_recall", BLUE), ("hidden_error_recall", GREEN), ("tv", ORANGE)]
    for i, policy in enumerate(policies):
        cx = left + group_w * (i + 0.5)
        for j, (metric, color) in enumerate(metric_colors):
            value = policy[metric]
            h = (value / 0.70) * chart_h
            x = cx + (j - 1) * (bar_w + 5) - bar_w / 2
            y = top + chart_h - h
            rows.append(rect(x, y, bar_w, h, fill=color, stroke=color, width=0, rx=3))
        label = policy["name"].replace("candidate_", "").replace("fixed_", "")
        for k, label_line in enumerate(label.replace("_", " ").split(" / ")):
            rows.append(text(cx, top + chart_h + 28 + 18 * k, label_line, size=13, anchor="middle"))
    legend_y = 630
    for j, (metric, color) in enumerate(metric_colors):
        x = 210 + j * 280
        rows.append(rect(x, legend_y - 14, 20, 20, fill=color, stroke=color, width=0, rx=2))
        legend_name = {
            "event_recall": "true-event recall",
            "hidden_error_recall": "hidden-error recall",
            "tv": "disturbance TV",
        }[metric]
        rows.append(text(x + 30, legend_y + 2, legend_name, size=17))
    rows.extend([
        text(60, 700, "Interpretation:", size=18, weight=700),
        text(180, 700, "targeted policies trade event recovery against hidden-error recovery and sampling distortion; fixed disagreement is not a free improvement.", size=17),
    ])
    write_svg(output, rows)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    with csv_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("name", "event_recall", "hidden_error_recall", "tv"))
        writer.writeheader()
        writer.writerows(policies)


def fig3_v5_surface(data: dict, output: Path, csv_output: Path) -> None:
    rows = svg_header()
    rows += [
        text(60, 58, "Figure 3. Locked V5 falsification surface", size=32, weight=700),
        text(60, 94, "Fixed scalar disagreement passed the complete gate in only one of nine prevalence × budget regimes.", size=19, fill=MUTED),
    ]
    section = data["v5_locked_surface"]
    prevalences = section["prevalences"]
    budgets = section["budgets"]
    passes = section["full_gate_pass"]
    x0, y0, cell_w, cell_h = 280, 165, 240, 115
    for j, budget in enumerate(budgets):
        rows.append(text(x0 + j * cell_w + cell_w / 2, y0 - 28, f"budget {int(budget*100)}%", size=19, weight=700, anchor="middle"))
    for i, prevalence in enumerate(prevalences):
        rows.append(text(x0 - 25, y0 + i * cell_h + cell_h / 2 + 7, prevalence, size=20, weight=700, anchor="end"))
        for j, _ in enumerate(budgets):
            passed = bool(passes[i][j])
            fill = LIGHT_GREEN if passed else LIGHT_RED
            stroke = GREEN if passed else RED
            rows.append(rect(x0 + j * cell_w, y0 + i * cell_h, cell_w - 10, cell_h - 10, fill=fill, stroke=stroke, width=2, rx=10))
            rows.append(text(x0 + j * cell_w + (cell_w - 10) / 2, y0 + i * cell_h + 55, "PASS" if passed else "FAIL", size=24, weight=700, fill=stroke, anchor="middle"))
    rows.append(text(60, 555, "Locked findings retained from V5", size=21, weight=700))
    for i, finding in enumerate(section["locked_findings"]):
        rows.append(text(85, 592 + i * 28, "•", size=20, weight=700, fill=RED if i < 4 else GREEN))
        rows.append(text(110, 592 + i * 28, finding, size=16))
    write_svg(output, rows)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    with csv_output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("prevalence", "budget", "full_gate_pass"))
        for i, prevalence in enumerate(prevalences):
            for j, budget in enumerate(budgets):
                writer.writerow((prevalence, budget, int(bool(passes[i][j]))))


def fig4_v6_architecture(data: dict, output: Path) -> None:
    rows = svg_header()
    rows += [
        text(60, 58, "Figure 4. Failure localisation changes the role of disagreement", size=31, weight=700),
        text(60, 94, "V6 keeps observer outputs separate and guarantees exploration; disagreement moves outside the direct allocation path.", size=18, fill=MUTED),
    ]
    # Observers
    rows.append(rect(95, 170, 300, 115, fill=LIGHT_BLUE, stroke=BLUE, width=2))
    rows.append(text(245, 205, "Biological-evidence observer", size=20, weight=700, anchor="middle"))
    rows.append(text(245, 238, "event evidence", size=17, fill=BLUE, anchor="middle"))
    rows.append(rect(805, 170, 300, 115, fill="#e0f2f1", stroke=TEAL, width=2))
    rows.append(text(955, 205, "Observability-risk observer", size=20, weight=700, anchor="middle"))
    rows.append(text(955, 238, "false / missed / attribution risk", size=17, fill=TEAL, anchor="middle"))
    # Diagnostic disagreement
    rows.append(rect(450, 165, 300, 125, fill="#f3e5f5", stroke=PURPLE, width=2))
    rows.append(text(600, 202, "Contradiction channel", size=21, weight=700, fill=PURPLE, anchor="middle"))
    rows.append(text(600, 235, "diagnose / falsify / localise", size=17, anchor="middle"))
    rows.append(text(600, 264, "0% direct allocation quota", size=17, weight=700, fill=RED, anchor="middle"))
    rows.append(line(395, 227, 450, 227, stroke=PURPLE, width=2, dash="7,5"))
    rows.append(line(750, 227, 805, 227, stroke=PURPLE, width=2, dash="7,5"))
    # Portfolio
    rows.append(rect(230, 385, 740, 180, fill="#ffffff", stroke=INK, width=2, rx=16))
    rows.append(text(600, 420, "Frozen V6 observer portfolio", size=25, weight=700, anchor="middle"))
    parts = [
        (0.50, "uniform exploration", MUTED),
        (0.10, "biological evidence", BLUE),
        (0.40, "observability risk", TEAL),
    ]
    bar_x, bar_y, bar_w, bar_h = 300, 465, 600, 48
    cursor = bar_x
    for share, label, color in parts:
        w = bar_w * share
        rows.append(rect(cursor, bar_y, w, bar_h, fill=color, stroke="#ffffff", width=1, rx=0))
        rows.append(text(cursor + w / 2, bar_y + 31, f"{int(share*100)}%", size=17, weight=700, fill="#ffffff", anchor="middle"))
        cursor += w
    for i, (_, label, color) in enumerate(parts):
        x = 315 + i * 260
        rows.append(rect(x, 535, 18, 18, fill=color, stroke=color, width=0, rx=2))
        rows.append(text(x + 27, 550, label, size=15))
    # Theory
    rows.append(rect(120, 625, 960, 85, fill=LIGHT_GRAY, stroke=GRID, width=1, rx=10))
    rows.append(text(145, 657, "Exploration guard:", size=18, weight=700))
    rows.append(text(310, 657, "Q = αU + (1−α)R", size=18))
    rows.append(text(560, 657, "TV(Q,U) = (1−α)TV(R,U)", size=18))
    rows.append(text(145, 687, "Coverage floor: Q(A) ≥ αU(A)", size=17))
    rows.append(text(560, 687, "Importance ratio: U(x)/Q(x) ≤ 1/α", size=17))
    write_svg(output, rows)


def fig5_v6_candidates(data: dict, output: Path, csv_output: Path) -> None:
    rows = svg_header()
    rows += [
        text(60, 58, "Figure 5. Focused V6 high-resolution candidate gate", size=31, weight=700),
        text(60, 94, "Candidate selection was driven by predefined robustness and TV criteria, not by a single mean score.", size=18, fill=MUTED),
    ]
    candidates = data["v6_focused_candidates"]
    left, top, chart_w, chart_h = 130, 175, 930, 330
    rows.append(line(left, top + chart_h, left + chart_w, top + chart_h, stroke=INK, width=2))
    # joint axis 0.96..1.13
    for value in (0.98, 1.00, 1.02, 1.06, 1.10):
        y = top + chart_h - ((value - 0.96) / 0.18) * chart_h
        rows.append(line(left, y, left + chart_w, y, stroke=GRID, width=1, dash="5,5" if value == 1.00 else None))
        rows.append(text(left - 18, y + 6, f"{value:.2f}", size=14, fill=MUTED, anchor="end"))
    group_w = chart_w / len(candidates)
    for i, candidate in enumerate(candidates):
        cx = left + group_w * (i + 0.5)
        worst = candidate["worst_joint_ratio"]
        mean_joint = candidate["mean_joint_ratio"]
        if worst is not None:
            y = top + chart_h - ((worst - 0.96) / 0.18) * chart_h
            rows.append(circle(cx - 23, y, 9, fill=BLUE))
        if mean_joint is not None:
            y = top + chart_h - ((mean_joint - 0.96) / 0.18) * chart_h
            rows.append(circle(cx + 23, y, 9, fill=GREEN))
        rows.append(text(cx, top + chart_h + 32, candidate["name"], size=16, weight=700, anchor="middle"))
        gate_fill = LIGHT_GREEN if candidate["passed"] else LIGHT_RED
        gate_stroke = GREEN if candidate["passed"] else RED
        rows.append(rect(cx - 66, top + chart_h + 50, 132, 34, fill=gate_fill, stroke=gate_stroke, width=1, rx=7))
        rows.append(text(cx, top + chart_h + 73, "PASS" if candidate["passed"] else "FAIL", size=15, weight=700, fill=gate_stroke, anchor="middle"))
    # TV panel
    rows.append(text(80, 600, "Max disturbance TV", size=18, weight=700))
    tv_x0 = 315
    tv_scale = 600 / 0.30
    rows.append(line(tv_x0, 612, tv_x0 + 600, 612, stroke=GRID, width=4))
    threshold_x = tv_x0 + 0.25 * tv_scale
    rows.append(line(threshold_x, 580, threshold_x, 655, stroke=RED, width=2, dash="6,4"))
    rows.append(text(threshold_x, 674, "TV ceiling 0.25", size=14, fill=RED, anchor="middle"))
    for i, candidate in enumerate(candidates):
        tv = candidate["max_tv"]
        if tv is None:
            continue
        y = 585 + i * 22
        x = tv_x0 + tv * tv_scale
        rows.append(circle(x, y, 7, fill=GREEN if candidate["passed"] else RED, stroke="#ffffff", width=1))
        rows.append(text(940, y + 5, f"{candidate['name']} {tv:.5f}", size=13))
    rows.append(rect(82, 690, 1035, 45, fill=LIGHT_GRAY, stroke=GRID, width=1, rx=8))
    rows.append(text(100, 719, "Frozen choice: E50/P10/I40/D0 — stronger joint robustness than E60 while remaining below the predefined TV ceiling.", size=16))
    rows.append(rect(940, 125, 18, 18, fill=BLUE, stroke=BLUE, width=0, rx=9))
    rows.append(text(970, 140, "worst joint ratio", size=15))
    rows.append(rect(940, 150, 18, 18, fill=GREEN, stroke=GREEN, width=0, rx=9))
    rows.append(text(970, 165, "mean joint ratio", size=15))
    write_svg(output, rows)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    with csv_output.open("w", newline="", encoding="utf-8") as handle:
        fields = ("name", "exploration", "pollipi", "insepi", "disagreement", "passed", "worst_joint_ratio", "mean_joint_ratio", "max_tv", "failure")
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)


def build(evidence_path: Path, output_dir: Path) -> dict[str, object]:
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    if data.get("schema") != "insepi-method-paper-pre-v7-figure-evidence-v1":
        raise ValueError("unexpected pre-V7 figure evidence schema")
    if "V7" in data.get("scope", "") and "no V7 seed" not in data.get("scope", ""):
        raise ValueError("figure evidence scope does not explicitly exclude V7 outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "fig1_generation_timeline": output_dir / "fig1_generation_timeline.svg",
        "fig2_v3_equal_budget": output_dir / "fig2_v3_equal_budget.svg",
        "fig2_data": output_dir / "fig2_v3_equal_budget.csv",
        "fig3_v5_falsification_surface": output_dir / "fig3_v5_falsification_surface.svg",
        "fig3_data": output_dir / "fig3_v5_falsification_surface.csv",
        "fig4_v6_architecture": output_dir / "fig4_v6_architecture.svg",
        "fig5_v6_candidate_gate": output_dir / "fig5_v6_candidate_gate.svg",
        "fig5_data": output_dir / "fig5_v6_candidate_gate.csv",
    }
    fig1_generation_timeline(data, outputs["fig1_generation_timeline"])
    fig2_v3_equal_budget(data, outputs["fig2_v3_equal_budget"], outputs["fig2_data"])
    fig3_v5_surface(data, outputs["fig3_v5_falsification_surface"], outputs["fig3_data"])
    fig4_v6_architecture(data, outputs["fig4_v6_architecture"])
    fig5_v6_candidates(data, outputs["fig5_v6_candidate_gate"], outputs["fig5_data"])
    manifest = {
        "schema": "insepi-method-paper-pre-v7-figure-manifest-v1",
        "evidence_sha256": file_sha256(evidence_path),
        "outputs": {name: {"path": str(path), "sha256": file_sha256(path)} for name, path in outputs.items()},
        "v7_materialised": False,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="manuscript/figures/pre_v7_evidence.json")
    parser.add_argument("--output-dir", default="manuscript/figures/generated")
    args = parser.parse_args()
    manifest = build(Path(args.evidence), Path(args.output_dir))
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
