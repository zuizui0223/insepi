# V10 real-video source audit — seven evaluation videos byte-frozen before observer execution

V10 is intended to add a semi-empirical test on real pollinator footage. This document remains **source provenance only**: no PolliPi/InsePi decision, V10 performance metric, perturbation choice, or result has yet been generated.

## Repository source

**Honeybee video tracking data**  
Ratnayake, Dyer & Dorin (2020), Monash University  
DOI: `10.26180/5f4c8d5815940`  
Figshare article id: `12895433`, version `1`  
Licence: **CC BY 4.0**.

The associated HyDaT study evaluated seven outdoor Scaevola honeybee sequences, with natural background and illumination variation and occlusion. The peer-reviewed paper states that the seven sequences were randomly selected from continuous footage; each was 27–71 s long, totalling 6 min 11 s, and detection was evaluated against human observations. The public HyDaT notebook independently gives the naming anchor `./input_video/bee_test_1.mp4`.

## What the repository actually stores

The public Figshare API exposes five top-level files rather than seven direct MP4 downloads. The relevant containers are:

- `Experiment_Data.zip` — file id `24528083`, 10,912,414,618 bytes, MD5 `885f88ec6075ed357f77615a13aff362`;
- `Honeybee_videos.zip` — file id `24528389`, 23,852,239,741 bytes, MD5 `a890fef7a1d3a5d174fc2d798c7ec301`.

Range-only inspection of `Honeybee_videos.zip` showed that `Scaevola.zip` is itself Deflate-compressed and would require streaming about 6.97 GB before its internal directory could be recovered. We therefore did **not** use that expensive route.

Range-only inspection of `Experiment_Data.zip` found the much smaller canonical evaluation bundle:

`Experiment_Data/Experiment_1/Experiment_1-Test_Videos.zip`

This member is Deflate method 8, compressed size `463,692,433` bytes, uncompressed size `463,635,092` bytes, CRC32 `8a7f6f61`.

## Canonical member resolution

Workflow run `32614581275`, from pre-lock head:

`05923e5a48ef10be94bbb9dc00891235952f5023`

streamed exactly that nested compressed member using HTTP Range reads, decoded its raw Deflate stream, verified the complete member CRC32 and size, retained only a bounded tail containing the nested ZIP central directory, and wrote **no decompressed video member to disk**.

The nested central directory contains one directory entry plus exactly seven video members. Thus the seven-video evaluation set is a **repository-derived fact**, not a filename inference.

## Canonical byte lock

Workflow run `32614909080`, from pre-receipt head:

`2b6a2b8f0f808171169b6bdf938cc56c842a0124`

re-streamed the already-frozen nested test bundle, verified its complete size and CRC32, wrote the decoded nested ZIP to temporary storage, checked all seven member names/sizes/CRCs/offsets against the pre-byte source lock, streamed each MP4 from the temporary ZIP to SHA-256, and deleted the temporary ZIP. Individual MP4 files were **not** written to the workspace or uploaded as artifacts. Neither observer was executed.

Nested test-bundle SHA-256:

`2249aa5c72435b12b3983955bd9b8a92b0b2350ef70dd88ca815a14ad7c044f1`

| Video | Uncompressed bytes | CRC32 | SHA-256 |
|---|---:|---|---|
| `bee_test_1.mp4` | 69,416,364 | `be8e6756` | `3223f41041629bcba84d2686f74c08c3d8e03b5cfef27ec74198eb5e72f69de0` |
| `bee_test_2.mp4` | 59,616,748 | `b5d82f12` | `1d39f369ab5c4a6bf015fec69c8aaf65ec10f618c50fda69e947c510e89959fe` |
| `bee_test_3.mp4` | 73,510,301 | `b4075043` | `6193736d994ad1ec0a94558aed41d7d93643c6bc830fb9d5ed1d5b21e9dbf433` |
| `bee_test_4.mp4` | 61,481,726 | `f2003132` | `c0a9c8219d0e588a976aa57dbb35ec66b1efadf927223e13f2f10ccfdf8f15f9` |
| `bee_test_5.mp4` | 74,741,879 | `7087e0f0` | `eb24100057410ec31dc4bd452507b6457abcd3c4e5ba629d65501f9ad7e6c49c` |
| `bee_test_6.mp4` | 89,449,937 | `17091e35` | `bc325107cedafbeae508f118be563a11605a6dbae1e19a0d981bfcf49f51707f` |
| `bee_test_7.mp4` | 35,727,534 | `c8c0caa4` | `ce19e09cca6681d400c868597269ad207d2ddfcf43d151523d19f9f40bdb4448` |

Byte-receipt JSON SHA-256: `94db50ed3105a8b40a1dac036fe31591cb455c51d9534461df6192438b1ce7bc`  
Byte-lock workflow artifact ZIP SHA-256: `56e3d2e4003077e650496a11705c6d9cf8012bd7e3bc0220114721d2c170f3a0`.

The complete machine-readable lock is:

`benchmarks/v10_real_video_source_lock.json`

## Selection rule is frozen

V10 uses **all seven** `bee_test_*.mp4` members in `Experiment_1-Test_Videos.zip`.

No clip was excluded, ranked, previewed, or selected based on either observer's output. There is therefore no post-performance clip-selection seam.

## Source-lock status

The source side is now **complete**. Any future V10 materialiser must refuse a video unless its SHA-256 matches the table above.

Both source-resolution and byte-lock workflows are manual-only after their canonical successful runs; routine PR/document edits cannot silently regenerate or alter the source evidence.

## What must be frozen before scientific V10

A separate **pre-result V10 scientific protocol** must fix, before either observer output is inspected:

- frame/window extraction and temporal sampling;
- native-scene treatment and any injected perturbation registry, if perturbations are used at all;
- exact PolliPi and InsePi observer commits/adapters;
- allocation policies and comparators;
- metrics and interpretation rules;
- treatment of available human observations versus algorithm-generated HyDaT/YOLO outputs;
- claim ceiling for a real-video pass, null result, or adverse result.

The paper defines Experiment 1 detection rate against **human observations**: a frame is a successful detection when the algorithm's bee position falls on the bee's visible body, with fully/partly hidden frames treated as occlusions. This establishes that human-reference evaluation existed, but the repository outputs must still be audited before any file is treated as reusable frame-level ground truth.

## Scientific boundaries

- V10 does not alter the frozen V6 `50% exploration / 10% evidence / 40% observability / 0% disagreement` method.
- V10 does not use or change V7 worlds, seed, pixels, traces, gate or claim ceiling.
- V10 cannot rescue or reinterpret a failing V7 result.
- The source/byte lock is not evidence of observer accuracy or allocation performance.
- HyDaT/YOLO output tracks are not automatically treated as ecological ground truth; their provenance must be audited before use as labels.
- If exact frozen V5 observer commits remain unavailable, V10 may prepare real data and a pre-result protocol but must not reconstruct or substitute observer logic.
