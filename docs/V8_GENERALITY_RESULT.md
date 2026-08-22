# V8 generality result — applicability, not universal optimality

## Immutable first run

The first pre-registered V8 execution completed successfully on workflow run `32546131520` from pre-result head:

`5b41b99cc2f4d3f58f3db8dcffdc569564b8178b`

- protocol SHA-256: `517958d2361f9fe5b6f8b962d5a5b5f552d942223b9cede8585253dde3fac6d2`
- result SHA-256: `09b670fb7efa01681578791cc02ca30c9807d9cb7fa80bba3951a1fc6529f4ce`
- uploaded artifact ZIP SHA-256: `5d1babec6bbfd667a3405f877d3a7394655b4b955ea0cd1c1a59776e0eb61b3d`
- contract tests: 8 passed before benchmark execution;
- V7 materialisation: absent;
- frozen 50/10/40/0 weights: unchanged.

No weight, grid, comparator, metric or estimator was altered after this result was inspected.

## Headline result

Across 864 abstract observer/world regimes:

- frozen V6 joint recovery was at or above uniform in **794 / 864 = 91.9%** of regimes;
- frozen V6 was at least as good as every tested same-50%-exploration comparator in only **185 / 864 = 21.4%** of regimes;
- mean frozen-V6 joint recovery ratio to uniform = **1.48785**;
- median = **1.15969**;
- 10th percentile = **1.00483**;
- 5th percentile = **0.96571**;
- worst regime = **0.66068**.

The correct interpretation is therefore **robust fixed compromise under unknown conditions**, not per-regime optimality.

## Comparison with fixed same-exploration policies

| Fixed policy | Mean joint ratio | Median | Fraction >= uniform | 10th percentile | Worst |
|---|---:|---:|---:|---:|---:|
| V6 separate 10E/40O | **1.488** | **1.160** | **0.919** | **1.005** | **0.661** |
| 50E only | 1.453 | 0.643 | 0.411 | 0.466 | 0.210 |
| 50O only | 1.008 | 0.999 | 0.471 | 0.890 | 0.257 |
| fused 20E/80O | 1.321 | 1.152 | 0.782 | 0.646 | 0.365 |
| max(E,O) | 1.276 | 1.106 | 0.713 | 0.794 | 0.457 |
| uniform | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

Among the targeted policies, V6 has the strongest lower tail and the highest fraction of regimes that avoid losing either event or hidden-error recovery relative to uniform. However, the identity of the **best** targeted policy changes across regimes, so a clairvoyant regime-specific policy can frequently outperform frozen V6.

This distinction matters: V6 is valuable when the regime is not known in advance, not because 10E/40O is universally optimal.

## Prevalence is the clearest boundary

| Event prevalence | V6 >= uniform | V6 best same-alpha | Mean V6 joint |
|---:|---:|---:|---:|
| 0.02 | **100%** | 6.5% | **2.256** |
| 0.10 | **100%** | 13.9% | **1.627** |
| 0.50 | **100%** | 23.6% | **1.093** |
| 0.90 | **67.6%** | 41.7% | **0.976** |

The best same-alpha comparator also changes with prevalence:

- prevalence 0.02: evidence-only is best in 88.9% of regimes;
- prevalence 0.10: evidence-only 50.9%, fused 38.4%;
- prevalence 0.50: fused 69.0%, max 28.7%;
- prevalence 0.90: observability-only 47.7%, max 28.7%, fused 23.6%.

Thus the dual-observer portfolio is not a universal optimizer. Its advantage is that it avoids the very large failure regions suffered by a fixed single-observer policy when the true event regime changes.

## Residual correlation creates tail risk

As shared residual correlation increases, the fraction of regimes in which V6 remains at/above uniform decreases:

- correlation 0.0: 97.2%;
- correlation 0.5: 95.1%;
- correlation 0.9: 83.3%.

At the same time, mean joint gain increases because some high-correlation/rare-event regimes produce very large gains. Therefore a high mean alone would be misleading. The MEE-facing result should emphasize lower-tail robustness and explicit failure regions rather than only the overall mean.

## The ecological-inference result is cleaner

The targeted selected sample is not generally representative of event prevalence.

For frozen V6, averaged over all 864 regimes:

- naïve selected-sample prevalence RMSE = **0.05581**;
- exploration-only prevalence RMSE = **0.03941**;
- mean signed naïve prevalence bias = approximately **+0.0455**;
- mean signed exploration-only bias = approximately **-0.0001**.

By true event prevalence:

| prevalence | naive bias | exploration bias | naive RMSE | exploration RMSE |
|---:|---:|---:|---:|---:|
| 0.02 | +0.0487 | -0.0010 | 0.0511 | **0.0176** |
| 0.10 | +0.0778 | ~0.0000 | 0.0818 | **0.0382** |
| 0.50 | +0.0460 | +0.0003 | **0.0631** | 0.0638 |
| 0.90 | +0.0095 | +0.0002 | **0.0272** | 0.0380 |

The uniform exploration subset remains essentially unbiased, while the full targeted sample is positively biased toward events. At high prevalence the larger targeted sample can have lower RMSE despite its small bias, showing the expected bias/variance trade-off.

The strongest ecological-design conclusion is therefore not “discard targeted samples for inference.” It is:

> **retain an explicit probability-sample exploration subset as a defensible denominator/reference design while using targeted arms for event recovery and error audit.**

This is a stronger and more ecological interpretation of the exploration guard than event-recovery benchmarking alone.

## Distributional distortion remains bounded but not always small

Frozen V6 disturbance-family TV across V8 has:

- mean = **0.2584**;
- maximum = **0.3951**.

The maximum remains below the half-exploration theoretical ceiling of 0.5, but many abstract regimes exceed the empirical 0.25 criterion used in the V4/V7 visual validation programme.

Therefore:

- `TV <= 0.5` from half exploration is a general analytical bound for the ideal mixture / conservative finite implementation;
- `TV <= 0.25` is **not** a general theorem and must remain an empirical locked-validation criterion specific to that benchmark family.

## What V8 changes in the paper claim

V8 argues against two overly strong narratives:

1. **“50/10/40 is universally optimal.”** False.
2. **“Any benefit is merely the 50% exploration component.”** Also too simple: same-alpha fixed alternatives have substantially larger failure regions, and the best targeted signal changes with event prevalence.

The stronger defensible narrative is:

> When event prevalence and observer reliability are not known in advance, guaranteed exploration plus separate evidence and observability quotas can provide a more robust fixed compromise than committing the targeted budget to one observer or one fused score. The method still has identifiable failure regions, especially when events are ubiquitous or observer residuals are strongly shared. The retained exploration subset additionally provides a near-unbiased reference sample for downstream ecological prevalence inference.

V7 remains the independent claim-bearing visual validation and is not modified by V8.
