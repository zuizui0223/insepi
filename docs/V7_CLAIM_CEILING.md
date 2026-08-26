# V7 claim ceiling — interpretation fixed before result inspection

This document maps locked V7 outcomes to the strongest claim the methods paper is
allowed to make. It exists to prevent post-result narrative inflation.

## Claim levels

### Level A — strong standalone allocation-method claim

Allowed only if **all V7 hard-gate rules pass**.

Permitted claim:

> Under finite sensing budgets and unknown event prevalence, an
> exploration-guarded portfolio that preserves independent biological-evidence
> and observability-risk quotas avoids the prevalence-shift collapse of fixed
> scalar prioritisation and improves joint recovery of true events and hidden
> observation errors relative to uniform exploration, while controlling sampling
> distortion.

This is still a simulation-method claim, not a field-accuracy claim.

### Level B — conditional allocation-method claim

Use if mean joint benefit and TV control pass, but at least one prevalence x budget
regime falls below the locked 0.98 joint-ratio floor.

Permitted claim:

> Exploration-guarded dual-observer allocation improves average simulation
> performance but is not prevalence/budget robust; deployment requires explicit
> regime conditions or adaptive estimation not established here.

Do not describe V6 as generally robust.

### Level C — bias-control / safe-exploration claim only

Use if the performance advantage fails but the exploration architecture keeps
selection distortion within the locked TV criterion and prevents the V5-style
concentration failure.

Permitted claim:

> Guaranteed exploration provides a principled bound on adaptive sampling
> distortion and prevents extreme concentration induced by fixed targeted
> ranking, but the tested observer portfolio does not establish a general recovery
> advantage.

The analytical mixture bound may remain a theoretical result.

### Level D — independent-observer diagnostic methodology

Use if allocation benefit fails or a single-arm removal dominates, while the two
independent observers continue to expose complementary failure families.

Permitted claim:

> Maintaining epistemically distinct observation programs and testing their
> contradictions is useful for falsifying allocation assumptions and localising
> observation-process failures, even though the resulting dual-observer allocation
> policy is not superior.

This returns the paper centre to contradiction-guided development rather than
allocation performance.

### Level E — benchmark/falsification paper

Use if observer complementarity itself does not generalise in V7, or provenance /
reproducibility gates fail.

Permitted claim:

> A sequence of locked simulations falsifies progressively stronger adaptive
> sensing hypotheses and identifies the conditions under which apparent gains do
> not generalise.

No best-programming claim is permitted.

## Failure-to-claim mapping

| V7 outcome | Maximum claim level | Interpretation |
| --- | --- | --- |
| all hard rules pass | A | frozen V6 survives locked generalisation |
| any regime joint ratio < 0.98, but mean > 1 and TV passes | B | average gain, no prevalence robustness |
| mean joint <= 1, TV passes | C | exploration/bias control only |
| V6 arm-removal strictly dominates full V6 | D | dual allocation unnecessary; observers may remain diagnostic |
| legacy targeted policy materially exceeds V6 worst-joint robustness | B or C | V6 not best allocator; depends on remaining bias/mean benefit |
| TV > 0.25 | D at most | frozen allocation does not control selection bias sufficiently |
| latent-truth leakage invariant fails | E | evaluation invalid for methodology claim |
| world/trace/provenance hashes diverge | E | reproducibility/parity failure |
| frozen observer complementarity disappears broadly | E or D | depends on whether contradiction still localises reproducible failures |

## Specific handling of disagreement

V7 does **not** test a claim that disagreement itself should receive positive
allocation quota. V5 already falsified fixed scalar disagreement allocation, and
V6 development selected disagreement weight zero.

Therefore:

- V7 success does not rehabilitate direct disagreement allocation;
- V7 failure must not be repaired by adding disagreement quota under the same
  validation generation;
- disagreement may be discussed as a diagnostic and falsification variable if
  supported by the frozen traces.

## Specific handling of observer-arm ablations

If `v6_no_pollipi` strictly dominates full V6, the paper may not claim that both
observer quotas are required for allocation. PolliPi may still be scientifically
useful as a biological-evidence observer or contradiction source.

If `v6_no_insepi` strictly dominates full V6, the paper may not claim that the
observability-risk quota improves allocation. InsePi may still retain value as a
noise/error diagnostic observer.

If neither dominates but one wins individual metrics, the correct conclusion is a
trade-off, not indispensable contribution.

## Field-data boundary

No V7 outcome permits claims about real ecological visit-rate accuracy,
real-world taxa classification accuracy, or field power/storage performance.
Those remain empirical validation questions for subsequent deployment data.

## One-shot interpretation rule

After V7 result inspection, select the highest claim level whose prerequisites are
satisfied. Do not edit this mapping to rescue a preferred conclusion. Any revised
method after V7 becomes a new generation requiring a new validation generation.
