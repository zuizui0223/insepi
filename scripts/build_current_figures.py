#!/usr/bin/env python3
"""Build deterministic current MEE figures from frozen headline evidence.

The figures are presentation artefacts. They do not run scientific simulations or
change any generation-specific claim. V13 is rendered as protocol/result-pending.
"""
from __future__ import annotations

import csv
from html import escape
from pathlib import Path


OUT = Path("manuscript/figures/current")
W, H = 1200, 760
INK = "#17212b"
MUTED = "#5b6773"
LIGHT = "#eef2f5"
BLUE = "#3465a4"
TEAL = "#2b8a7e"
ORANGE = "#c9792b"
RED = "#b64b4b"
GREEN = "#4d8b5f"
PURPLE = "#7556a3"


def t(x: float, y: float, text: str, size: int = 22, weight: int = 400, anchor: str = "start", fill: str = INK) -> str:
    return f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">{escape(text)}</text>'


def r(x: float, y: float, w: float, h: float, fill: str = "white", stroke: str = "#c7d0d9", sw: float = 2, rx: float = 12) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def l(x1: float, y1: float, x2: float, y2: float, stroke: str = MUTED, sw: float = 3, dash: str | None = None) -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def c(x: float, y: float, radius: float, fill: str, stroke: str = "white", sw: float = 2) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def arrow(x1: float, y1: float, x2: float, y2: float, stroke: str = MUTED) -> str:
    return l(x1, y1, x2, y2, stroke, 3) + f'<polygon points="{x2},{y2} {x2-12},{y2-7} {x2-12},{y2+7}" fill="{stroke}"/>'


def wrap_text(x: float, y: float, lines: list[str], size: int = 18, fill: str = INK, leading: int = 25, weight: int = 400, anchor: str = "start") -> str:
    return "".join(t(x, y + i * leading, line, size, weight, anchor, fill) for i, line in enumerate(lines))


def frame(title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        r(0, 0, W, H, "white", "white", 0, 0),
        t(50, 52, title, 30, 700),
        t(50, 82, subtitle, 17, 400, "start", MUTED),
    ]


def finish(parts: list[str]) -> str:
    parts.append("</svg>\n")
    return "".join(parts)


def write_svg(name: str, parts: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(finish(parts), encoding="utf-8")


def write_csv(name: str, header: list[str], rows: list[list[object]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def fig1() -> None:
    p = frame("Fig. 1 | Three observation lanes and contradiction-guided development", "Different scientific objectives remain separate; contradiction selects tests rather than truth or an automatic priority score.")
    p += [r(65, 130, 260, 105, "#eef5fb", BLUE), t(195, 165, "Biological evidence", 23, 700, "middle", BLUE), t(195, 195, "event-candidate enrichment", 17, 400, "middle"),
          r(65, 305, 260, 105, "#edf8f5", TEAL), t(195, 340, "Observability risk", 23, 700, "middle", TEAL), t(195, 370, "observation-failure audit", 17, 400, "middle"),
          r(65, 480, 260, 105, "#f7f2fb", PURPLE), t(195, 515, "Protected random audit", 23, 700, "middle", PURPLE), t(195, 545, "probability-sample denominator", 17, 400, "middle")]
    p += [arrow(325, 182, 470, 260), arrow(325, 357, 470, 285), arrow(325, 532, 470, 510)]
    p += [r(470, 205, 285, 155, "#fff7ed", ORANGE), t(612, 245, "Contradiction", 25, 700, "middle", ORANGE), wrap_text(612, 278, ["generate competing", "failure hypotheses"], 18, INK, 25, 400, "middle")]
    p += [arrow(755, 282, 860, 282, ORANGE), r(860, 205, 275, 155, "#fff4f4", RED), t(997, 245, "Controlled intervention", 23, 700, "middle", RED), wrap_text(997, 278, ["choose the test that", "separates hypotheses"], 18, INK, 25, 400, "middle")]
    p += [arrow(997, 360, 997, 455, GREEN), r(820, 455, 355, 125, "#f1f8f2", GREEN), t(997, 492, "Paired response diagnosis", 23, 700, "middle", GREEN), t(997, 525, "(Δ evidence, Δ observability)", 19, 400, "middle"), t(997, 552, "prediction before truth unseal", 17, 400, "middle", MUTED)]
    p += [l(470, 510, 755, 510, PURPLE, 3), t(612, 490, "Random lane independently samples agreement / silence", 16, 400, "middle", PURPLE), t(600, 670, "No arrow runs from disagreement directly to truth or final acquisition priority.", 19, 700, "middle", RED)]
    write_svg("fig1_architecture.svg", p)


def fig2() -> None:
    p = frame("Fig. 2 | Frozen generations turn failure into method development", "Negative generations are preserved and constrain what later generations are allowed to claim.")
    generations = [
        ("V3", "direct disagreement", "NEG", RED),
        ("V5", "scalar disagreement", "FAIL", RED),
        ("V7", "50/10/40 locked", "FAIL/C", RED),
        ("V8", "generality map", "MAP", BLUE),
        ("V9", "design inference", "PASS", GREEN),
        ("V10", "real pixels", "C", ORANGE),
        ("V11", "static localisation", "FAIL/D", RED),
        ("V12", "causal intervention", "B", GREEN),
        ("V13", "physical validation", "PENDING", PURPLE),
    ]
    x0, y, dx = 80, 300, 125
    p.append(l(x0, y, x0 + dx * (len(generations)-1), y, "#aab4be", 5))
    for i, (g, label, status, color) in enumerate(generations):
        x = x0 + i * dx
        p += [c(x, y, 20, color), t(x, y+7, g, 15, 700, "middle", "white"), t(x, y-48, status, 17, 700, "middle", color)]
        lines = label.split(" ")
        p += wrap_text(x, y+52, lines, 15, INK, 21, 400, "middle")
    p += [r(140, 520, 920, 115, "#f7f9fb", "#c7d0d9"), t(600, 555, "Claim-bearing pivot", 21, 700, "middle"), t(600, 590, "passive contradiction → failed static causal labels → intervention-response diagnosis", 20, 400, "middle"), t(600, 620, "V13 tests physical transfer without rewriting V7/V11 failures", 17, 400, "middle", MUTED)]
    write_svg("fig2_generation_ledger.svg", p)
    write_csv("fig2_generation_ledger.csv", ["generation", "label", "status"], [[g, label, status] for g, label, status, _ in generations])


def fig3() -> None:
    p = frame("Fig. 3 | Guarded allocation is a robustness architecture, not a universal winner", "Development success, locked failure and broad generality are shown together.")
    # Panel A: V6 candidates scatter
    p += [t(70, 135, "A  V6 development candidates", 21, 700), l(90, 360, 425, 360), l(90, 180, 90, 360)]
    candidates = [(0.26567,1.00842,"U40",RED),(0.21919,1.00846,"U50",GREEN),(0.17222,1.00832,"U60",BLUE),(0.12907,0.98329,"U70",ORANGE)]
    for tv, joint, label, color in candidates:
        x = 100 + (tv-0.12)/(0.28-0.12)*300
        yy = 345 - (joint-0.98)/(1.012-0.98)*145
        p += [c(x, yy, 9, color), t(x+12, yy+5, label, 14, 700, "start", color)]
    p += [t(255, 392, "max disturbance TV", 15, 400, "middle", MUTED), t(54, 270, "worst joint", 15, 400, "middle", MUTED)]
    # Panel B: V7
    p += [t(480, 135, "B  V7 locked unseen-world test", 21, 700)]
    vals = [("worst",0.9247839629,RED),("mean",0.9509088103,ORANGE),("uniform",1.0,MUTED)]
    for i,(lab,val,color) in enumerate(vals):
        x=500+i*105; bh=val*150
        p += [r(x, 360-bh, 60, bh, color, color, 0, 4), t(x+30, 385, lab, 14, 400, "middle"), t(x+30, 350-bh, f"{val:.3f}", 14, 700, "middle", color)]
    p += [t(645, 430, "gate FAIL / claim C", 18, 700, "middle", RED), t(645, 457, "max TV = 0.2025", 16, 400, "middle", MUTED)]
    # Panel C: V8
    p += [t(835, 135, "C  V8 abstract regimes", 21, 700)]
    bars=[("≥ uniform",91.9,GREEN),("regime-wise best",21.4,BLUE)]
    for i,(lab,val,color) in enumerate(bars):
        y0=215+i*125; bw=val/100*280
        p += [r(850,y0,280,36,LIGHT,LIGHT,0,4),r(850,y0,bw,36,color,color,0,4),t(850,y0-10,lab,15,700),t(1135,y0+26,f"{val:.1f}%",16,700,"end",color)]
    p += [t(990, 500, "794 / 864 ≥ uniform", 17, 700, "middle", GREEN), t(990, 530, "185 / 864 best same-α", 17, 700, "middle", BLUE), t(990, 575, "weakest at very common events", 15, 400, "middle", MUTED), t(990, 598, "and high residual correlation", 15, 400, "middle", MUTED)]
    p += [t(600, 690, "50U/10E/40O is retained as a tested robust compromise—not an optimal allocation.", 19, 700, "middle", INK)]
    write_svg("fig3_allocation_evidence.svg", p)
    write_csv("fig3_allocation_evidence.csv", ["generation","metric","value"], [["V7","worst_joint",0.9247839629],["V7","mean_joint",0.9509088103],["V7","max_tv",0.202475],["V8","uniform_or_better_pct",91.9],["V8","regime_best_pct",21.4]])


def fig4() -> None:
    p = frame("Fig. 4 | Protected random exploration is an inferential design component", "Targeting enriches selected observations; the protected probability sample preserves a denominator and audits shared blind spots.")
    p += [t(70, 145, "A  Sampling guarantee", 21, 700), r(70,175,480,175,"#f7f9fb"), t(310,215,"Q = αU + (1−α)R",25,700,"middle",BLUE), t(310,252,"TV(Q,U) ≤ 1−α",19,400,"middle"), t(310,282,"Q(A) ≥ αU(A)",19,400,"middle"), t(310,312,"P(miss family) = C(N−m,qU) / C(N,qU)",17,400,"middle")]
    p += [t(640,145,"B  V9 finite-population inference",21,700)]
    # Coverage bars
    p += [t(660,195,"95% interval coverage",16,700), r(660,215,420,34,LIGHT,LIGHT,0,4), r(660,215,410,34,GREEN,GREEN,0,4), t(1095,240,"97.75%",16,700,"end",GREEN), t(660,280,"naive targeted sample",15,400), r(660,300,420,34,LIGHT,LIGHT,0,4), r(660,300,220,34,RED,RED,0,4), t(1095,325,"52.4%",16,700,"end",RED)]
    p += [t(70,405,"C  Bias",21,700), r(70,435,480,115,"#f7f9fb"), t(310,472,"protected mean bias ≈ 0.000001",18,700,"middle",GREEN), t(310,510,"naive mean bias ≈ +0.0426",18,700,"middle",RED)]
    p += [t(640,405,"D  Shared-blind-spot audit",21,700), r(640,435,480,115,"#fff7ed",ORANGE), t(880,472,"Observer-E quiet + Observer-O low risk",18,700,"middle"), t(880,505,"does not prove the condition is truly absent",17,400,"middle"), t(880,532,"random lane can still sample it",17,700,"middle",PURPLE)]
    p += [t(600,680,"Protected random audit solves a different problem from targeted event/risk enrichment.",20,700,"middle")]
    write_svg("fig4_protected_random_audit.svg", p)
    write_csv("fig4_v9_inference.csv", ["estimator","mean_bias","coverage_pct","rmse"], [["protected_exploration",0.00000091,97.75,0.04282],["naive_targeted",0.0426,52.4,""]])


def fig5() -> None:
    p = frame("Fig. 5 | Static contradiction failed; controlled interventions restored identifiability", "The largest separate-channel benefit appears after the first discriminating intervention.")
    p += [t(65,140,"A  V11 static held-out localisation",21,700)]
    vals=[("contradiction",0.3469,RED),("early fusion",0.5058,ORANGE),("observability",0.4475,TEAL)]
    for i,(lab,val,color) in enumerate(vals):
        x=80+i*145; bh=val*250
        p += [r(x,390-bh,90,bh,color,color,0,4),t(x+45,420,lab,14,400,"middle"),t(x+45,380-bh,f"{val:.3f}",15,700,"middle",color)]
    p += [t(250,475,"claim D",18,700,"middle",RED),t(250,505,"fault → no-fault collapse",16,400,"middle",MUTED)]
    p += [t(590,140,"B  V12 diagnostic accuracy",21,700)]
    # two intervention stages as grouped bars
    stages=[("after 1",0.9608,0.7367),("after 2",0.9858,0.9658)]
    for i,(stage,dual,fused) in enumerate(stages):
        x=620+i*250
        for j,(val,color,label) in enumerate(((dual,GREEN,"dual"),(fused,ORANGE,"fusion"))):
            bx=x+j*90; bh=val*250
            p += [r(bx,390-bh,65,bh,color,color,0,4),t(bx+32,380-bh,f"{val:.3f}",14,700,"middle",color),t(bx+32,420,label,13,400,"middle")]
        p += [t(x+75,455,stage,16,700,"middle")]
    p += [t(835,505,"wrong-module rate",16,700,"middle"),t(835,535,"dual 0.0159  |  fusion 0.0433",16,400,"middle"),t(835,570,"stable diagnosis",16,700,"middle"),t(835,600,"1.01 vs 1.26 interventions",16,400,"middle")]
    # conceptual projection inset
    p += [r(510,630,630,70,"#f7f9fb"),t(825,660,"Separate response vectors can remain distinct even when scalar projection collapses them.",16,700,"middle"),t(825,686,"V12 claim B: conditional causal-identification advantage",16,400,"middle",GREEN)]
    write_svg("fig5_causal_diagnosis.svg", p)
    write_csv("fig5_diagnostic_results.csv", ["generation","strategy","after_1","after_2","wrong_module_rate"], [["V11","contradiction_static","",0.3469,0.8707],["V12","dual",0.9608,0.9858,0.0159],["V12","early_scalar_fusion",0.7367,0.9658,0.0433],["V12","event_only",0.7653,0.8767,0.0885],["V12","observability_only",0.7794,0.8772,0.0867]])


def fig6() -> None:
    p = frame("Fig. 6 | Transfer boundary from real image texture to blinded physical validation", "V10 supports partial observation-process transfer; V13 is frozen before acquisition and has no performance result yet.")
    p += [t(70,145,"A  V10 real-pixel perturbation transfer",21,700),r(70,175,480,250,"#f7f9fb"),t(310,215,"7 frozen honeybee videos",20,700,"middle"),t(310,250,"6 families × 3 intensity tiers",18,400,"middle"),t(310,285,"positive high-tier families: 4 / 6",18,700,"middle",ORANGE),t(310,320,"dose-monotone families: 5 / 6",18,700,"middle",GREEN),t(310,355,"median high-tier Δ risk: 0.6272",18,700,"middle",TEAL),t(310,390,"claim C — partial / family-specific",18,700,"middle",ORANGE)]
    p += [t(625,145,"B  V13 blinded physical generation",21,700),r(625,175,510,250,"#f7f2fb",PURPLE),t(880,215,"108 development + 72 held-out blocks",19,700,"middle"),t(880,250,"actual day × scene clusters",18,400,"middle"),t(880,285,"placebo + 3 non-cumulative interventions",18,400,"middle"),t(880,320,"prediction SHA committed before truth unseal",17,400,"middle"),t(880,355,"22-path execution digest frozen",17,400,"middle"),t(880,395,"RESULT PENDING",25,700,"middle",PURPLE)]
    p += [arrow(550,300,625,300,MUTED),t(600,485,"Transfer claim boundary",22,700,"middle"),r(120,515,960,105,"#fff4f4",RED),t(600,550,"V10: real texture + known perturbation truth",18,700,"middle"),t(600,580,"V13: physical intervention transfer after blinded held-out evaluation",18,700,"middle"),t(600,608,"Neither currently establishes natural pollinator-detection accuracy.",18,700,"middle",RED)]
    p += [t(600,690,"The physical-result panel must accept A/B/C/D without retuning.",18,700,"middle",INK)]
    write_svg("fig6_transfer_boundary.svg", p)
    write_csv("fig6_transfer_boundary.csv", ["generation","metric","value"], [["V10","positive_high_tier_families",4],["V10","dose_monotone_families",5],["V10","global_high_tier_median_risk_delta",0.62718017578125],["V10","allocation_cells_at_or_above_uniform","54/54"],["V13","scientific_result","PENDING"]])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
    print("MEE_CURRENT_FIGURES", len(list(OUT.glob("fig*.svg"))), "SVG")
    print(OUT)


if __name__ == "__main__":
    main()
