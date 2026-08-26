# V10 annotation provenance audit — Experiment 1 frame-level human truth is not deposited

## Question

Before using the seven byte-frozen real videos for V10, can any deposited Experiment 1 file legitimately serve as frame-level human reference truth?

**Answer: no.** The deposit supports human-reference evaluation at the aggregate level for Experiment 1, but the audited frame-level CSVs are outputs of HyDaT and stand-alone YOLO, not human annotations.

## Canonical audit

Workflow run `32615437253`, head `f2cd89b1316091e69903557b1b541ba889239612`, accessed no video pixels and ran neither observer. Artifact ZIP SHA-256:

`1454a8f10aef504baba3782597d8f11d77a05483208474ef3814ac8fb32a55df`

The audit extracted four small files from the already byte-locked repository container:

1. `Experiment1-Results.xlsx`;
2. `Experiment_1-CSV_HyDaT.zip`;
3. `Experiment_1-CSV_YOLO.zip`;
4. `Experiment_2 - Observations_Record.xlsx`, used only as a provenance-format comparator.

## Experiment 1 Results workbook

`Experiment1-Results.xlsx` has two sheets, `Detection-rate` and `Tracking-time`.

`Detection-rate` contains, per test video:

- Total Frames;
- **HB Occluded Frames**;
- **HB visible frames** = Total − Occluded;
- HyDaT Detected Frames and Detection rate;
- Stand-alone YOLO Detected Frames and Detection rate.

Thus the workbook clearly combines human-reference aggregate counts with algorithm-summary counts. It does **not** contain per-frame human coordinates or a frame-indexed visible/occluded label vector.

The workbook also contains an explicit manual adjustment in `Detection-rate!E9`: `=1338-78`. That is compatible with a curated summary table, not a reusable frame-level label file.

## Experiment 1 CSV bundles are algorithm outputs

Both HyDaT and YOLO CSV bundles contain one CSV per `bee_test_1` … `bee_test_7` with the same algorithm-track schema:

`nframe, x0, y0, area, x, y, occlusion, sx, sy, method, px, py, x0i, y0i, sx11, sy11, speed, speeds, angle, delta_area, mse_area, state`

No column or member name identifies human/manual/ground-truth coordinates or visibility labels.

The strongest internal check is that the CSV `occlusion` field is algorithm-specific rather than human truth:

- in the YOLO CSVs, the number of rows with `occlusion == 0` exactly reproduces the workbook's stand-alone YOLO detected-frame count in **all seven** videos;
- in the HyDaT CSVs, the same condition reproduces the workbook's HyDaT detected-frame count in videos 1–6; video 7 has 1338 such rows, while the workbook manually uses `1338-78 = 1260`;
- the HyDaT and YOLO `occlusion` sequences differ for the same videos, which is impossible if the column were a shared human-reference label.

Therefore these CSVs are useful as historical algorithm outputs only. They cannot be used as V10 truth without circularity.

## Experiment 2 provides the contrast

The complete `Experiment_Data.zip` member index contains an explicitly named:

`Experiment_Data/Experiment_2/Experiment_2 - Observations_Record.xlsx`

The workbook itself contains blocks headed **Human Observation** with categories `Occluded`, `Exited FoV`, and `Other`, cross-tabulated against **HyDaT Estimate**. This is a clear human-reference record, but it belongs to a different experiment/video and is not transferable to the seven Experiment 1 videos.

The contrast is informative: when the deposit supplies human observations, it labels them explicitly. No analogous Experiment 1 observation-record member exists.

## Frozen decision

For scientific V10:

- **do not** use HyDaT CSVs as ground truth;
- **do not** use YOLO CSVs as ground truth;
- **do not** convert `Experiment1-Results.xlsx` into invented frame-level labels;
- human visible/occluded counts from the workbook may be retained only as secondary video-level context;
- the primary non-circular V10 target will be **known, deterministic perturbations applied to the seven byte-frozen real videos**.

This means V10 can test whether the observation-risk machinery and guarded allocation transfer from synthetic images to real ecological pixels, but it cannot by itself claim field biological-event detection accuracy.

## Next protocol requirement

Before any video pixel is decoded for observer evaluation, V10 must freeze:

1. MP4 container metadata and frame/window selection;
2. background construction;
3. deterministic perturbation operators/intensities and assignment;
4. exact frozen observer commits/adapters;
5. same-exploration comparators;
6. real-pixel metrics and claim ceiling.

If the exact frozen V5 observer commits remain unreachable, data materialisation/protocol work may continue, but observer execution stays blocked.
