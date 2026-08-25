# V13 field-run checklist

This is an operator checklist for the already-frozen V13 protocol. It does not change scientific semantics. The authoritative execution order remains `docs/V13_EXECUTION_ORDER.md`; quantitative apparatus tolerances are authoritative in `benchmarks/v13_physical_apparatus_freeze.json`.

## Before acquisition — private operator environment

- [ ] Generate one cryptographically random 64-hex `PRIVATE_V13_SALT` locally.
- [ ] Do **not** paste the salt into GitHub, chat, observer logs, or manuscripts.
- [ ] Run `scripts/v13_build_randomisation.py`.
- [ ] Preserve `v13_randomisation_commitment.json` and its SHA-256 before recording starts.
- [ ] Keep `v13_private_truth_ledger.csv` and the salt outside the observer/prediction environment.
- [ ] Generate capture templates and the protected-QC annotation template.
- [ ] Run the execution-freeze preflight and confirm the scientific execution digest equals `benchmarks/v13_execution_freeze.json`.
- [ ] Confirm exact observers remain PolliPi `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9` and InsePi `980813bab996909020140fad5bd83b055eb3db9c`.

## Apparatus calibration — before observer output exists

- [ ] Lock camera-to-target plane distance at **1000 ± 20 mm** within each scene.
- [ ] Standard event proxy = **100 ± 2 mm** matte high-contrast circular disk on a matte neutral carrier.
- [ ] Development event-side impairment: same 100-mm geometry, target/carrier luminance contrast **0.20–0.30 × standard** under the same illumination.
- [ ] Development nuisance-side impairment: fan-driven mechanically isolated background, air speed **1.5 ± 0.2 m/s** at the background plane.
- [ ] Development shared-optical impairment: semi-opaque front-of-lens strip covering **0.30 ± 0.03** of canonical frame width across target and surrounding scene.
- [ ] Held-out event-side impairment: **50 ± 2 mm** high-contrast disk at the same target-plane centre.
- [ ] Held-out nuisance-side impairment: moving shadow **0.50 ± 0.05 Hz**; trough illuminance **0.60 ± 0.10 × unshadowed**.
- [ ] Held-out shared-optical impairment: full-aperture diffusion filter with visible transmittance **0.70 ± 0.10**.
- [ ] Make these physical measurements without consulting PolliPi/InsePi outputs.
- [ ] If a specified subtype/tolerance is infeasible, stop before acquisition rather than substituting another subtype under V13.

## Per physical block

- [ ] Treat one block — not one frame — as the experimental unit.
- [ ] Record actual local date and physical scene code.
- [ ] Record device, firmware, lens, mount, exposure, gain, focus, and lens position.
- [ ] Record 1920×1080 constant-30-fps clips.
- [ ] Placebo phase first, 10 s / 300 frames.
- [ ] Apply all three active interventions in the private-plan order.
- [ ] Each active phase is 10 s / 300 frames.
- [ ] Complete a 5-s washout before each active phase.
- [ ] Restore the **same latent treatment baseline** before each active phase.
- [ ] Never accumulate active interventions.
- [ ] Do not change camera settings within the block.
- [ ] Mark any operator/protocol deviation immediately; do not repair it post hoc after observer output.
- [ ] Mark block complete only when all four phase clips and metadata are present.

## Intervention semantics

- [ ] `event_restore`: replace current event proxy with the matched 100-mm standard target at the same location; unrelated nuisance/optical state remains unchanged.
- [ ] `observability_restore`: neutralise the nuisance source only; target and shared-optical state remain unchanged.
- [ ] `shared_restore`: replace the occluding/diffusing carrier with the matched clear carrier only.
- [ ] In no-fault blocks, use matched sham handling: identical standard target, nuisance remains off, identical clear carrier.
- [ ] After every active phase, restore the original latent placebo state before the next active phase.

## Acquisition totals

- [ ] Development: 108 blocks = 3 dates × 3 physical scenes × 4 classes × 3 replicates.
- [ ] Held-out: 72 blocks = 2 new dates × 3 new physical scenes × 4 classes × 3 replicates.
- [ ] Development and held-out dates are disjoint.
- [ ] Development and held-out physical scenes are disjoint.
- [ ] Total: 180 blocks and 720 phase clips.
- [ ] Every actual date × scene cluster contains exactly 12 blocks.

## Before any observer sees real V13 pixels

- [ ] Run `v13_validate_capture_logs.py`; require PASS.
- [ ] Run `v13_validate_field_bundle.py` with clip-byte validation; require PASS.
- [ ] Verify all 720 clip hashes are preserved.
- [ ] Run the exact-observer smoke gate; require exact commit, software-separation and frame-index checks to pass.
- [ ] Do not expose latent treatment class, subtype, treatment-success notes, private salt, or held-out truth to observer execution.

## Truth-free observation stage

- [ ] Materialise exactly one canonical V13 pixel artifact from the observer-safe plan.
- [ ] Confirm the artifact contains only safe registry metadata and canonical pixels.
- [ ] Run exact frozen PolliPi and InsePi on the same artifact bytes.
- [ ] Confirm each trace has 5,760 result rows plus provenance.
- [ ] Summarise eight repeated measurements per phase to phase medians.
- [ ] Compute each active response against the same within-block placebo summary.
- [ ] Produce the 180-row safe block-response table.

## Prediction freeze — still blinded

- [ ] In the private environment, split the truth ledger.
- [ ] Transfer **development labels only** to the prediction environment.
- [ ] Keep `v13_heldout_truth_SEALED.csv` sealed.
- [ ] Generate four-strategy held-out predictions.
- [ ] Create and durably preserve `v13_prediction_commitment.json`.
- [ ] Record prediction-file SHA-256 and prediction-ledger SHA-256.
- [ ] Verify the held-out truth has still not been read.

## Protected physical QC

- [ ] Annotate only the preselected protected-QC blocks.
- [ ] Annotators do not see observer outputs or predicted classes.
- [ ] Record treatment compliance and gross protocol violation exactly as observed.
- [ ] Do not relabel the latent treatment class from observer performance.

## Final unseal

- [ ] Only after prediction commitment exists, unseal held-out treatment truth.
- [ ] Run the locked evaluator with the same completed block log and its validation receipt.
- [ ] Final cluster identity comes from actual `recording_date_local × physical_scene_code`, not synthetic planning slots.
- [ ] Preserve all report/provenance hashes and the A/B/C/D result even if unfavorable.
- [ ] Do not replace failed blocks, change claim thresholds, or retune the diagnostic method under V13 after unseal.

## Stop conditions

Stop the V13 generation rather than silently repairing it if any of these occur:

- scientific execution digest mismatch;
- wrong frozen observer commit;
- missing/extra phase clip;
- non-30-fps or wrong-resolution recording;
- missing required native sample frame;
- cumulative intervention or failed baseline restoration;
- development/held-out date or scene overlap;
- fewer/more than six held-out physical clusters;
- apparatus outside frozen tolerance without a declared pre-observer deviation;
- latent treatment leakage into observer/prediction inputs;
- prediction file changes after commitment;
- held-out truth is read before prediction commitment;
- protected QC identifies a gross protocol violation that invalidates treatment identity.
