# V8 byte-determinism correction

## Scope

This note records a reproducibility correction made **after the first V8 scientific result was inspected**. It does not redefine V8, change the frozen V6 weights, alter the factorial grid, add/remove comparators, modify seeds, change metrics/estimators, or change any reported scientific conclusion.

## What was observed

The first pre-registered run (`32546131520`) and a later automatic rerun produced identical headline and regime-level scientific values, including:

- 864 regimes;
- frozen V6 >= uniform in 794 regimes;
- frozen V6 >= all same-alpha comparators in 185 regimes;
- mean V6 joint ratio `1.4878501258460761`;
- mean delta to best same-alpha `-0.4179469403999378`;
- naive prevalence RMSE `0.05581013542599007`;
- exploration-only prevalence RMSE `0.03940601781923415`.

However, the exact JSON SHA differed:

- first result SHA: `09b670fb7efa01681578791cc02ca30c9807d9cb7fa80bba3951a1fc6529f4ce`;
- later rerun SHA before correction: `2e1e60501388b462704ab8d3e248bbb313bac268fbaa63ee22adfee1e20bc16d`.

## Cause

`_family_tv()` accumulated four disturbance-family terms by iterating a Python `set`. Python hash randomization can alter set iteration order across processes. Floating-point addition is not strictly associative, so only the least-significant numerical bits could differ even when all scientifically meaningful values were unchanged.

## Correction

Commit `399dab96f0a966eda69eed209100e14cd37e340d` sorts family labels before TV summation. This changes only accumulation order.

A regression test then executes a mini-V8 under distinct `PYTHONHASHSEED` values. The full V8 CI was strengthened further to execute all 864 regimes twice, under:

- `PYTHONHASHSEED=1`;
- `PYTHONHASHSEED=987654`.

The gate requires exact equality of:

- result JSON SHA-256;
- regime-policy CSV SHA-256;
- applicability CSV SHA-256;
- quality/correlation-slice CSV SHA-256.

## Canonical deterministic result

Workflow run `32546799719` passed the full byte-identical rerun gate.

Both complete executions produced:

`5a6a828c5a48b8b1d73a466c4f933f5934dc7d9dc4c178d5867564720dbdeefe`

as the result JSON SHA-256.

Canonical artifact ZIP SHA-256:

`d31d1e8b78018ecb5e2c517f2af8f854066b09c397954cb11addeaecac3d5587`

The CI printed `V8_BYTE_IDENTICAL_RERUN true` and all V8 contract/determinism tests passed (`10 passed`).

## Scientific interpretation

The canonical deterministic run reproduces the first-run scientific values. Therefore the first run remains the timestamped pre-registered scientific observation, while the canonical deterministic artifact is the preferred byte-reproducible evidence package for archiving and downstream figure/manuscript generation.
