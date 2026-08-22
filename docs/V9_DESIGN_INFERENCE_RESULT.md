# V9 design-based inference result — protected exploration is the inferential reference design

## Canonical frozen execution

The first V9 execution was run from pre-result head

`0505ecf53aaf7045d3d15dbf10143be52d8c5b79`

on workflow run `32547803107`.

- protocol SHA-256: `aa8bb9c762b7f952c2c298aa2435a9f52edc64f60ebf619b4df1898a83d7cca7`;
- result SHA-256: `2586a3d166a8e67c1012b470145cc3093d70d94da777c71a816736e09177eba0`;
- uploaded artifact ZIP SHA-256: `2768d54d72c19d06516bf1e579b7729569dad39db31edbc07526dafbcadea316`;
- 576 regimes;
- 57,600 generated finite populations;
- the complete run was executed twice under distinct Python hash seeds and produced byte-identical JSON/CSV evidence;
- V7 was not materialised;
- frozen V6 weights remained 50/10/40/0.

## Headline result

| Quantity | Naive full targeted sample | Protected exploration |
|---|---:|---:|
| Mean signed prevalence bias | +0.042576 | **+0.0000009** |
| RMSE | 0.059093 | **0.042819** |
| 95% interval coverage | 0.523889 | **0.977500** |
| Mean 95% interval width | 0.123066 | 0.154980 |

The protected estimator's empirical RMSE was almost exactly the theoretical SRSWOR standard deviation:

```text
empirical protected RMSE   = 0.0428193
theory-based mean SD       = 0.0423710
ratio                       = 1.01058
```

This is the main V9 validation result: the analytical probability-sampling argument, the actual guarded-selector implementation and the Monte Carlo behaviour agree.

## The naive complete sample can be badly misleading

The complete guarded sample contains preferentially selected event- and risk-priority windows. Treating it as if it were a representative random sample produced an average positive prevalence bias of 4.26 percentage points and nominal-95% coverage of only 52.4%.

The problem was strongest for rare/intermediate events:

| Nominal prevalence | Naive bias | Naive 95% coverage | Protected bias | Protected 95% coverage |
|---:|---:|---:|---:|---:|
| .01 | +.02784 | .4572 | -.00009 | **.9910** |
| .02 | +.04219 | .3270 | +.00016 | **.9851** |
| .05 | +.06066 | .2618 | +.00026 | **.9794** |
| .10 | +.06993 | .3179 | +.00034 | **.9740** |
| .50 | +.04596 | .8122 | -.00007 | **.9638** |
| .90 | +.00887 | .9673 | -.00060 | **.9718** |

Thus the adaptive sample is useful for **finding** events/errors but should not be treated naively as the ecological denominator.

## Protected design validity held across all tested prevalence-budget cells

Across the 24 nominal-prevalence × budget cells:

- minimum protected 95% coverage = **0.96125**;
- maximum absolute protected signed bias = **0.001505**;
- empirical RMSE / theoretical-SD ratios ranged from **0.9767 to 1.0307**.

Coverage remained above nominal across every tested budget when aggregated over the remaining regime dimensions:

| Total budget | Naive 95% coverage | Protected 95% coverage | Naive RMSE | Protected RMSE |
|---:|---:|---:|---:|---:|
| .05 | .5899 | **.9842** | .07761 | **.06524** |
| .10 | .5085 | **.9794** | .06555 | **.04504** |
| .25 | .4539 | **.9745** | .05013 | **.02717** |
| .50 | .5432 | **.9718** | .03370 | **.01761** |

## Precision cost is real and must remain visible

The protected exact intervals were about 25.9% wider on average than the naive Wilson intervals (`0.15498` vs `0.12307`). This is not a defect to tune away. The protected inference uses only the probability-sample component and therefore has less nominal sample size; its uncertainty interval is correspondingly wider while retaining valid coverage.

The protected estimator also did **not** have lower RMSE in every prevalence regime. At nominal prevalence .50 and .90, the larger targeted sample had smaller raw RMSE, even though its design validity was not guaranteed. This trade-off is important:

> targeted data can be precise for the wrong sampling distribution; protected exploration provides interpretable probability-sample inference.

The method therefore should not discard targeted observations. Instead it assigns them a different role: discovery/audit rather than naive denominator estimation.

## Study-design consequence

After V9, the guarded method has a clean two-purpose interpretation:

```text
protected uniform exploration
    -> probability-sample reference / ecological denominator

evidence + observability targeting
    -> efficient event and observation-error discovery
```

This is stronger than describing exploration only as an anti-bias safety valve. It gives the exploration component an explicit inferential function.

## What V9 proves and what it does not

V9 supports:

- exact design-unbiasedness of the protected prevalence estimator conditional on each realised finite world;
- correct finite-population variance formula;
- exact hypergeometric confidence intervals with at least nominal design coverage;
- implementation-level agreement between theoretical and empirical uncertainty;
- strong evidence that naive use of the full preferential sample can bias ecological prevalence estimates and destroy nominal CI coverage.

V9 does **not** establish:

- error-free field labels;
- occupancy/detection inference under repeated imperfect observations;
- unbiased inference from the complete targeted sample without its inclusion probabilities;
- spatial/temporal probability designs other than the frozen SRSWOR exploration component;
- field superiority of PolliPi or InsePi;
- a replacement for the still-pending locked V7 visual validation.

## Frozen interpretation

The MEE-facing method claim should now be framed as an adaptive ecological **study design**, not simply an event-recovery allocator:

> Reserve an explicit probability-sample exploration component for valid ecological inference, and use the remaining finite sensing budget adaptively to enrich biological events and observation-process failures. The two roles need not be collapsed into the same sample or estimator.
