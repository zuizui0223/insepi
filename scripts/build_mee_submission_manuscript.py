#!/usr/bin/env python3
"""Build the current double-anonymous MEE reviewer manuscript.

This is a presentation layer only. It preserves the current scientific narrative
and locked V7/V10/V11/V12 outcomes, inserts journal-facing peer-review and AI-use
statements, replaces the working bibliography with the audited bibliography, and
anonymises repository-identifying observer names and 40-character Git commits.

It must not recreate the obsolete pre-V7 placeholder manuscript.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re


DATA_CODE = """## Data/Code for peer review

An anonymised review bundle contains the simulation and diagnostic code, tests, benchmark registries, locked-result provenance needed to audit the completed V7, V10, V11 and V12 generations, and the frozen pre-field V13 protocol. V13 physical data do not yet exist and no V13 performance result is represented in this manuscript. A formal public archive/DOI will be created for the accepted evidence package. An explicit open-source software licence remains a submission gate and is not selected automatically by the build system.
"""

AI_DISCLOSURE = """### 2.15. AI-assisted software and manuscript development

Generative AI systems were used as coding and writing assistants during portions of software development, testing, documentation and manuscript preparation. OpenAI ChatGPT (GPT-5.6 Sol) was used during V6–V13 infrastructure, validation, reproducibility and manuscript-packaging work. Repository commit metadata also records Anthropic Claude Opus 4.8 and Claude Sonnet 5 assistance in earlier software development. AI outputs were treated as proposed code or text rather than authoritative results: executable changes were subjected to repository tests and CI, scientific claims were tied to preserved protocols, ledgers, result hashes and claim ceilings, and the corresponding author assumes responsibility for the final code, analyses and manuscript text. AI systems were not treated as authors.
"""

REFERENCES = """## References

Aubry, P., Francesiaz, C. & Guillemain, M. (2024). On the impact of preferential sampling on ecological status and trend assessment. *Ecological Modelling*, 492, 110707. https://doi.org/10.1016/j.ecolmodel.2024.110707

Avizienis, A. (1985). The N-version approach to fault-tolerant software. *IEEE Transactions on Software Engineering*, SE-11(12), 1491–1501. https://doi.org/10.1109/TSE.1985.231893

Bothmann, L., Wimmer, L., Charrakh, O., Weber, T., Edelhoff, H., Peters, W., Nguyen, H., Benjamin, C. & Menzel, A. (2023). Automated wildlife image classification: An active learning tool for ecological applications. *Ecological Informatics*, 77, 102231. https://doi.org/10.1016/j.ecoinf.2023.102231

Conn, P.B., Thorson, J.T. & Johnson, D.S. (2017). Confronting preferential sampling when analysing population distributions: diagnosis and model-based triage. *Methods in Ecology and Evolution*, 8(11), 1535–1546. https://doi.org/10.1111/2041-210X.12803

Diggle, P.J., Menezes, R. & Su, T.-l. (2010). Geostatistical inference under preferential sampling. *Journal of the Royal Statistical Society: Series C (Applied Statistics)*, 59(2), 191–232. https://doi.org/10.1111/j.1467-9876.2009.00701.x

Dwork, C., Feldman, V., Hardt, M., Pitassi, T., Reingold, O. & Roth, A. (2015). The reusable holdout: Preserving validity in adaptive data analysis. *Science*, 349(6248), 636–638. https://doi.org/10.1126/science.aaa9375

Henrys, P.A., Mondain-Monval, T.O. & Jarvis, S.G. (2024). Adaptive sampling in ecology: Key challenges and future opportunities. *Methods in Ecology and Evolution*, 15(9), 1483–1496. https://doi.org/10.1111/2041-210X.14393

MacKenzie, D.I., Nichols, J.D., Lachman, G.B., Droege, S., Royle, J.A. & Langtimm, C.A. (2002). Estimating site occupancy rates when detection probabilities are less than one. *Ecology*, 83(8), 2248–2255. https://doi.org/10.1890/0012-9658(2002)083[2248:ESORWD]2.0.CO;2

McKeeman, W.M. (1998). Differential testing for software. *Digital Technical Journal*, 10(1), 100–107.

Morris, T.P., White, I.R. & Crowther, M.J. (2019). Using simulation studies to evaluate statistical methods. *Statistics in Medicine*, 38(11), 2074–2102. https://doi.org/10.1002/sim.8086

Seung, H.S., Opper, M. & Sompolinsky, H. (1992). Query by committee. In *Proceedings of the Fifth Annual Workshop on Computational Learning Theory*, 287–294. ACM. https://doi.org/10.1145/130385.130417
"""

GIT_SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])")


def anonymous_commit_id(original: str) -> str:
    digest = hashlib.sha256(("mee-double-anonymous|" + original.lower()).encode("utf-8")).hexdigest()[:10]
    return f"[anonymous-commit-{digest}]"


def anonymise_review_text(text: str) -> str:
    text = text.replace("PolliPi", "Observer-E")
    text = text.replace("InsePi", "Observer-O")
    text = GIT_SHA_RE.sub(lambda match: anonymous_commit_id(match.group(0)), text)
    return text


def strip_internal_metadata(source: str) -> str:
    lines = source.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("working manuscript must start with a Markdown title")
    abstract_start = source.index("## Abstract")
    return lines[0].rstrip() + "\n\n" + source[abstract_start:]


def insert_peer_review_statement(text: str) -> str:
    if "## Data/Code for peer review" in text:
        raise ValueError("working manuscript unexpectedly already contains reviewer Data/Code statement")
    keyword_marker = "**Keywords:**"
    if keyword_marker not in text:
        raise ValueError("cannot locate keyword line after abstract")
    return text.replace(keyword_marker, DATA_CODE.rstrip() + "\n\n" + keyword_marker, 1)


def add_verified_citation_context(text: str) -> str:
    anchors = [
        (
            "Autonomous ecological sensors observe biological processes through an observation process.",
            "Autonomous ecological sensors observe biological processes through an observation process. The distinction between biological state and observation is familiar from imperfect-detection ecology: non-detection cannot be equated with biological absence when detection is uncertain (MacKenzie et al., 2002).",
        ),
        (
            "Preferential sampling is already known to bias ecological inference when the observation process depends on the system or conditions under study (Diggle, Menezes & Su, 2010; Conn, Thorson & Johnson, 2017), and adaptive ecological sampling raises related challenges for representativeness and downstream inference (Henrys, Mondain-Monval & Jarvis, 2024).",
            "Preferential sampling is already known to bias ecological inference when the observation process depends on the system or conditions under study (Diggle, Menezes & Su, 2010; Conn, Thorson & Johnson, 2017), and adaptive ecological sampling raises related challenges for representativeness and downstream inference (Henrys, Mondain-Monval & Jarvis, 2024). Simulation studies likewise show that preferential inclusion can bias ecological status estimates, with the magnitude depending on the association between inclusion and the variable of interest and on sampling effort (Aubry, Francesiaz & Guillemain, 2024).",
        ),
        (
            "Locked failure reduced the claim ceiling but did not trigger tuning under the same generation.",
            "Locked failure reduced the claim ceiling but did not trigger tuning under the same generation. Simulation studies are particularly useful for method evaluation because the data-generating truth is known (Morris, White & Crowther, 2019), while repeated adaptation to held-out evidence can compromise naïve validation if the analysis changes after inspection (Dwork et al., 2015).",
        ),
        (
            "Likewise, the method is not a new disagreement-based active learner.",
            "Likewise, the method is not a new disagreement-based active learner. Active-learning workflows have already been developed for ecological image classification (Bothmann et al., 2023); our protected random component and non-equivalent observer objectives address a different sampling-design problem.",
        ),
    ]
    for old, new in anchors:
        if old not in text:
            raise ValueError(f"cannot locate verified-citation anchor: {old[:72]}")
        text = text.replace(old, new, 1)
    return text


def insert_ai_disclosure(text: str) -> str:
    if "AI-assisted software and manuscript development" in text:
        raise ValueError("working manuscript unexpectedly already contains AI disclosure")
    results_marker = "\n---\n\n## 3. Results"
    if results_marker not in text:
        raise ValueError("cannot locate Results boundary for AI disclosure")
    return text.replace(results_marker, "\n\n" + AI_DISCLOSURE.rstrip() + results_marker, 1)


def replace_working_references(text: str) -> str:
    marker = "## References (working citations)"
    if marker not in text:
        raise ValueError("cannot locate working reference section")
    return text.split(marker, 1)[0].rstrip() + "\n\n" + REFERENCES


def build(source: str) -> str:
    rewritten = strip_internal_metadata(source)
    rewritten = insert_peer_review_statement(rewritten)
    rewritten = add_verified_citation_context(rewritten)
    rewritten = insert_ai_disclosure(rewritten)
    rewritten = replace_working_references(rewritten)
    if "[[V7_LOCKED_RESULT" in rewritten:
        raise ValueError("obsolete V7 publication placeholder remains in current manuscript")
    return anonymise_review_text(rewritten)


def abstract_word_count(text: str) -> int:
    start = text.index("## Abstract")
    end = text.index("## Data/Code for peer review")
    block = text[start:end].replace("## Abstract", "")
    return len(block.split())


def total_word_count(text: str) -> int:
    return len(text.split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="manuscript/METHODS_PAPER_DRAFT.md")
    parser.add_argument("--output", default="manuscript/generated/MEE_CURRENT_SUBMISSION.md")
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8")
    output = build(source)
    abstract_count = abstract_word_count(output)
    total_count = total_word_count(output)
    if abstract_count > 350:
        raise SystemExit(f"MEE abstract exceeds 350 words: {abstract_count}")
    if total_count > 8000:
        raise SystemExit(f"MEE manuscript exceeds 8000-word ceiling: {total_count}")
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(f"MEE_CURRENT_ABSTRACT_WORDS {abstract_count}")
    print(f"MEE_CURRENT_TOTAL_WORDS {total_count}")
    print(path)


if __name__ == "__main__":
    main()
