# Methods in Ecology and Evolution packaging gate

This file tracks **submission-format and peer-review packaging** only. Scientific pass/fail is controlled separately by the locked V7 protocol and claim ceiling.

## Current state

| Requirement | Status | Evidence / action |
|---|---|---|
| Standard Article framing | PASS | Simulation-first new method, not workflow glue |
| Main manuscript anonymised | PASS by build | `scripts/build_mee_submission_manuscript.py` + anonymous bundle sanitiser |
| Abstract numbered 1–4 | PASS by build | CI checks exactly four numbered paragraphs |
| Abstract target ≤350 words | PASS by build | builder fails if pre-V7 abstract exceeds 350 words |
| Data/Code for peer review statement | PASS by build | inserted directly below Abstract |
| Keywords | PASS | retained below Data/Code statement |
| Separate title page | PASS template | `manuscript/TITLE_PAGE_TEMPLATE.md`; excluded from anonymous bundle |
| AI assistance disclosure | PASS draft | Methods disclosure names ChatGPT GPT-5.6 Sol and repository-recorded Claude assistance; corresponding author responsibility stated |
| Anonymous peer-review code bundle | PASS by build | deterministic ZIP; owner/email/GitHub identifiers and searchable 40-char git SHAs scrubbed |
| Pre-V7 figures | PASS | deterministic Fig. 1–5 SVG/CSV package; V7 absent |
| V7 final result | BLOCKED | exact frozen V5 observer branches not yet publicly reachable |
| Open-source software licence | **BLOCKED — explicit author choice required** | repository currently has no root `LICENSE`, `LICENSE.txt`, `LICENSE.md` or `COPYING` |
| Stable public archive / DOI | PENDING after V7 | create immutable archive after locked result is preserved |
| Final Data Availability statement | PENDING archive DOI | title page and final manuscript updated after archiving |

## Why the licence remains blocked

Methods in Ecology and Evolution requires code accompanying submissions to carry an open-source software licence. Choosing MIT, BSD-3-Clause, GPL or another licence changes the legal permissions granted by the copyright holder, so the build system deliberately **does not choose one automatically**. Until an explicit licence is added at repository root, the anonymous bundle is labelled `license_ready=false` and must not be treated as submission-ready code.

## Double-anonymous handling

The review bundle intentionally removes repository ownership, email addresses and public git commit identifiers. Scientific SHA-256 fingerprints for simulated worlds, registries and reports remain unchanged because they identify evidence, not authors. The final public archive should restore canonical source provenance after peer review.

## V7 boundary

No packaging task may insert, infer or simulate a V7 outcome. `[[V7_LOCKED_RESULT]]` remains unresolved until the one-shot execution ledger exists. Packaging CI may build manuscripts and figures from V1–V6 evidence, but it must not generate V7 seed, pixels, traces or reports.
