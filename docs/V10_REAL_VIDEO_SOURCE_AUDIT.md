# V10 real-video source audit — no semi-empirical run before byte-level source lock

V10 is intended to add a semi-empirical test on real pollinator footage. This document is **source-resolution only**. It does not define a V10 result generation yet.

## Preferred source

**Honeybee video tracking data**  
Ratnayake, Dyer & Dorin (2020), Monash University  
DOI: `10.26180/5f4c8d5815940`  
Monash Bridges article id: `12895433`  
Declared licence: **CC BY 4.0**.

The associated PLOS ONE study evaluated seven Scaevola honeybee video sequences randomly selected from continuous outdoor footage. Each sequence was 27–71 seconds; total evaluation footage was 6 min 11 s. The videos contain natural changes in background, illumination and bee movement, and at least one bee occlusion occurred in every sequence. This makes the set a substantially better semi-empirical stress test than creating more synthetic image perturbations.

The public HyDaT repository associated with the data names at least one evaluation input explicitly:

```text
./input_video/bee_test_1.mp4
```

and writes the corresponding `bee_test_1_track.csv`. This provides a reproducible naming anchor, but it is **not sufficient by itself** to infer all seven file identifiers or download URLs.

## Why the dataset is preferable to the 2022 strawberry dataset for the first V10

The 2022 Spatial Monitoring dataset is also CC BY 4.0 and contains ten 10-minute evaluation videos (100 min total, 180,000 frames). It is valuable for a later cross-system extension, but its complete archive is ~19.85 GB.

The Honeybee dataset's seven evaluation clips total only 6 min 11 s and directly contain wind-blown foliage and occlusion. V10 should therefore try to lock these seven short evaluation clips first rather than downloading either complete 19–47 GB repository archive.

## Required source lock before V10 can exist

For every candidate evaluation video, the following must be obtained from the repository API or landing-page metadata:

- immutable article/version identifier;
- Figshare/Monash file id;
- exact filename;
- exact byte size;
- direct download URL supplied by the repository;
- repository-provided MD5 when available;
- local SHA-256 after download;
- licence and attribution string.

No filename is reconstructed or guessed from `bee_test_1.mp4`.

## Resolution workflow

`scripts/resolve_v10_figshare_source.py` queries the public Figshare article API and writes a machine-readable list of all files and video candidates. The CI workflow intentionally downloads **metadata only**, not video bytes.

Only after this resolver yields a manageable fixed set will a separate pre-result V10 protocol be committed. That future protocol must freeze video file IDs/hashes, frame/window extraction, native-versus-injected disturbance handling, observer adapters, metrics and interpretation before observer outputs are inspected.

## Scientific boundaries

- V10 must not alter frozen V6 weights.
- V10 must not use or change V7 worlds, seed, pixels, traces or gate.
- V10 cannot rescue a failing V7 result.
- Real-video source resolution is not evidence of method performance.
- If the repository API cannot expose individual files reproducibly, V10 remains blocked rather than substituting an unversioned mirror or manually chosen local clip.
