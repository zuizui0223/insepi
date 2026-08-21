# V7 manuscript-finalization contract — fixed before result inspection

This document freezes how the locked V7 ledger is converted into reviewer-facing manuscript text, Supplementary Information and Main Figure 6. It is a presentation contract only: it cannot recompute the V7 scientific gate, modify the method, choose a new seed or reinterpret a claim level.

## Inputs

The finalizer accepts only:

1. the immutable `pollipi-insepi-v7-execution-ledger-v1` file;
2. the corresponding `pollipi-insepi-v7-report-v1` file;
3. the already-built double-anonymous pre-V7 manuscript;
4. the pre-V7 Supplementary Information.

Before filling any result text it verifies:

- report file SHA-256 equals `ledger.report_sha256`;
- report/ledger claim levels agree;
- report/ledger scientific gate status and failed-rule lists agree;
- claim A occurs only with a passing gate and no non-A level occurs with a passing gate;
- V6 robustness summaries agree;
- world, pixel, observer-trace, source, allocator, generator, world-spec and baseline-registry provenance agree;
- all nine prevalence × budget regimes exist for both uniform and frozen V6 metrics.

Any mismatch aborts finalization.

## Context-specific placeholders

Before V7 the generated manuscript contains exactly one of each:

- `[[V7_LOCKED_RESULT:ABSTRACT]]`
- `[[V7_LOCKED_RESULT:TABLE]]`
- `[[V7_LOCKED_RESULT:RESULTS]]`
- `[[V7_LOCKED_RESULT:DISCUSSION]]`
- `[[V7_LOCKED_RESULT:REPRODUCIBILITY_LEDGER]]`

The SI contains:

- `[[V7_LOCKED_RESULT:STATUS]]`
- `[[V7_LOCKED_RESULT:SUPPLEMENTARY]]`

No generic result paragraph is reused across contexts.

## Claim-level wording ceiling

### A — strong standalone simulation allocation claim

Abstract language states that all preregistered hard rules passed and reports worst joint ratio, mean joint ratio and maximum TV. Discussion may state that the frozen exploration-guarded portfolio survived the new locked prevalence/budget challenge. It must still say this is simulation evidence, not field validation.

### B — conditional allocation claim

Abstract language states that the full robustness gate failed and the allocation benefit is conditional rather than generally prevalence/budget robust. Discussion may retain average benefit or sampling-control language only where supported by the ledger.

### C — bias-control / exploration claim

Abstract language states that general recovery advantage was not established. Discussion centres the analytical and empirical sampling-bias-control role of guaranteed exploration; targeted observer weights remain task dependent.

### D — contradiction-guided development claim

Abstract language states that a superior-allocation claim for the full dual-observer portfolio was rejected. Discussion recentres on contradiction-guided development, failure localisation and diagnostic observer diversity.

### E — benchmark/falsification only

No performance or best-programming claim is retained. The manuscript may report only the preserved benchmark/falsification and reproducibility lessons.

These mappings are implemented in `scripts/finalize_submission_from_v7.py` and tested using synthetic ledgers only.

## Results insertion

The Results paragraph always reports:

- mechanically assigned claim level;
- locked PASS/FAIL;
- worst joint ratio;
- mean joint ratio;
- maximum TV;
- the complete failed-rule list;
- an explicit statement that V6 weights, thresholds, baselines and the V7 seed were not changed after inspection.

## Reproducibility insertion

Reviewer-facing text records scientific SHA-256 evidence directly but pseudonymises 40-character source commits consistently. It includes:

- world fingerprint;
- pixel SHA-256;
- Observer-E and Observer-O trace SHA-256;
- final report SHA-256;
- anonymous source identifiers for both observers, allocator and generator.

Canonical public provenance is restored only in the post-review archive.

## Supplementary Information

The finalizer inserts:

1. the locked gate summary;
2. a complete table of every policy × prevalence × budget metric from the V7 report;
3. the immutable provenance block.

No V7 value is typed manually into SI.

## Main Figure 6

Figure 6 layout is fixed before V7:

- three panels for prevalence 0.10, 0.50 and 0.90;
- x-axis: 10%, 25% and 50% budget;
- blue circles: frozen-V6 event-recall ratio to uniform;
- red squares: frozen-V6 observer-relative hidden-error ratio to uniform;
- reference lines at ratio 1.00 and locked floor 0.98;
- each regime displays frozen-V6 disturbance TV;
- footer reports locked PASS/FAIL, claim level, worst joint ratio, mean joint ratio and maximum TV.

A CSV with the nine regime ratios and TV values is generated alongside the SVG. The layout cannot be altered after result inspection under the same V7 generation except for non-semantic accessibility fixes that leave data, scales and annotations unchanged.

## Finalization receipt

Finalization writes a receipt containing:

- source ledger SHA-256;
- source report SHA-256;
- locked report SHA-256;
- claim level and gate status;
- SHA-256 for final manuscript, final SI, Figure 6 SVG and Figure 6 CSV;
- a canonical receipt SHA-256.

This receipt separates a deterministic publication transform from the upstream scientific execution.
