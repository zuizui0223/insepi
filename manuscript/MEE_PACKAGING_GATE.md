# Methods in Ecology and Evolution packaging gate

This file tracks submission-format and peer-review packaging. Scientific pass/fail remains controlled by the frozen generation-specific protocols and claim ceilings.

## Current state

| Requirement | Status | Evidence / action |
|---|---|---|
| Standard Article framing | PASS | Methodology paper centred on contradiction-guided development, controlled diagnosis and protected probability sampling |
| Current main manuscript | PASS working draft | V7/V10/V11/V12 locked outcomes represented; V13 explicitly result-pending |
| Main manuscript anonymisation | PASS by current build contract | Observer-E / Observer-O labels; owner/project names and searchable 40-char Git commits removed |
| Abstract numbered 1–4 | PASS by build contract | exactly four source-derived numbered paragraphs retained |
| Abstract target ≤350 words | PASS/FAIL determined by current builder | builder refuses output above 350 words |
| Main manuscript ≤8,000 words | PASS/FAIL determined by current builder | builder refuses output above 8,000 words |
| Data/Code for peer review statement | PASS by build | inserted directly below abstract before keywords |
| Separate title page | PASS template | `manuscript/TITLE_PAGE_TEMPLATE.md`; excluded from anonymous bundle |
| AI assistance disclosure | PASS draft | Methods disclosure names ChatGPT GPT-5.6 Sol and repository-recorded Claude assistance; author responsibility stated |
| Current anonymous peer-review code bundle | PASS by build contract; CI required | based on V13 scientific tree, includes completed V7/V10/V11/V12 evidence and frozen V13 protocol |
| Core bibliography metadata | PASS | 11-entry `REFERENCES_VERIFIED.bib`; publisher/institutional metadata audit retained |
| Observation/simulation validation citations | PASS current builder | MacKenzie 2002, Morris 2019, Dwork 2015, Aubry 2024 and Bothmann 2023 inserted with bounded roles |
| Current Supplementary Information | PASS draft | `SUPPLEMENTARY_INFORMATION_CURRENT.md` covers V1–V13 and contains no V7 placeholders |
| Current main figures | **IN PROGRESS** | old pre-V7 Fig. 1–5 are historical only; regenerate figures for falsification / V9 / V11→V12 / V10–V13 story |
| V7 locked result | PASS evidence | FAIL/C preserved; report SHA `20ff5ecc...` |
| V10 locked real-pixel result | PASS evidence | partial transfer/C preserved; one-shot run `32693453262` |
| V11 locked result | PASS evidence | static localisation FAIL/D preserved |
| V12 locked result | PASS evidence | controlled intervention claim B preserved |
| V13 physical result | **RESULT PENDING** | pre-field execution frozen; stronger physical-transfer MEE claim waits for blinded acquisition/evaluation |
| PolliPi open-source licence | **BLOCKED — explicit author choice required** | no explicit root licence recorded |
| InsePi open-source licence | **BLOCKED — explicit author choice required** | no explicit root licence recorded |
| Stable public archive / DOI | PENDING final claim set | create immutable archive after final submission evidence set is fixed |
| Final Data Availability statement | PENDING archive DOI | update after archive creation |

## Scientific evidence already closed

The package must preserve, not re-run or reinterpret, these outcomes:

- V7: general frozen-allocation superiority rejected, claim C;
- V10: partial/family-specific real-pixel observation-risk transfer, claim C;
- V11: static contradiction-state causal localisation rejected, claim D;
- V12: conditional causal-identification advantage under controlled interventions, claim B.

V13 is a separate pre-field generation. Its 22-path scientific execution digest is:

`96c44136f51d30060534b7157c9adc1c68a42883e401757db63193ebb7a8035d`.

Packaging work must not modify those 22 critical paths.

## Why the licence remains blocked

Methods in Ecology and Evolution requires accompanying code to carry an appropriate open-source software licence. The method depends on two separately executable observer repositories, so both repositories require explicit licensing before the public submission/archive package can be considered complete.

No prior repository-wide licence grant was identified that authorises the build system to choose terms automatically. Selecting MIT, BSD-3-Clause, Apache-2.0, GPL or another licence changes legal permissions granted by the copyright holder. The package therefore remains `license_ready=false` until the author explicitly chooses/authorises licences for both repositories.

## Double-anonymous handling

The current review bundle:

- starts from the V13 scientific tree rather than the obsolete pre-V7 tree;
- removes repository ownership, email addresses, public observer-project names and 40-character Git commit identifiers from content and paths;
- retains 64-character scientific SHA-256 evidence fingerprints;
- includes `MEE_CURRENT_SUBMISSION.md` and `SUPPLEMENTARY_INFORMATION_CURRENT.md`;
- excludes the title page and historical `SUPPLEMENTARY_INFORMATION_PRE_V7.md` / `V7_FINALIZATION_CONTRACT.md` from reviewer-facing content;
- declares completed locked generations V7/V10/V11/V12 and explicitly declares `v13_scientific_result_present=false`.

Canonical historical files remain in repository history for provenance.

## Bibliography boundary

`REFERENCES_VERIFIED.bib` remains the canonical audited bibliography source. New literature may clarify the method's position but may not retrospectively upgrade a locked negative result.

## V13 boundary

V13 may be described only as a frozen physical protocol until its no-peek sequence completes:

`private randomisation → physical capture → capture validation → truth-free pixels → exact observers → blinded predictions → prediction commitment → protected QC → held-out truth unseal → frozen evaluator`.

No packaging task may invent or simulate a V13 scientific outcome for the manuscript.

## Pre-submission blockers remaining

For the intended stronger MEE version, the remaining substantive blockers are:

1. execute V13 physical acquisition/evaluation exactly as frozen and accept its A/B/C/D outcome without retuning;
2. build the current V1–V13-aligned main figure set (the old pre-V7 figures are not the final figures);
3. explicitly choose and add compatible open-source licences to both observer repositories;
4. create the final stable archive/DOI after the claim set is fixed.

A conservative simulation-first manuscript can be packaged before V13, but it must retain the narrower claim ceiling and still requires the current figures and explicit licences before submission.