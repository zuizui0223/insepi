#!/usr/bin/env python3
"""Finalize the reviewer manuscript, SI and Figure 6 from a locked V7 ledger.

This script is intentionally downstream of V7. It never renders V7 worlds, calls
observers, changes pass/fail rules or recomputes the scientific gate. It accepts
only the immutable execution ledger and report, verifies their internal hashes and
claim level, then fills pre-registered manuscript/SI placeholders and renders a
fixed result figure.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import html
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


LEDGER_SCHEMA = "pollipi-insepi-v7-execution-ledger-v1"
REPORT_SCHEMA = "pollipi-insepi-v7-report-v1"
CLAIM_LEVELS = {"A", "B", "C", "D", "E"}

MAIN_MARKERS = {
    "abstract": "[[V7_LOCKED_RESULT:ABSTRACT]]",
    "table": "[[V7_LOCKED_RESULT:TABLE]]",
    "results": "[[V7_LOCKED_RESULT:RESULTS]]",
    "discussion": "[[V7_LOCKED_RESULT:DISCUSSION]]",
    "repro": "[[V7_LOCKED_RESULT:REPRODUCIBILITY_LEDGER]]",
}
SI_MARKERS = {
    "status": "[[V7_LOCKED_RESULT:STATUS]]",
    "supplementary": "[[V7_LOCKED_RESULT:SUPPLEMENTARY]]",
}

POLICY_LABELS = {
    "uniform": "Uniform",
    "pollipi_candidate": "Observer-E only",
    "insepi_audit": "Observer-O only",
    "legacy_fixed_disagreement": "Legacy fixed disagreement",
    "candidate_or_risky": "Candidate OR risky",
    "candidate_and_risky": "Candidate AND risky",
    "v6_frozen": "Frozen V6",
    "v6_no_pollipi": "V6 without Observer-E arm",
    "v6_no_insepi": "V6 without Observer-O arm",
}


@dataclass(frozen=True, slots=True)
class VerifiedV7:
    ledger: dict[str, object]
    report: dict[str, object]
    claim_level: str
    gate_passed: bool
    failures: tuple[str, ...]
    worst_joint: float
    mean_joint: float
    max_tv: float


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def anonymous_commit_id(original: str) -> str:
    digest = hashlib.sha256(("mee-double-anonymous|" + original.lower()).encode("utf-8")).hexdigest()[:10]
    return f"[anonymous-commit-{digest}]"


def _float_dict_equal(left: Mapping[str, object], right: Mapping[str, object]) -> bool:
    if set(left) != set(right):
        return False
    for key in left:
        a, b = left[key], right[key]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(float(a) - float(b)) > 1e-12:
                return False
        elif a != b:
            return False
    return True


def verify_v7(ledger_path: Path, report_path: Path) -> VerifiedV7:
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if ledger.get("schema") != LEDGER_SCHEMA:
        raise ValueError("unexpected V7 execution-ledger schema")
    if report.get("schema") != REPORT_SCHEMA:
        raise ValueError("unexpected V7 report schema")
    if ledger.get("report_sha256") != sha256_file(report_path):
        raise ValueError("V7 report file hash differs from execution ledger")

    claim = str(ledger.get("claim_level", ""))
    if claim not in CLAIM_LEVELS:
        raise ValueError(f"unexpected V7 claim level: {claim!r}")
    if report.get("claim_level") != claim:
        raise ValueError("V7 report and ledger claim levels differ")

    gate = report.get("gate")
    if not isinstance(gate, Mapping):
        raise ValueError("V7 report is missing gate")
    passed = bool(gate.get("passed"))
    if bool(ledger.get("gate_passed")) != passed:
        raise ValueError("V7 report and ledger gate status differ")
    if claim == "A" and not passed:
        raise ValueError("claim A requires a passing locked gate")
    if claim != "A" and passed:
        raise ValueError("a passing locked gate must map to claim A")

    failures = tuple(str(item) for item in ledger.get("gate_failures", []))
    if tuple(str(item) for item in gate.get("failures", [])) != failures:
        raise ValueError("V7 report and ledger failure lists differ")

    v6_ledger = ledger.get("v6_robustness")
    v6_report = gate.get("v6")
    if not isinstance(v6_ledger, Mapping) or not isinstance(v6_report, Mapping):
        raise ValueError("V7 robustness summary is missing")
    if not _float_dict_equal(v6_ledger, v6_report):
        raise ValueError("V7 report and ledger robustness summaries differ")

    provenance = report.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("V7 report is missing provenance")
    for key in (
        "world_fingerprint",
        "pixel_artifact_sha256",
        "pollipi_trace_sha256",
        "insepi_trace_sha256",
        "pollipi_source_commit",
        "insepi_source_commit",
        "allocator_sha",
        "generator_sha",
        "world_spec_sha256",
        "baseline_registry_sha256",
    ):
        if str(provenance.get(key, "")) != str(ledger.get(key, "")):
            raise ValueError(f"V7 report/ledger provenance mismatch: {key}")

    metrics = report.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("V7 report contains no policy metrics")
    policies = {str(row.get("policy")) for row in metrics if isinstance(row, Mapping)}
    if not {"uniform", "v6_frozen"}.issubset(policies):
        raise ValueError("V7 report must contain uniform and v6_frozen metrics")
    regimes = {
        (float(row["prevalence"]), float(row["budget"]))
        for row in metrics
        if isinstance(row, Mapping) and str(row.get("policy")) == "v6_frozen"
    }
    expected_regimes = {(p, b) for p in (0.1, 0.5, 0.9) for b in (0.1, 0.25, 0.5)}
    if regimes != expected_regimes:
        raise ValueError("V7 report does not contain all nine frozen V6 regimes")

    return VerifiedV7(
        ledger=dict(ledger),
        report=dict(report),
        claim_level=claim,
        gate_passed=passed,
        failures=failures,
        worst_joint=float(v6_ledger["worst_joint_ratio"]),
        mean_joint=float(v6_ledger["mean_joint_ratio"]),
        max_tv=float(v6_ledger["max_tv"]),
    )


def _failure_phrase(failures: Sequence[str]) -> str:
    if not failures:
        return "none"
    return "; ".join(f"`{item}`" for item in failures)


def claim_texts(v7: VerifiedV7) -> dict[str, str]:
    w, m, tv = v7.worst_joint, v7.mean_joint, v7.max_tv
    level = v7.claim_level
    if level == "A":
        abstract = (
            f"In the one-shot locked V7 simulation, the frozen portfolio passed all preregistered hard rules "
            f"(worst joint ratio {w:.3f}, mean joint ratio {m:.3f}, maximum TV {tv:.3f}), supporting a simulation-level claim of robustness across the tested prevalence and budget shifts."
        )
        discussion = (
            "V7 therefore supports the strongest preregistered simulation claim: the frozen exploration-guarded portfolio survived a new locked prevalence/budget challenge without violating the sampling-distortion ceiling or being strictly dominated by either observer-arm removal. This remains a simulation-method result, not field validation."
        )
    elif level == "B":
        abstract = (
            f"The one-shot locked V7 simulation did not satisfy the full robustness gate (claim level B; worst joint ratio {w:.3f}, mean {m:.3f}, maximum TV {tv:.3f}), so the allocation benefit is conditional rather than generally robust across prevalence and budget."
        )
        discussion = (
            "V7 limits the performance claim to a conditional allocation result. Average benefit and sampling control may remain, but at least one preregistered robustness condition failed; the frozen allocator must therefore not be described as generally prevalence/budget robust."
        )
    elif level == "C":
        abstract = (
            f"The one-shot locked V7 simulation did not establish a general recovery advantage (claim level C; worst joint ratio {w:.3f}, mean {m:.3f}, maximum TV {tv:.3f}), leaving the exploration guard's bias-control properties as the principal allocation result."
        )
        discussion = (
            "V7 does not support a general recovery advantage for the tested observer portfolio. The defensible allocation claim is instead the analytical and empirical bias-control role of guaranteed exploration; targeted observer quotas should be treated as task-dependent components requiring separate validation."
        )
    elif level == "D":
        abstract = (
            f"The one-shot locked V7 simulation rejected a superior-allocation claim for the full dual-observer portfolio (claim level D; worst joint ratio {w:.3f}, mean {m:.3f}, maximum TV {tv:.3f}); the surviving contribution is contradiction-guided development and explicit sampling safeguards rather than allocator superiority."
        )
        discussion = (
            "V7 recentres the paper on contradiction-guided development. The full dual-observer allocation cannot be claimed superior under the locked criteria; the value of the two observers is therefore diagnostic and hypothesis-localising, while any future allocation redesign constitutes a new method generation requiring a new validation generation."
        )
    else:  # E
        abstract = (
            "The locked V7 evidence did not support a valid performance claim (claim level E); the contribution is therefore restricted to the preserved benchmark/falsification record and reproducibility lessons."
        )
        discussion = (
            "V7 permits only a benchmark/falsification interpretation. No best-allocation or robustness claim is retained, and any revised method must begin a new development and validation generation."
        )

    results = (
        f"The one-shot V7 ledger assigned **claim level {level}**. The frozen V6 portfolio had worst joint ratio "
        f"**{w:.6f}**, mean joint ratio **{m:.6f}**, and maximum disturbance-distribution TV **{tv:.6f}**. "
        f"The locked scientific gate was **{'PASS' if v7.gate_passed else 'FAIL'}**. "
        f"Recorded failed rules: {_failure_phrase(v7.failures)}. The result was retained without changing V6 weights, thresholds, baselines or the V7 seed."
    )
    table = f"{'PASS' if v7.gate_passed else 'FAIL'}; claim level {level}"
    return {"abstract": abstract, "results": results, "discussion": discussion, "table": table}


def reproducibility_text(v7: VerifiedV7) -> str:
    led = v7.ledger
    return "\n".join(
        (
            f"- V7 claim level: **{v7.claim_level}**",
            f"- locked gate: **{'PASS' if v7.gate_passed else 'FAIL'}**",
            f"- world fingerprint: `{led['world_fingerprint']}`",
            f"- pixel artifact SHA-256: `{led['pixel_artifact_sha256']}`",
            f"- Observer-E trace SHA-256: `{led['pollipi_trace_sha256']}`",
            f"- Observer-O trace SHA-256: `{led['insepi_trace_sha256']}`",
            f"- final report SHA-256: `{led['report_sha256']}`",
            f"- Observer-E source: `{anonymous_commit_id(str(led['pollipi_source_commit']))}`",
            f"- Observer-O source: `{anonymous_commit_id(str(led['insepi_source_commit']))}`",
            f"- allocator source: `{anonymous_commit_id(str(led['allocator_sha']))}`",
            f"- generator source: `{anonymous_commit_id(str(led['generator_sha']))}`",
        )
    )


def replace_exact(text: str, marker: str, replacement: str) -> str:
    count = text.count(marker)
    if count != 1:
        raise ValueError(f"expected exactly one {marker}, found {count}")
    return text.replace(marker, replacement, 1)


def finalize_manuscript(pre_text: str, v7: VerifiedV7) -> str:
    parts = claim_texts(v7)
    text = replace_exact(pre_text, MAIN_MARKERS["abstract"], parts["abstract"])
    text = replace_exact(text, MAIN_MARKERS["table"], parts["table"])
    text = replace_exact(text, MAIN_MARKERS["results"], parts["results"])
    text = replace_exact(text, MAIN_MARKERS["discussion"], parts["discussion"])
    text = replace_exact(text, MAIN_MARKERS["repro"], reproducibility_text(v7))
    if "[[V7_LOCKED_RESULT" in text:
        raise ValueError("final manuscript still contains V7 placeholders")
    return text


def _policy_label(policy: str) -> str:
    return POLICY_LABELS.get(policy, policy.replace("_", " "))


def _metrics_table(report: Mapping[str, object]) -> str:
    rows = [row for row in report["metrics"] if isinstance(row, Mapping)]
    lines = [
        "| Prevalence | Budget | Policy | Event recall | Observer-relative hidden-error recall | Captures/error | TV |",
        "|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in sorted(rows, key=lambda r: (float(r["prevalence"]), float(r["budget"]), str(r["policy"]))):
        cpe = row.get("captures_per_hidden_error")
        cpe_text = "NA" if cpe is None else f"{float(cpe):.4f}"
        lines.append(
            f"| {float(row['prevalence']):.2f} | {float(row['budget']):.2f} | {_policy_label(str(row['policy']))} | "
            f"{float(row['true_event_recall']):.4f} | {float(row['hidden_error_recall']):.4f} | {cpe_text} | {float(row['disturbance_tv_distance']):.4f} |"
        )
    return "\n".join(lines)


def finalize_supplement(pre_text: str, v7: VerifiedV7) -> str:
    status = (
        f"V7 executed once under the frozen protocol. Scientific gate: **{'PASS' if v7.gate_passed else 'FAIL'}**; "
        f"claim level: **{v7.claim_level}**; worst joint ratio={v7.worst_joint:.6f}; mean joint ratio={v7.mean_joint:.6f}; "
        f"maximum TV={v7.max_tv:.6f}."
    )
    supplementary = "\n\n".join(
        (
            f"### S9.1. Locked gate\n\n{status}\n\nFailed rules: {_failure_phrase(v7.failures)}.",
            "### S9.2. Complete policy metrics\n\n" + _metrics_table(v7.report),
            "### S9.3. Immutable provenance\n\n" + reproducibility_text(v7),
        )
    )
    text = replace_exact(pre_text, SI_MARKERS["status"], status)
    text = replace_exact(text, SI_MARKERS["supplementary"], supplementary)
    # The generic preamble placeholder documents the boundary; after execution it
    # is replaced with a short immutable-status sentence too.
    text = text.replace("[[V7_LOCKED_RESULT]]", f"V7 completed at claim level {v7.claim_level} under the locked protocol.")
    if "[[V7_LOCKED_RESULT" in text:
        raise ValueError("final supplementary information still contains V7 placeholders")
    return text


def _regime_rows(report: Mapping[str, object]) -> list[dict[str, float]]:
    metrics = [row for row in report["metrics"] if isinstance(row, Mapping)]
    by_key = {
        (float(row["prevalence"]), float(row["budget"]), str(row["policy"])): row
        for row in metrics
    }
    rows: list[dict[str, float]] = []
    for prevalence in (0.1, 0.5, 0.9):
        for budget in (0.1, 0.25, 0.5):
            v6 = by_key[(prevalence, budget, "v6_frozen")]
            uniform = by_key[(prevalence, budget, "uniform")]
            event_ratio = float(v6["true_event_recall"]) / float(uniform["true_event_recall"])
            error_ratio = float(v6["hidden_error_recall"]) / float(uniform["hidden_error_recall"])
            rows.append(
                {
                    "prevalence": prevalence,
                    "budget": budget,
                    "event_ratio": event_ratio,
                    "error_ratio": error_ratio,
                    "joint_ratio": min(event_ratio, error_ratio),
                    "tv": float(v6["disturbance_tv_distance"]),
                }
            )
    return rows


def write_figure6_csv(path: Path, v7: VerifiedV7) -> None:
    rows = _regime_rows(v7.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("prevalence", "budget", "event_ratio", "error_ratio", "joint_ratio", "tv"))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _svg_text(x: float, y: float, text: str, size: int = 15, weight: str = "400", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="#202124" text-anchor="{anchor}">{html.escape(text)}</text>'
    )


def write_figure6_svg(path: Path, v7: VerifiedV7) -> None:
    rows = _regime_rows(v7.report)
    width, height = 1200, 760
    margin_x = 70
    panel_w = 330
    panel_gap = 35
    top, plot_h = 125, 340
    ratios = [value for row in rows for value in (row["event_ratio"], row["error_ratio"])]
    y_min = min(0.75, min(ratios) - 0.05)
    y_max = max(1.25, max(ratios) + 0.05)

    def ymap(value: float) -> float:
        return top + plot_h * (y_max - value) / (y_max - y_min)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        _svg_text(60, 48, "Figure 6. One-shot locked V7 validation", 25, "700"),
        _svg_text(60, 78, f"Scientific gate: {'PASS' if v7.gate_passed else 'FAIL'}  |  preregistered claim level: {v7.claim_level}", 17, "700"),
    ]
    prevalence_labels = {0.1: "rare prevalence (0.10)", 0.5: "balanced prevalence (0.50)", 0.9: "common prevalence (0.90)"}
    for panel_idx, prevalence in enumerate((0.1, 0.5, 0.9)):
        x0 = margin_x + panel_idx * (panel_w + panel_gap)
        svg.append(_svg_text(x0 + panel_w / 2, 110, prevalence_labels[prevalence], 16, "700", "middle"))
        svg.append(f'<rect x="{x0}" y="{top}" width="{panel_w}" height="{plot_h}" fill="none" stroke="#5f6368" stroke-width="1"/>')
        for ref, dash, label in ((1.0, "", "uniform"), (0.98, "6,5", "locked floor")):
            y = ymap(ref)
            dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
            svg.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0+panel_w}" y2="{y:.1f}" stroke="#9aa0a6" stroke-width="1"{dash_attr}/>')
            if panel_idx == 0:
                svg.append(_svg_text(x0 - 8, y + 5, f"{ref:.2f}", 12, "400", "end"))
        subset = [row for row in rows if row["prevalence"] == prevalence]
        xs = [x0 + 65, x0 + panel_w / 2, x0 + panel_w - 65]
        for i, row in enumerate(subset):
            x = xs[i]
            svg.append(_svg_text(x, top + plot_h + 25, f"{int(row['budget']*100)}%", 13, "400", "middle"))
            for ratio, shape in ((row["event_ratio"], "circle"), (row["error_ratio"], "square")):
                y = ymap(ratio)
                if shape == "circle":
                    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#1a73e8"/>')
                else:
                    svg.append(f'<rect x="{x-6:.1f}" y="{y-6:.1f}" width="12" height="12" fill="#d93025"/>')
            svg.append(_svg_text(x, top + plot_h + 45, f"TV {row['tv']:.3f}", 11, "400", "middle"))
    svg.extend(
        [
            '<circle cx="80" cy="530" r="6" fill="#1a73e8"/>',
            _svg_text(95, 535, "event-recall ratio to uniform", 14),
            '<rect x="350" y="524" width="12" height="12" fill="#d93025"/>',
            _svg_text(370, 535, "observer-relative hidden-error ratio to uniform", 14),
            _svg_text(60, 590, f"Worst joint ratio = {v7.worst_joint:.6f}", 17, "700"),
            _svg_text(60, 620, f"Mean joint ratio = {v7.mean_joint:.6f}", 17),
            _svg_text(60, 650, f"Maximum disturbance TV = {v7.max_tv:.6f}", 17),
            _svg_text(60, 690, "Result interpretation is fixed by the preregistered A–E claim ceiling; scientific FAIL remains a valid reproducible execution.", 14),
            '</svg>',
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def write_receipt(path: Path, *, v7: VerifiedV7, outputs: Mapping[str, Path], ledger_path: Path, report_path: Path) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "mee-v7-submission-finalization-receipt-v1",
        "claim_level": v7.claim_level,
        "gate_passed": v7.gate_passed,
        "source_ledger_sha256": sha256_file(ledger_path),
        "source_report_sha256": sha256_file(report_path),
        "locked_report_sha256": v7.ledger["report_sha256"],
        "outputs": {name: {"path": str(p), "sha256": sha256_file(p)} for name, p in sorted(outputs.items())},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--pre-manuscript", default="manuscript/generated/MEE_PRE_V7_SUBMISSION.md", type=Path)
    parser.add_argument("--pre-supplement", default="manuscript/SUPPLEMENTARY_INFORMATION_PRE_V7.md", type=Path)
    parser.add_argument("--output-manuscript", default="manuscript/generated/MEE_FINAL_SUBMISSION.md", type=Path)
    parser.add_argument("--output-supplement", default="manuscript/generated/SUPPLEMENTARY_INFORMATION_FINAL.md", type=Path)
    parser.add_argument("--figure-svg", default="manuscript/figures/generated/fig6_v7_locked_validation.svg", type=Path)
    parser.add_argument("--figure-csv", default="manuscript/figures/generated/fig6_v7_locked_validation.csv", type=Path)
    parser.add_argument("--receipt", default="manuscript/generated/V7_SUBMISSION_FINALIZATION_RECEIPT.json", type=Path)
    args = parser.parse_args()

    v7 = verify_v7(args.ledger, args.report)
    manuscript = finalize_manuscript(args.pre_manuscript.read_text(encoding="utf-8"), v7)
    supplement = finalize_supplement(args.pre_supplement.read_text(encoding="utf-8"), v7)
    args.output_manuscript.parent.mkdir(parents=True, exist_ok=True)
    args.output_manuscript.write_text(manuscript, encoding="utf-8")
    args.output_supplement.parent.mkdir(parents=True, exist_ok=True)
    args.output_supplement.write_text(supplement, encoding="utf-8")
    write_figure6_csv(args.figure_csv, v7)
    write_figure6_svg(args.figure_svg, v7)
    outputs = {
        "manuscript": args.output_manuscript,
        "supplement": args.output_supplement,
        "figure6_svg": args.figure_svg,
        "figure6_csv": args.figure_csv,
    }
    receipt = write_receipt(args.receipt, v7=v7, outputs=outputs, ledger_path=args.ledger, report_path=args.report)
    print("MEE_V7_FINAL_CLAIM_LEVEL", v7.claim_level)
    print("MEE_V7_FINAL_GATE", "PASS" if v7.gate_passed else "FAIL")
    print("MEE_V7_FINAL_RECEIPT", receipt["receipt_sha256"])


if __name__ == "__main__":
    main()
