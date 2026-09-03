# Repository overview

## Current state

The active InsePi programme is the original physical observation-system development line, with **V13 as the current execution target**:

```text
V7   allocation validation                         FAIL / C
V8   conditional generality map                    retained
V9   protected probability-sample inference        retained
V10  real-pixel observation-process transfer       partial / C
V11  static contradiction localisation             FAIL / D
V12  controlled causal interventions               B
V13  blinded physical same-stream validation       RESULT PENDING
```

V14/V15 code and frozen results remain available as later side-line methodology/provenance, but they are not the current InsePi execution surface.

## Why V13 is the continuation point

V11 showed that static observer-state disagreement did not reliably identify the causal failure module under mechanism-subtype shift. V12 changed the experiment rather than retuning the failed classifier: it applied controlled interventions and measured paired observer responses. That recovered high conditional identifiability in simulation and reached claim B.

V13 is the physical boundary for that result. It asks whether the same causal diagnostic structure transfers to a real camera stream across new days and scenes under blinded held-out evaluation.

## V13 physical design

Independent unit:

`recording day × physical scene × latent treatment class × replicate`.

Frozen treatment classes:

- event-side failure;
- nuisance-side failure;
- shared optical failure;
- no fault.

Every block records placebo plus the complete three-intervention battery on the same stream. Active phases are non-cumulative and each is compared with the same restored placebo baseline.

Frozen scale:

- development: 108 blocks;
- held-out: 72 blocks on new days/scenes;
- total: 180 blocks;
- 4 phase clips per block;
- 720 clips total.

## Frozen V13 execution order

The authoritative sequence is:

1. private randomisation and commitment;
2. observer-safe capture/QC templates;
3. physical acquisition;
4. capture-log validation;
5. byte-complete field-bundle validation;
6. truth-free canonical pixel materialisation;
7. exact frozen PolliPi/InsePi smoke gates;
8. truth-free observer traces;
9. safe block-response table;
10. private truth split;
11. blinded held-out prediction using development labels only;
12. prediction commitment;
13. blinded protected QC;
14. held-out truth unseal and frozen evaluation.

Skipping ahead is a protocol failure. The prediction environment has no held-out-truth argument.

Normative files:

- `docs/V13_PHYSICAL_INTERVENTION_PROTOCOL.md`;
- `docs/V13_EXECUTION_ORDER.md`;
- `docs/V13_FIELD_RUN_CHECKLIST.md`;
- `benchmarks/v13_physical_intervention_protocol.json`;
- `benchmarks/v13_physical_apparatus_freeze.json`;
- `benchmarks/v13_observer_measurement_freeze.json`;
- `benchmarks/v13_execution_freeze.json`.

## Current software development

The restart branch adds `scripts/v13_pipeline_status.py`, a fail-closed operator aid that reports the next stage from workspace artifacts while never reading private truth contents.

Example:

```bash
python scripts/v13_pipeline_status.py --workspace /path/to/private/v13
```

It verifies ordering and the 720-clip cardinality boundary only. It does not change the frozen scientific protocol or replace any existing validator.

## Active CI

Generic pull requests run:

- `.github/workflows/test.yml`.

V13 also retains one manual-only preflight:

- `.github/workflows/v13-manual-preflight.yml`.

That preflight verifies the frozen execution digest and V13 contract tests and confirms that no V13 scientific result has yet been materialised.

## Historical side lines

The repository intentionally keeps later V14/V15 modules and results importable for reproducibility. They must not be confused with the active V13 physical causal-diagnostic programme simply because they are present on `main`.

No historical V7/V10/V11/V12 result is rewritten by the V13 continuation, and a failed V13 physical protocol must be retained as evidence rather than retuned under the same generation.

## Empirical next step

The next scientific work is **physical acquisition under the frozen V13 plan**, not another synthetic threshold search.

Before acquisition:

- run the V13 execution-digest preflight;
- generate the private 64-hex salt locally;
- build and preserve the randomisation commitment;
- create observer-safe capture/QC templates;
- keep private truth out of GitHub and the observer environment.

After acquisition, every frozen gate must pass in order before observer output is generated.

## Claim boundary

V13 validates a physical observation-system intervention pathway, not natural pollinator detection itself. Natural visitation accuracy, ecological prevalence, occupancy or species-level performance remain separate later validation questions.
