# V13 end-to-end execution order

This order is part of the blinding/reproducibility boundary. Do not skip forward by giving held-out treatment truth to the observer or prediction environment.

## Stage 0 — preserve prior generations

Do not modify or rerun to tune:

- V7: locked **FAIL/C**;
- V11: locked **FAIL/D**;
- V12: locked **B**, result SHA-256 `7879cb05359eb45df76b8f9b77b3d2b412d0ae1d85e2315cb5a5c38299986222`.

V13 is a new physical generation.

## Stage 1 — private randomisation before field acquisition

Generate a cryptographically random 64-hex salt **locally**. Do not paste it into chat, GitHub, observer logs or manuscript materials.

Example local generation:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then, in a private directory:

```bash
python scripts/v13_build_randomisation.py \
  --salt "$PRIVATE_V13_SALT" \
  --output-dir PRIVATE_V13_PLAN
```

Private material:

- `v13_private_truth_ledger.csv`;
- the salt itself.

Observer-safe material:

- `v13_observer_plan.csv`;
- `v13_protected_qc_plan.csv`;
- `v13_randomisation_commitment.json`.

Preserve the commitment JSON and its SHA-256 before acquisition.

## Stage 2 — create field capture/QC templates

```bash
python scripts/v13_make_capture_templates.py \
  --observer-plan PRIVATE_V13_PLAN/v13_observer_plan.csv \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --output-dir V13_CAPTURE_LOGS

python scripts/v13_make_qc_template.py \
  --qc-plan PRIVATE_V13_PLAN/v13_protected_qc_plan.csv \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --output V13_QC_ANNOTATION_TEMPLATE.csv
```

The capture templates contain no latent treatment class.

## Stage 3 — physical acquisition

Collect exactly:

- 108 development blocks;
- 72 held-out blocks on new days/scenes;
- 180 total blocks;
- 4 clips per block;
- 720 total phase clips.

Every clip must be:

- 1920×1080;
- constant 30 fps;
- exactly 300 native frames / 10 s.

Every block:

1. placebo;
2. three active interventions in the private-salt order;
3. 5-s washout before each active phase;
4. restore the same latent treatment baseline before every active phase;
5. never accumulate active interventions.

Complete the block and phase capture logs while operating the experiment.

## Stage 4 — capture-log gate

Before any observer execution:

```bash
python scripts/v13_validate_capture_logs.py \
  --observer-plan PRIVATE_V13_PLAN/v13_observer_plan.csv \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --block-log V13_CAPTURE_LOGS/v13_block_capture_log.csv \
  --phase-log V13_CAPTURE_LOGS/v13_phase_capture_log.csv \
  --output-receipt V13_CAPTURE_LOGS/v13_capture_validation.json
```

Observer execution is forbidden if this step fails.

## Stage 5 — byte-level field bundle validation

```bash
python scripts/v13_validate_field_bundle.py \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --private-truth PRIVATE_V13_PLAN/v13_private_truth_ledger.csv \
  --observer-plan PRIVATE_V13_PLAN/v13_observer_plan.csv \
  --qc-plan PRIVATE_V13_PLAN/v13_protected_qc_plan.csv \
  --clips-dir V13_CLIPS \
  --output-receipt V13_FIELD_BYTE_RECEIPT.json
```

This records every clip SHA-256 and verifies 180/720 cardinality and blinding metadata.

The private truth ledger is used here only to verify the commitment/plan relationship in the private operator environment. It is not transferred to observer execution.

## Stage 6 — materialise one canonical truth-free pixel artifact

Use the same pinned `imageio-ffmpeg==0.6.0` binary frozen in the V10/V13 decoder contract.

```bash
FFMPEG_PATH="$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')"
python scripts/v13_materialize_pixels.py \
  --observer-plan PRIVATE_V13_PLAN/v13_observer_plan.csv \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --clips-dir V13_CLIPS \
  --ffmpeg "$FFMPEG_PATH" \
  --output-dir V13_PIXELS
```

Outputs:

- `v13_frames.npy`;
- `v13_backgrounds.npy`;
- `v13_safe_registry.json`;
- `v13_pixel_receipt.json`.

No latent treatment truth enters this artifact.

## Stage 7 — exact observer checkouts and smoke gates

Exact required commits:

PolliPi:

`d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`

InsePi:

`980813bab996909020140fad5bd83b055eb3db9c`

Use the already published `frozen/v5-method` branches and verify exact tips.

Before real pixels:

```bash
python scripts/v13_run_pollipi_frozen.py \
  --source-root POLLIPI_FROZEN \
  --smoke-test

python scripts/v13_run_insepi_frozen.py \
  --source-root INSEPI_FROZEN \
  --smoke-test
```

InsePi smoke includes frame-index invariance at bookkeeping indices 0 / 1 / 5759.

## Stage 8 — emit truth-free observer traces

```bash
python scripts/v13_run_pollipi_frozen.py \
  --source-root POLLIPI_FROZEN \
  --artifact-dir V13_PIXELS \
  --output V13_TRACES/pollipi_v13_trace.jsonl

python scripts/v13_run_insepi_frozen.py \
  --source-root INSEPI_FROZEN \
  --artifact-dir V13_PIXELS \
  --output V13_TRACES/insepi_v13_trace.jsonl
```

Each trace contains 5,760 sample results plus one provenance record.

## Stage 9 — convert traces to safe block responses

```bash
python scripts/v13_summarize_observer_traces.py \
  --artifact-dir V13_PIXELS \
  --pollipi-trace V13_TRACES/pollipi_v13_trace.jsonl \
  --insepi-trace V13_TRACES/insepi_v13_trace.jsonl \
  --output-dir V13_RESPONSES
```

Outputs are truth-free:

- phase medians;
- 180 block-level `(delta_evidence, delta_observability)` triplets;
- response receipt/hashes.

## Stage 10 — split private truth in the private environment

```bash
python scripts/v13_split_private_truth.py \
  --private-truth PRIVATE_V13_PLAN/v13_private_truth_ledger.csv \
  --commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --output-dir PRIVATE_V13_TRUTH_SPLIT
```

Transfer to the blinded prediction environment **only**:

- `v13_development_labels.csv`.

Keep sealed:

- `v13_heldout_truth_SEALED.csv`.

## Stage 11 — blinded held-out prediction

```bash
python scripts/v13_predict_blinded.py \
  --responses V13_RESPONSES/v13_safe_block_responses.csv \
  --response-receipt V13_RESPONSES/v13_response_receipt.json \
  --development-labels PRIVATE_V13_TRUTH_SPLIT/v13_development_labels.csv \
  --output V13_PREDICTIONS/v13_predictions.json
```

The predictor has no held-out-truth argument.

## Stage 12 — freeze prediction commitment BEFORE truth unseal

```bash
python scripts/v13_commit_prediction.py \
  --predictions V13_PREDICTIONS/v13_predictions.json \
  --output V13_PREDICTIONS/v13_prediction_commitment.json
```

Preserve this commitment in a durable location before opening held-out truth. Record both:

- prediction file SHA-256;
- prediction ledger SHA-256.

## Stage 13 — blinded protected QC

Annotators complete only the salt-selected QC template. They do not see PolliPi/InsePi outputs or predicted classes.

Every selected row must explicitly record treatment-compliance questions and gross protocol violation yes/no.

## Stage 14 — unseal held-out truth and run the frozen evaluator

Only now:

```bash
python scripts/v13_evaluate_locked.py \
  --predictions V13_PREDICTIONS/v13_predictions.json \
  --prediction-commitment V13_PREDICTIONS/v13_prediction_commitment.json \
  --heldout-truth PRIVATE_V13_TRUTH_SPLIT/v13_heldout_truth_SEALED.csv \
  --truth-split-receipt PRIVATE_V13_TRUTH_SPLIT/v13_truth_split_receipt.json \
  --randomisation-commitment PRIVATE_V13_PLAN/v13_randomisation_commitment.json \
  --qc-plan PRIVATE_V13_PLAN/v13_protected_qc_plan.csv \
  --qc-annotations V13_QC_ANNOTATIONS.csv \
  --output V13_RESULT/v13_report.json
```

The evaluator reports:

- block-level performance;
- six held-out day×scene cluster results;
- 5,000-cluster-bootstrap interval;
- one-intervention and two-intervention performance;
- full-battery ceiling;
- A/B/C/D claim level;
- complete prediction/truth/QC provenance hashes.

## Non-negotiable stop boundary

Do not create a V13 scientific result if any earlier gate fails. Do not replace a failed physical block, treatment subtype, claim rule or held-out split after observer output under the same generation.
