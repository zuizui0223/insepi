# V13 physical same-stream intervention protocol

## Purpose

V12 established a synthetic **conditional** causal-identification result (claim B): controlled interventions made held-out failure classes highly identifiable, and separate E/O responses were most useful for diagnostic efficiency. V13 is the physical boundary.

The goal is not to obtain more frames. It is to test whether controlled physical manipulations produce reproducible paired observer-response signatures across **new days and scenes**, while preserving block-level replication and blinding.

The authoritative quantitative apparatus recipe is frozen before acquisition in `benchmarks/v13_physical_apparatus_freeze.json`. PolliPi/InsePi output may not be used to tune those physical treatment magnitudes.

## Experimental unit

A frame is not a replicate.

The independent experimental block is:

`day × scene × latent physical treatment class × replicate`.

Each block contains one placebo phase and the complete three-intervention diagnostic battery on the **same camera stream**. Frame-level outputs are summarised within phase and never resampled as independent observations.

## Frozen scale

### Development

- 3 days;
- 3 scenes per day;
- 4 latent treatment classes;
- 3 replicate blocks per day × scene × class;
- **108 blocks**.

### Held-out

- 2 different days;
- 3 scenes per day that do not appear in development;
- 4 treatment classes;
- 3 replicate blocks per day × scene × class;
- **72 blocks**.

Total: **180 physical blocks**.

With 4 recorded phases per block, the observer plan contains **720 phase clips**.

## Frozen apparatus geometry

Common geometry:

- rigid camera mount;
- camera-to-target plane = **1000 ± 20 mm**;
- standard event proxy = **100 ± 2 mm** matte high-contrast circular disk on a matte neutral carrier;
- target centre fixed within a block;
- background mechanically isolated from the target carrier.

Apparatus calibration is based on physical measurement or raw calibration imagery only. It must never use PolliPi/InsePi scores.

## Physical treatment classes

The treatment truth comes from the physical operator ledger, not from PolliPi/InsePi output.

### Event-side

Development subtype is fixed to **target-only contrast attenuation**. Target geometry remains 100 mm; target/carrier luminance contrast must be **0.20–0.30 ×** the standard-target contrast under the same illumination.

Held-out subtype is fixed to a **target scale shift**: a **50 ± 2 mm** high-contrast disk at the same target-plane centre.

The nuisance source is otherwise held fixed. `event_restore` replaces the current target with the standard 100-mm reference at the same location.

### Nuisance-side

Development subtype is fixed to **fan-driven background motion** at **1.5 ± 0.2 m/s** measured at the mechanically isolated background plane.

Held-out subtype is fixed to a **moving shadow** at **0.50 ± 0.05 Hz**, with shadow-trough illuminance **0.60 ± 0.10 ×** the unshadowed level.

The local standard event proxy is otherwise held fixed. `observability_restore` neutralises the nuisance source only.

### Shared optical

Development subtype is fixed to **partial optical occlusion**: a semi-opaque front-of-lens strip crossing target and surrounding scene, covering **0.30 ± 0.03** of canonical frame width.

Held-out subtype is fixed to a **full-aperture diffusion filter** with visible transmittance **0.70 ± 0.10**.

`shared_restore` replaces the impaired optical carrier with a matched clear carrier while target and nuisance state remain unchanged.

### No fault

Matched clean physical control:

- standard 100-mm event proxy;
- nuisance source off;
- matched clear optical carrier.

Active phases use matched sham handling: an identical standard target, nuisance-neutral handling, and an identical clear carrier.

These subtypes are now fixed rather than interchangeable examples. If one proves infeasible before acquisition, the scientific execution freeze must be revised before any V13 physical data are collected. After acquisition starts, replacement requires a new generation.

## Diagnostic phases

Every block records:

1. placebo — 10 s;
2. three active phases, each 10 s, in a salt-randomised order:
   - `event_restore`;
   - `observability_restore`;
   - `shared_restore`.

Use 5 s washout between phases. The first 2 s of each recorded phase are stabilisation and excluded from the block summary.

Active interventions are **non-cumulative**. During washout the operator restores the exact latent placebo treatment state. Every active phase is therefore a paired counterfactual against the same within-block placebo reference. If that state cannot be restored, abort the block rather than treating later phases as comparable.

Each observer channel is summarised by the **median output during the remaining within-phase interval**. The causal response is phase median minus placebo median.

All three active phases are physically collected for every block. The held-out primary analysis nevertheless reveals only the **two interventions selected by the frozen generic diagnostic algorithm**. The third response is used only for the secondary full-battery ceiling.

This prevents the acquisition operator from changing which physical experiment is performed after seeing algorithm output.

## Blind randomisation

Run locally before field acquisition:

```bash
python scripts/v13_build_randomisation.py \
  --salt <PRIVATE_64_HEX_SALT> \
  --output-dir <PRIVATE_V13_PLAN_DIR>
```

The salt must never enter the observer environment or repository.

The generator creates:

- `v13_private_truth_ledger.csv` — private operator truth;
- `v13_observer_plan.csv` — safe observer-facing plan;
- `v13_protected_qc_plan.csv` — opaque block IDs plus independent QC assignment;
- `v13_randomisation_commitment.json` — hashes and counts only.

Before observer execution, preserve the commitment JSON and its SHA-256. The private truth ledger remains sealed until held-out predictions are emitted.

## Clip naming

The observer plan assigns deterministic opaque names such as:

`b<opaque-id>__p0_placebo.mp4`

and one clip key for each active phase.

Treatment class and subtype must never appear in filenames, directories or observer-facing metadata.

## Protected physical QC

A salt-derived 25% sample of blocks is selected independently for blinded treatment-compliance review.

Annotators do not see observer outputs. They record only whether the planned physical conditions were actually present and whether a gross protocol violation occurred.

QC may invalidate a block or the whole physical claim according to the frozen protocol, but it may not relabel a treatment after looking at model output.

## Pre-observer validation

After acquisition and before either observer is run:

```bash
python scripts/v13_validate_capture_logs.py \
  --observer-plan <v13_observer_plan.csv> \
  --commitment <v13_randomisation_commitment.json> \
  --block-log <v13_block_capture_log.csv> \
  --phase-log <v13_phase_capture_log.csv> \
  --output-receipt <v13_capture_validation.json>
```

This establishes the actual physical day×scene cluster identities and verifies the non-cumulative phase contract.

Then validate the byte-complete field bundle:

```bash
python scripts/v13_validate_field_bundle.py \
  --commitment <v13_randomisation_commitment.json> \
  --private-truth <PRIVATE/v13_private_truth_ledger.csv> \
  --observer-plan <v13_observer_plan.csv> \
  --qc-plan <v13_protected_qc_plan.csv> \
  --clips-dir <CLIP_DIRECTORY> \
  --output-receipt <v13_field_byte_receipt.json>
```

The validator checks committed file hashes, exact 180/720 cardinality, placebo position, active intervention order, public/private block-ID agreement, absence of treatment-truth tokens in the public observer plan and the presence/hash of every clip.

The private truth ledger is used only in the private operator environment. It is not transferred to observer execution.

## Measurement path

The pre-field measurement freeze fixes:

- 1920×1080 RGB24, constant 30 fps, exactly 300 frames/phase;
- retained native frame indices 75, 105, 135, 165, 195, 225, 255, 285;
- V10 deterministic grayscale/downsample canonicalisation to 96×128;
- block background = pixel-wise median of the eight retained placebo frames only;
- the same placebo background for placebo and all three active phases;
- PolliPi input = frame/background only;
- InsePi bookkeeping frame index = 0;
- phase score = median of eight retained observer samples;
- active causal response = active phase median − placebo phase median.

Frames are repeated measurements, never uncertainty replicates.

## Analysis

Development blocks fit `interaction_sensing.causal_diagnostics` using the full physical battery.

Held-out evaluation:

1. truth ledger remains sealed;
2. observer traces are emitted on all clips;
3. the generic diagnostic planner replays a maximum two-intervention budget from the physical response table;
4. held-out class predictions are frozen;
5. prediction bytes and prediction ledger are committed;
6. only then is private treatment truth joined;
7. actual physical date×scene cluster identity is joined from the previously validated completed capture log;
8. report block-level and `day × scene` cluster-level results.

Uncertainty uses `day × scene` clusters, not frames. The preregistered analysis uses 5,000 cluster bootstrap resamples and also reports every held-out cluster explicitly.

## Claim boundary

V13 A requires both high absolute held-out performance and at least +0.10 over the best comparator. A single excellent day is insufficient: minimum held-out day×scene cluster accuracy must also exceed the frozen floor.

V13 does not validate natural pollinator detection accuracy. A standardised physical event proxy establishes the observation-system intervention response only. Natural ecological event accuracy remains a separate empirical question.

## Stop conditions

Do not proceed to scientific observer evaluation if:

- the scientific execution digest differs from the committed pre-field freeze;
- the private truth ledger commitment no longer matches;
- public filenames/metadata leak latent treatment identity;
- held-out days/scenes overlap development;
- within-block camera settings changed unexpectedly;
- apparatus is outside the frozen physical tolerance without a declared deviation;
- latent treatment baseline is not restored between active phases;
- a frozen treatment subtype was substituted after observer inspection;
- required clips are missing;
- protected QC identifies a gross protocol failure that invalidates treatment identity.

A failed physical protocol is evidence and must not be repaired under the same V13 generation.
