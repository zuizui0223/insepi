# V15-v2 cluster sampling and power planning

## Purpose

The V15-v2 readiness registry previously had `sampling_power_plan = unset`. The correct next step is **not** to choose an arbitrary sample size. The scientific quantities that determine the required number of independent field clusters have not yet been frozen.

`src/interaction_sensing/v15_power.py` therefore implements a parameterized planning contract. It turns explicit scientific inputs into an approximate cluster requirement while refusing to infer those inputs from held-out results.

## Replication unit

Frames are not independent biological replicates. Analysis windows within the same recording context are also correlated.

Every frozen plan must name its cluster unit explicitly. The intended field concept is a genuinely independent capture block such as:

```text
recording day × focal scene/flower
```

or another predeclared unit justified before held-out scoring.

The current calculation uses the equal-cluster design effect:

```text
DE = 1 + (m - 1) × ICC
```

where `m` is mean evaluable windows per cluster and `ICC` is the intracluster correlation.

## Two development calculations

### 1. Precision planning

For a binary metric such as visit recall or unobservable recall, the planner accepts a target confidence half-width.

If an expected rate is available from development-only evidence, it can be supplied explicitly. If it is not available, the function uses `p=0.5` **only as the mathematical worst-case Bernoulli variance**, not as an empirical guess.

The independent-window normal approximation is then inflated by the cluster design effect and divided by mean windows per cluster.

### 2. System-comparison power

For a binary comparison endpoint the planner requires:

- baseline rate;
- alternative rate;
- effect direction;
- minimum effect of scientific interest (MESI);
- alpha;
- target power;
- cluster size and ICC.

The planned effect must be at least the declared MESI.

The current v1 calculation deliberately uses the independent-proportions normal approximation before cluster inflation. The actual V15 systems are evaluated on the same windows, so a positive paired correlation could improve efficiency. **No pairing gain is assumed** until development-only evidence supports and freezes a paired model.

This makes v1 a conservative planning baseline rather than a final inferential model.

## Inputs that remain scientifically unresolved

This implementation does not decide:

- which V15 endpoint is primary;
- the numerical MESI;
- the expected development baseline rate;
- the field ICC;
- the final mean evaluable windows per independent cluster;
- alpha or target power for the final claim family;
- the final held-out cluster count.

Those values must be committed before held-out scoring. The planner exists so that the final N follows mechanically from the frozen inputs rather than being selected by convenience or result inspection.

## Readiness consequence

With this module and `benchmarks/v15_cluster_power_plan_v1_contract.json`, `sampling_power_plan` moves from:

```text
unset -> development_defined
```

It does **not** become `frozen`.

At this point the only core readiness item still explicitly `unset` is `claim_thresholds`; the overall gate remains `BLOCKED_SAFE` because every development-defined item still needs a true pre-held-out freeze and the absence strategy remains undecided.

## Claim boundary

No numerical power result, final sample size, or field performance claim is made by this development planning module.
