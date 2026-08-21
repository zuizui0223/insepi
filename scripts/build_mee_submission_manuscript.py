#!/usr/bin/env python3
"""Build a journal-compliant pre-V7 manuscript without changing scientific content.

This presentation layer converts the working manuscript to the current Methods in
Ecology and Evolution initial-submission structure:
- numbered 1--4 abstract;
- Data/Code for peer review statement immediately below the abstract;
- explicit AI-assistance disclosure in Methods;
- V7 outcome remains an unresolved placeholder until the locked ledger exists.
"""
from __future__ import annotations

import argparse
from pathlib import Path


ABSTRACT = """## Abstract

1. Autonomous ecological sensors can conserve storage, power and review effort by preferentially recording windows that appear biologically informative, but preferential acquisition also changes the distribution of observation conditions. We therefore distinguish biological-event evidence from observation-process reliability and ask how adaptive sensing can use both without losing non-preferential coverage.

2. We developed two deliberately non-equivalent observation programs in parallel: a biological-evidence observer (PolliPi) and an observability/error-risk observer (InsePi). They remained independently executable and were compared only after inference on shared latent and byte-identical visual simulations. An early equal-budget test showed that direct disagreement was not automatically beneficial, and a one-shot locked validation subsequently falsified the stronger hypothesis that a fixed scalar disagreement ranking would remain robust under event-prevalence shift, despite persistent complementary observer information.

3. We replaced scalar ranking with an exploration-guarded portfolio that reserves uniform sampling and assigns separate quotas to biological-evidence and observability-risk signals. High-resolution development froze a 50% exploration, 10% evidence, 40% observability-risk instance with zero direct disagreement quota. Across nine inspected prevalence-by-budget development regimes, its worst joint event/error-recovery ratio relative to uniform sampling was 1.00846, mean joint ratio 1.11642 and maximum disturbance-distribution total-variation distance 0.21919. For Q = αU + (1−α)R, the exploration guard also gives TV(Q,U)=(1−α)TV(R,U), Q(A)≥αU(A), and U(x)/Q(x)≤1/α. [[V7_LOCKED_RESULT]]

4. The resulting contribution is a simulation-first methodology for adaptive ecological sensing: preserve epistemically distinct observers, use contradiction to falsify acquisition assumptions rather than force consensus, retain guaranteed exploration in the final sampling design, and separate method development from locked validation. The study does not claim field accuracy; empirical deployment is external validation.

## Data/Code for peer review

All simulation code, tests, benchmark registries, pre-V7 figures and the manuscript build scripts are prepared as an anonymised peer-review bundle. The final V7 seed, pixels, traces and result are intentionally absent until the preregistered one-shot validation is legally unblocked by exact frozen-commit reachability. A formal public archive/DOI will be created only after the final locked result is preserved. An open-source software licence is required before submission and is tracked as an explicit packaging gate rather than selected automatically.

**Keywords:** adaptive sampling; ecological monitoring; preferential sampling; edge sensing; observability; falsification; active learning; simulation; reproducible methods
"""

AI_DISCLOSURE = """### 2.13. AI-assisted software and manuscript development

Generative AI systems were used as coding and writing assistants during portions of software development, testing, documentation and manuscript preparation. OpenAI ChatGPT (GPT-5.6 Sol) was used during the final V6/V7 infrastructure and manuscript-packaging phase. Repository commit metadata also records Anthropic Claude Opus 4.8 and Claude Sonnet 5 assistance in earlier software development. AI outputs were treated as proposed code or text rather than authoritative results: executable changes were subjected to repository tests and CI, simulation claims were tied to preserved ledgers and hashes, and the corresponding author assumes responsibility for the final code, analyses and manuscript text. AI systems were not treated as authors.
"""


def build(source: str) -> str:
    abstract_start = source.index("## Abstract")
    intro_start = source.index("---\n\n## 1. Introduction")
    rewritten = source[:abstract_start] + ABSTRACT + "\n---\n\n## 1. Introduction" + source[intro_start + len("---\n\n## 1. Introduction"):]

    results_marker = "\n---\n\n## 3. Results"
    if results_marker not in rewritten:
        raise ValueError("cannot locate Results boundary for AI disclosure")
    rewritten = rewritten.replace(results_marker, "\n\n" + AI_DISCLOSURE + results_marker, 1)
    return rewritten


def abstract_word_count(text: str) -> int:
    start = text.index("## Abstract")
    end = text.index("## Data/Code for peer review")
    block = text[start:end]
    words = [token for token in block.replace("## Abstract", "").split() if token != "[[V7_LOCKED_RESULT]]"]
    return len(words)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="manuscript/METHODS_PAPER_DRAFT.md")
    parser.add_argument("--output", default="manuscript/generated/MEE_PRE_V7_SUBMISSION.md")
    args = parser.parse_args()

    source = Path(args.source).read_text(encoding="utf-8")
    output = build(source)
    count = abstract_word_count(output)
    if count > 350:
        raise SystemExit(f"MEE abstract exceeds 350 words before V7 insertion: {count}")
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output, encoding="utf-8")
    print(f"MEE_PRE_V7_ABSTRACT_WORDS {count}")
    print(path)


if __name__ == "__main__":
    main()
