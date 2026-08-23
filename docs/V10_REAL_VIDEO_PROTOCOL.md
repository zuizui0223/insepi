# V10 real-video protocol — frozen before any scientific pixel inspection

## Purpose

V10 is a semi-empirical transfer test on **real pollinator-video pixels**, not a field biological-accuracy study. The seven source videos, their exact bytes, annotation provenance, container metadata and decoder identity were all frozen before this protocol.

The primary question is:

> Do the frozen observation-risk and exploration-guarded allocation principles respond appropriately to **known observation-process perturbations** when the underlying image texture comes from real ecological videos?

Because Experiment 1 does not deposit reusable frame-level human truth, V10 does **not** evaluate biological-event detection accuracy.

The machine-readable contract is `benchmarks/v10_real_video_protocol.json`. It is authoritative if prose and code disagree.

## Source and pre-result boundary

All seven repository-derived `bee_test_1.mp4` … `bee_test_7.mp4` files are included. Their SHA-256 identities are frozen in `benchmarks/v10_real_video_source_lock.json`; no clip can be dropped after observer performance is seen.

Before this protocol was written:

- no PolliPi or InsePi observer had been run on these real videos;
- no V10 video frame had been decoded for scientific inspection;
- Experiment 1 HyDaT/YOLO tracks had been classified as algorithm outputs, not truth;
- the exact decoder executable had been frozen without reading video bytes.

## Base windows

All videos are exactly 60 fps. V10 decodes only native frame indices satisfying `n mod 60 == 0`, beginning at `n=0`. Adjacent decoded frames form one-second pairs:

`background = frame at t-1 s`

`current = frame at t s`.

No image-content rule is used. This gives 58, 48, 59, 46, 57, 70 and 26 windows by video, **364 base windows total**.

## Canonical real-pixel representation

The observer-generation lattice was developed on 96×128 images with 32-pixel cells. Feeding raw 1920×1080 directly would silently change the effective method. V10 therefore preserves both the native 16:9 field of view and the 96×128 lattice:

1. frozen FFmpeg outputs RGB24;
2. convert to deterministic integer grayscale: `(77R + 150G + 29B + 128) // 256`;
3. because 1920/128 = 1080/72 = 15 exactly, average each non-overlapping 15×15 block with integer nearest rounding `(sum + 112) // 225`, yielding 72×128;
4. edge-pad 12 rows above and below, yielding 96×128 uint8.

There is no crop, learned resize, content-aware transform or post-hoc manual edit.

## Paired perturbation transfer

The background always remains native. The current canonical frame has 19 variants:

- native;
- shadow × three V7 intensity tiers;
- occlusion × three tiers;
- blur × three tiers;
- sensor banding × three tiers;
- glare × three tiers;
- framing drift × three tiers.

The tiers are the already frozen V7 values `0.45, 0.80, 1.15`. Operator formulas are carried from the frozen V7 generator rather than retuned on real data. V7 wind, clutter, lens, shake and composite families are excluded **before** real-pixel execution for the reasons recorded in the JSON contract.

Thus:

`364 × (1 + 6 × 3) = 6,916` conditions.

Every random operator parameter is derived deterministically from the source-video SHA, native frame index, family and tier.

## Observer contract

Both observers receive only the same canonical `(frame, background)` pair.

PolliPi evidence priority is frozen as:

- strong candidate = 1.0;
- uncertain local activity = 0.70;
- otherwise = 0.

InsePi observability priority is:

`max(false_event_risk, missed_event_risk, attribution_risk)`.

Perturbation labels, video-level human aggregates and all other truth/provenance fields are attached only **after** each observer emits its decision.

Scientific observer execution remains blocked until the exact frozen V5 commits are reachable:

- PolliPi `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`;
- InsePi `980813bab996909020140fad5bd83b055eb3db9c`.

No reconstructed substitute is permitted.

## Primary paired metrics

For each real native pair and each perturbation variant:

`risk_delta = InsePi risk(perturbed) - InsePi risk(native)`.

Report:

- median paired risk shift by family/tier;
- fraction of base windows with positive shift;
- global median shift by tier;
- within-family dose monotonicity across the three tiers.

PolliPi outputs are diagnostic only because biological truth is unavailable. Report perturbation-induced candidate-rate change and transitions to `environmental_noise`; do not call them sensitivity, specificity or accuracy.

## Allocation transfer panels

Allocation uses **18 fixed panels**, one per family × tier. In each panel exactly 182 of the 364 base windows receive that known disturbance and the remaining 182 remain native. The disturbed half is selected by a fixed SHA-256 rank over stable window IDs, not by observer output.

At budgets 10%, 25% and 50%, 200 paired selection replicates compare:

- uniform;
- frozen V6 50U/10E/40O;
- 50U/50E;
- 50U/50O;
- 50U + a 20E/80O fused targeted score;
- 50U + max(E,O).

The primary allocation truth is simply the known perturbation assignment. Metrics are disturbance recall, recall ratio to paired uniform and disturbance yield. Representation is summarized by source-video TV and video×temporal-quartile TV.

Biological-event recall is forbidden in V10.

## Claim ceiling

The claim level is determined mechanically after locked observer execution:

- **A — broad transfer:** at least 5/6 families have positive high-tier median risk shift, at least 4/6 have nondecreasing family-level median risk across tiers, and frozen V6 is at least uniform on mean disturbance recall in at least 45/54 family-tier×budget cells with overall mean ratio >1.
- **B — observer transfer, allocation mixed:** the two observer-transfer conditions pass but the allocation condition does not.
- **C — partial transfer:** only 3–4 families show positive high-tier median shift, or support is clearly family-specific.
- **D — null/adverse:** at most 2 families show positive high-tier median shift, or the global high-tier median shift is non-positive.

No V10 result can establish field pollinator-detection accuracy, pollinator-identification accuracy, occupancy/detection-probability validity, or universal optimality of 50/10/40.

## Relation to V7

V10 is orthogonal to locked V7. It uses no V7 final seed, pixels, traces or gate. It may not rescue, reinterpret or tune around a failing V7. The only V7 content reused is the **already frozen generic perturbation operator/intensity contract**.

Pixel materialisation may occur after this protocol freeze. Observer execution may not occur until both exact V5 commits are externally reachable and adapter compatibility checks pass.
