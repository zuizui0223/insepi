#!/usr/bin/env python3
"""Build a journal-compliant, double-anonymous pre-V7 manuscript.

This presentation layer converts the working manuscript to the current Methods in
Ecology and Evolution initial-submission structure while preserving the scientific
content and the locked V7 boundary.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re


ABSTRACT = """## Abstract

1. Autonomous ecological sensors can conserve storage, power and review effort by preferentially recording windows that appear biologically informative, but preferential acquisition also changes the distribution of observation conditions. We therefore distinguish biological-event evidence from observation-process reliability and ask how adaptive sensing can use both without losing non-preferential coverage.

2. We developed two deliberately non-equivalent observation programs in parallel: a biological-evidence observer (Observer-E) and an observability/error-risk observer (Observer-O). They remained independently executable and were compared only after inference on shared latent and byte-identical visual simulations. An early equal-budget test showed that direct disagreement was not automatically beneficial, and a one-shot locked validation subsequently falsified the stronger hypothesis that a fixed scalar disagreement ranking would remain robust under event-prevalence shift, despite persistent complementary observer information.

3. We replaced scalar ranking with an exploration-guarded portfolio that reserves uniform sampling and assigns separate quotas to biological-evidence and observability-risk signals. High-resolution development froze a 50% exploration, 10% evidence, 40% observability-risk instance with zero direct disagreement quota. Across nine inspected prevalence-by-budget development regimes, its worst joint event/error-recovery ratio relative to uniform sampling was 1.00846, mean joint ratio 1.11642 and maximum disturbance-distribution total-variation distance 0.21919. For Q = αU + (1−α)R, the exploration guard also gives TV(Q,U)=(1−α)TV(R,U), Q(A)≥αU(A), and U(x)/Q(x)≤1/α. [[V7_LOCKED_RESULT]]

4. The resulting contribution is a simulation-first methodology for adaptive ecological sensing: preserve epistemically distinct observers, use contradiction to falsify acquisition assumptions rather than force consensus, retain guaranteed exploration in the final sampling design, and separate method development from locked validation. The study does not claim field accuracy; empirical deployment is external validation.

## Data/Code for peer review

All simulation code, tests, benchmark registries, pre-V7 figures and manuscript build scripts are prepared as an anonymised peer-review bundle. The final V7 seed, pixels, traces and result are intentionally absent until the preregistered one-shot validation is reproducibly unblocked by exact frozen-commit reachability. A formal public archive/DOI will be created only after the final locked result is preserved. An open-source software licence is required before submission and is tracked as an explicit packaging gate rather than selected automatically.

**Keywords:** adaptive sampling; ecological monitoring; preferential sampling; edge sensing; observability; falsification; active learning; simulation; reproducible methods
"""

AI_DISCLOSURE = """### 2.13. AI-assisted software and manuscript development

Generative AI systems were used as coding and writing assistants during portions of software development, testing, documentation and manuscript preparation. OpenAI ChatGPT (GPT-5.6 Sol) was used during the final V6/V7 infrastructure and manuscript-packaging phase. Repository commit metadata also records Anthropic Claude Opus 4.8 and Claude Sonnet 5 assistance in earlier software development. AI outputs were treated as proposed code or text rather than authoritative results: executable changes were subjected to repository tests and CI, simulation claims were tied to preserved ledgers and hashes, and the corresponding author assumes responsibility for the final code, analyses and manuscript text. AI systems were not treated as authors.
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
V7_CONTEXT_MARKERS = (
    "[[V7_LOCKED_RESULT:ABSTRACT]]",
    "[[V7_LOCKED_RESULT:TABLE]]",
    "[[V7_LOCKED_RESULT:RESULTS]]",
    "[[V7_LOCKED_RESULT:DISCUSSION]]",
)


def anonymous_commit_id(original: str) -> str:
    digest = hashlib.sha256(("mee-double-anonymous|" + original.lower()).encode("utf-8")).hexdigest()[:10]
    return f"[anonymous-commit-{digest}]"


def anonymise_review_text(text: str) -> str:
    # Observer project names are unique enough to reveal the public repositories,
    # so the review manuscript uses role labels. Public names are restored only
    # after double-anonymous review.
    text = text.replace("PolliPi", "Observer-E")
    text = text.replace("InsePi", "Observer-O")
    text = GIT_SHA_RE.sub(lambda match: anonymous_commit_id(match.group(0)), text)
    return text


def specialise_v7_placeholders(text: str) -> str:
    """Assign each generic V7 placeholder a fixed manuscript role before V7 exists."""

    generic = "[[V7_LOCKED_RESULT]]"
    if text.count(generic) != len(V7_CONTEXT_MARKERS):
        raise ValueError(
            f"expected {len(V7_CONTEXT_MARKERS)} generic V7 placeholders, found {text.count(generic)}"
        )
    for marker in V7_CONTEXT_MARKERS:
        text = text.replace(generic, marker, 1)
    return text


def strip_internal_header(source_prefix: str) -> str:
    title = source_prefix.splitlines()[0].strip()
    if not title.startswith("# "):
        raise ValueError("working manuscript must start with a Markdown title")
    return title + "\n\n"


def add_verified_citation_context(text: str) -> str:
    state_sentence = "These constraints create a strong incentive to allocate observation effort adaptively."
    state_addition = (
        state_sentence
        + " The broader distinction between biological state and observation process is familiar from imperfect-detection ecology: a non-detection cannot be equated with biological absence unless detection is certain (MacKenzie et al., 2002)."
    )
    if state_sentence not in text:
        raise ValueError("cannot locate observation-process citation anchor")
    text = text.replace(state_sentence, state_addition, 1)

    adaptive_sentence = (
        "Recent work on adaptive ecological sampling similarly emphasises that targeted data collection can make raw samples non-representative unless the changing design is accounted for (Henrys, Mondain-Monval & Jarvis, 2024)."
    )
    adaptive_addition = (
        adaptive_sentence
        + " Simulation work also demonstrates that preferential sampling can bias ecological status estimates, with the magnitude depending on the association between inclusion and the variable of interest and on sampling effort (Aubry, Francesiaz & Guillemain, 2024)."
    )
    if adaptive_sentence not in text:
        raise ValueError("cannot locate preferential-sampling citation anchor")
    text = text.replace(adaptive_sentence, adaptive_addition, 1)

    generation_sentence = "No result from V5 was used to retune the same scalar disagreement score. Instead, its failure triggered a change in policy class."
    generation_addition = (
        generation_sentence
        + " More generally, simulation studies permit direct method evaluation because the data-generating truth is known (Morris, White & Crowther, 2019), while adaptive reuse of held-out evidence can compromise naïve validation if the analysis itself changes after inspection (Dwork et al., 2015). These considerations motivated a new untouched validation generation rather than continued reuse of V4 or V5 as final evidence."
    )
    if generation_sentence not in text:
        raise ValueError("cannot locate simulation-validation citation anchor")
    return text.replace(generation_sentence, generation_addition, 1)


def replace_working_references(text: str) -> str:
    marker = "## References (working citations)"
    if marker not in text:
        raise ValueError("cannot locate working reference section")
    return text.split(marker, 1)[0].rstrip() + "\n\n" + REFERENCES


def build(source: str) -> str:
    abstract_start = source.index("## Abstract")
    intro_start = source.index("---\n\n## 1. Introduction")
    prefix = strip_internal_header(source[:abstract_start])
    rewritten = prefix + ABSTRACT + "\n---\n\n## 1. Introduction" + source[intro_start + len("---\n\n## 1. Introduction"):]
    rewritten = add_verified_citation_context(rewritten)
    rewritten = replace_working_references(rewritten)

    results_marker = "\n---\n\n## 3. Results"
    if results_marker not in rewritten:
        raise ValueError("cannot locate Results boundary for AI disclosure")
    rewritten = rewritten.replace(results_marker, "\n\n" + AI_DISCLOSURE + results_marker, 1)
    rewritten = specialise_v7_placeholders(rewritten)
    return anonymise_review_text(rewritten)


def abstract_word_count(text: str) -> int:
    start = text.index("## Abstract")
    end = text.index("## Data/Code for peer review")
    block = text[start:end]
    words = [token for token in block.replace("## Abstract", "").split() if not token.startswith("[[V7_LOCKED_RESULT")]
    return len(words)


def total_word_count(text: str) -> int:
    return len(text.split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="manuscript/METHODS_PAPER_DRAFT.md")
    parser.add_argument("--output", default="manuscript/generated/MEE_PRE_V7_SUBMISSION.md")
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8")
    output = build(source)
    abstract_count = abstract_word_count(output)
    total_count = total_word_count(output)
    if abstract_count > 350:
        raise SystemExit(f"MEE abstract exceeds 350 words before V7 insertion: {abstract_count}")
    if total_count > 7600:
        raise SystemExit(f"pre-V7 manuscript leaves insufficient room under MEE 8000-word ceiling: {total_count}")
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(f"MEE_PRE_V7_ABSTRACT_WORDS {abstract_count}")
    print(f"MEE_PRE_V7_TOTAL_WORDS {total_count}")
    print(path)


if __name__ == "__main__":
    main()
