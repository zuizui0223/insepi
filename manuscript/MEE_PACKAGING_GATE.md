# Methods in Ecology and Evolution packaging gate

This file tracks **submission-format and peer-review packaging** only. Scientific pass/fail is controlled separately by the locked V7 protocol and claim ceiling.

## Current state

| Requirement | Status | Evidence / action |
|---|---|---|
| Standard Article framing | PASS | Simulation-first new method, not workflow glue |
| Main manuscript anonymised | PASS by build + unpack audit | role labels Observer-E / Observer-O; public project names, owner and searchable 40-char commit IDs absent |
| Abstract numbered 1–4 | PASS by build | CI checks exactly four numbered paragraphs |
| Abstract target ≤350 words | PASS | current pre-V7 abstract = **257 words** |
| Main manuscript word budget | PASS | current pre-V7 generated manuscript = **5,428 words**, leaving margin for locked V7 result under the journal ceiling |
| Data/Code for peer review statement | PASS by build | inserted directly below Abstract |
| Keywords | PASS | retained below Data/Code statement |
| Separate title page | PASS template | `manuscript/TITLE_PAGE_TEMPLATE.md`; excluded from anonymous bundle |
| AI assistance disclosure | PASS draft | Methods disclosure names ChatGPT GPT-5.6 Sol and repository-recorded Claude assistance; corresponding author responsibility stated |
| Anonymous peer-review code bundle | PASS by build + manual grep | deterministic ZIP; text and paths scrub owner/project names, email and searchable 40-char git SHAs; JSONL/BibTeX included in scan |
| Core bibliography metadata | PASS | 11-entry `REFERENCES_VERIFIED.bib`; publisher/institutional metadata audit; corrected Avizienis DOI and Aubry title |
| Observation/simulation validation citations | PASS | MacKenzie 2002, Morris 2019 and Dwork 2015 inserted with bounded citation roles |
| Supplementary Information | PASS pre-V7 | `SUPPLEMENTARY_INFORMATION_PRE_V7.md` contains V1–V6 tables, theorem derivation, hashes and seed-independent V7 preregistration; result fields remain placeholders |
| Pre-V7 figures | PASS | deterministic Fig. 1–5 SVG/CSV package; V7 absent |
| V7 final result | **BLOCKED** | exact frozen V5 observer branches not yet publicly reachable |
| Open-source software licence | **BLOCKED — explicit author choice required** | repository currently has no root `LICENSE`, `LICENSE.txt`, `LICENSE.md` or `COPYING` |
| Stable public archive / DOI | PENDING after V7 | create immutable archive after locked result is preserved |
| Final Data Availability statement | PENDING archive DOI | title page and final manuscript updated after archiving |

## Why the licence remains blocked

Methods in Ecology and Evolution requires code accompanying submissions to carry an open-source software licence. Choosing MIT, BSD-3-Clause, GPL or another licence changes the legal permissions granted by the copyright holder, so the build system deliberately **does not choose one automatically**. Until an explicit licence is added at repository root, the anonymous bundle is labelled `license_ready=false` and must not be treated as submission-ready code.

## Double-anonymous handling

The review bundle removes repository ownership, email addresses, public observer-project names and public git commit identifiers from both content and paths. Scientific SHA-256 fingerprints for simulated worlds, registries and reports remain unchanged because they identify evidence, not authors. The latest unpacked artifact was checked with a case-insensitive recursive text/path scan and produced zero project/owner leaks. The final public archive should restore canonical source provenance after peer review.

## Bibliography boundary

`REFERENCES_VERIFIED.bib` is now the canonical bibliography source. `REFERENCE_AUDIT.md` records corrections and limits on what each neighbouring literature can support. Literature added after V7 must not be used to retrospectively inflate a failing locked claim.

## V7 boundary

No packaging task may insert, infer or simulate a V7 outcome. `[[V7_LOCKED_RESULT]]` remains unresolved until the one-shot execution ledger exists. Packaging CI may build manuscripts, supplementary information and figures from V1–V6 evidence, but it must not generate V7 seed, pixels, traces or reports.

## Pre-submission blockers remaining

Only two blockers remain outside ordinary title-page completion:

1. make the exact frozen V5 observer commits externally reachable, then execute the already staged one-shot V7 workflow;
2. select and add an open-source software licence explicitly.

Neither blocker may be bypassed by publication-packaging code.
