# interaction-sensing / InsePi

## Active mainline

InsePi is again centred on the original observation-system development sequence:

```text
V7   frozen allocation validation                 FAIL / C
V10  locked real-pixel perturbation transfer      partial / C
V11  static contradiction localisation            FAIL / D
V12  controlled causal intervention diagnosis     B
V13  blinded same-stream physical validation      RESULT PENDING
```

**V13 is the active scientific mainline.** The immediate goal is to execute the already-frozen physical intervention experiment without retuning it, then accept the preregistered A/B/C/D outcome.

Later V14/V15 target–nuisance/observability work remains in the repository for provenance and as a separate experimental side line. It does not define the current InsePi execution path.

## Current scientific question

V12 showed in a synthetic setting that controlled interventions can make otherwise non-identifying observer failures causally distinguishable. V13 asks whether that diagnostic structure survives a physical camera system across **new recording days and new physical scenes**.

The physical treatment classes are:

- `event_side`;
- `nuisance_side`;
- `shared_optical`;
- `no_fault`.

Every independent block records the same-stream battery:

1. placebo;
2. `event_restore`;
3. `observability_restore`;
4. `shared_restore`;

with the three active phases in a private-salt randomised order and with baseline restoration between phases. Frames are repeated measurements, not replicates. The inferential unit is the physical block, and held-out uncertainty is clustered by actual `recording_date_local × physical_scene_code`.

## Frozen V13 scale

Development:

- 3 days × 3 scenes × 4 treatment classes × 3 replicates = **108 blocks**.

Held-out:

- 2 new days × 3 new scenes × 4 treatment classes × 3 replicates = **72 blocks**.

Total:

- **180 blocks**;
- 4 phase clips per block;
- **720 ten-second clips**.

The quantitative apparatus tolerances, measurement path, blinding rules, prediction commitment, QC gate and A/B/C/D evaluation contract are already frozen. See:

- `docs/V13_PHYSICAL_INTERVENTION_PROTOCOL.md`;
- `docs/V13_EXECUTION_ORDER.md`;
- `docs/V13_FIELD_RUN_CHECKLIST.md`;
- `benchmarks/v13_physical_intervention_protocol.json`;
- `benchmarks/v13_physical_apparatus_freeze.json`;
- `benchmarks/v13_observer_measurement_freeze.json`;
- `benchmarks/v13_execution_freeze.json`.

## Fail-closed execution surface

The repository already contains the complete no-peek path:

```text
private randomisation
→ capture templates
→ physical acquisition
→ capture-log validation
→ byte-level field bundle validation
→ truth-free canonical pixels
→ exact frozen PolliPi/InsePi smoke gates
→ truth-free observer traces
→ block response table
→ development labels only
→ blinded held-out predictions
→ prediction SHA commitment
→ protected QC
→ held-out truth unseal
→ frozen cluster-level evaluator
```

The active manual preflight is:

```text
.github/workflows/v13-manual-preflight.yml
```

Frozen historical scientific workflows remain under `provenance/frozen_github_workflows/` and are not rerun automatically.

## Pipeline status auditor

The V13 mainline restart adds a non-scientific convenience auditor that reports the next executable stage and blocks obvious order violations without reading private truth contents:

```bash
python scripts/v13_pipeline_status.py --workspace /path/to/private/v13
```

JSON output is available with `--json`.

The auditor only checks artifact presence and clip cardinality. It does **not** alter the V13 execution digest, infer treatment truth, validate scientific results, or replace any frozen gate.

## Exact observer boundary

V13 uses the exact frozen observer commits already specified by the protocol:

- PolliPi: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- InsePi: `980813bab996909020140fad5bd83b055eb3db9c`.

Observer execution receives canonical pixels/backgrounds only. Held-out treatment truth is unavailable to the prediction environment until predictions have been committed.

## Current next action

Before any physical acquisition, generate the private randomisation locally using a fresh 64-hex salt and preserve the commitment. **Do not place the salt or private truth ledger in GitHub, chat, observer logs, or manuscript materials.**

The authoritative command sequence is in `docs/V13_EXECUTION_ORDER.md`.

## Repository structure

- `src/interaction_sensing/` — current and historical observation, causal-diagnostic and evaluation code.
- `benchmarks/` — frozen protocols, result receipts and scientific contracts.
- `docs/` — V13 execution protocol plus historical development records.
- `scripts/` — reproducible generation, validation, observer and evaluation runners.
- `tests/` — unit tests and frozen scientific-contract tests.
- `provenance/frozen_github_workflows/` — byte-preserved historical generation workflows.
- `legacy/` — earlier prototypes and baselines retained for provenance.

## Quick start

```bash
python -m pip install -e ".[runtime,analysis,dev]"
pytest
python scripts/v13_pipeline_status.py --workspace /path/to/private/v13
```

## Claim boundary

V13 is a blinded physical **observation-system intervention** experiment. It is not natural pollinator detection validation and does not by itself establish field visitation accuracy, species accuracy, occupancy validity, ecological prevalence, or universal observer superiority. Those claims require separate biological field validation after the physical diagnostic boundary is resolved.
