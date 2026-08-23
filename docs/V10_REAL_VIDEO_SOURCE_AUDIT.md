# V10 real-video source audit — source members frozen before observer execution

V10 is intended to add a semi-empirical test on real pollinator footage. This document remains **source provenance only**: no PolliPi/InsePi decision, V10 performance metric, perturbation choice, or result has yet been generated.

## Repository source

**Honeybee video tracking data**  
Ratnayake, Dyer & Dorin (2020), Monash University  
DOI: `10.26180/5f4c8d5815940`  
Figshare article id: `12895433`, version `1`  
Licence: **CC BY 4.0**.

The associated HyDaT study evaluated seven outdoor Scaevola honeybee sequences, with natural background and illumination variation and occlusion. The public HyDaT notebook independently gives the naming anchor `./input_video/bee_test_1.mp4`.

## What the repository actually stores

The public Figshare API exposes five top-level files rather than seven direct MP4 downloads. The relevant containers are:

- `Experiment_Data.zip` — file id `24528083`, 10,912,414,618 bytes, MD5 `885f88ec6075ed357f77615a13aff362`;
- `Honeybee_videos.zip` — file id `24528389`, 23,852,239,741 bytes, MD5 `a890fef7a1d3a5d174fc2d798c7ec301`.

Range-only inspection of `Honeybee_videos.zip` showed that `Scaevola.zip` is itself Deflate-compressed and would require streaming about 6.97 GB before its internal directory could be recovered. We therefore did **not** use that expensive route.

Range-only inspection of `Experiment_Data.zip` found the much smaller canonical evaluation bundle:

`Experiment_Data/Experiment_1/Experiment_1-Test_Videos.zip`

This member is Deflate method 8, compressed size `463,692,433` bytes, uncompressed size `463,635,092` bytes, CRC32 `8a7f6f61`.

## Canonical source resolution

Workflow run `32614581275`, from pre-lock head:

`05923e5a48ef10be94bbb9dc00891235952f5023`

streamed exactly that nested compressed member using HTTP Range reads, decoded its raw Deflate stream, verified the complete member CRC32 and size, retained only a bounded tail containing the nested ZIP central directory, and wrote **no decompressed video member to disk**.

The nested central directory contains one directory entry plus exactly seven video members:

| Video | Uncompressed bytes | Compressed bytes | CRC32 |
|---|---:|---:|---|
| `bee_test_1.mp4` | 69,416,364 | 69,366,017 | `be8e6756` |
| `bee_test_2.mp4` | 59,616,748 | 59,575,431 | `b5d82f12` |
| `bee_test_3.mp4` | 73,510,301 | 73,459,641 | `b4075043` |
| `bee_test_4.mp4` | 61,481,726 | 61,443,077 | `f2003132` |
| `bee_test_5.mp4` | 74,741,879 | 74,693,757 | `7087e0f0` |
| `bee_test_6.mp4` | 89,449,937 | 89,390,525 | `17091e35` |
| `bee_test_7.mp4` | 35,727,534 | 35,705,130 | `c8c0caa4` |

Thus the seven-video evaluation set is now a **repository-derived fact**, not a filename inference.

The machine-readable lock is:

`benchmarks/v10_real_video_source_lock.json`

Canonical source-resolution evidence hashes are recorded there, including artifact ZIP SHA-256 `12ff6f92a09b8114f87088245359bd6a5d993795c04c390c19a1a4ac8864acef` and nested test-bundle index SHA-256 `aef593dc941c3265b469d15639af9bee5a27352fd0104a9d4b33d061837f14bd`.

## Selection rule is frozen

V10 uses **all seven** `bee_test_*.mp4` members in `Experiment_1-Test_Videos.zip`.

No clip was excluded, ranked, previewed, or selected based on either observer's output. There is therefore no post-performance clip selection seam.

## Remaining byte lock

The source members are identified, but scientific V10 is still blocked on one mechanical step: each of the seven MP4 members must be extracted and given a local SHA-256.

Before observer execution, extraction must verify for every file:

1. exact filename from the source lock;
2. exact uncompressed byte size;
3. exact ZIP CRC32;
4. then SHA-256 of the extracted MP4 bytes.

All seven SHA-256 values must be frozen together. Observer execution is forbidden if even one member is missing or mismatched.

## What must be frozen after the byte lock

A separate **pre-result V10 scientific protocol** must then fix, before either observer output is inspected:

- frame/window extraction and temporal sampling;
- native-scene treatment and any injected perturbation registry, if perturbations are used at all;
- exact PolliPi and InsePi observer commits/adapters;
- allocation policies and comparators;
- metrics and interpretation rules;
- treatment of available manual or algorithm-generated track annotations;
- claim ceiling for a real-video pass, null result, or adverse result.

## Scientific boundaries

- V10 does not alter the frozen V6 `50% exploration / 10% evidence / 40% observability / 0% disagreement` method.
- V10 does not use or change V7 worlds, seed, pixels, traces, gate or claim ceiling.
- V10 cannot rescue or reinterpret a failing V7 result.
- The source lock is not evidence of observer accuracy or allocation performance.
- HyDaT/YOLO output tracks are not automatically treated as ecological ground truth; their provenance must be audited before use as labels.
- If exact frozen V5 observer commits remain unavailable, V10 can prepare data and protocol but must not substitute reconstructed observer code.
