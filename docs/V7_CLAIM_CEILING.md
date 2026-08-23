# V7 claim ceiling — interpretation fixed before result inspection

This document maps a **valid locked V7 scientific execution** to the strongest
claim the methods paper is allowed to make. It exists to prevent post-result
narrative inflation. The machine-readable mapping is frozen in
`benchmarks/v7_claim_mapping_freeze.json` and implemented by
`scripts/v7_evaluate_locked.py::_claim_level`.

A runtime, provenance, trace, artifact, hash or truth-boundary failure is **not a
scientific negative result**. It invalidates the V7 execution, the workflow fails
closed, and **no V7 claim level is assigned**. This is intentionally separate from
levels A–D below.

## Valid scientific claim levels

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

Use when TV control and mean joint benefit remain favorable but at least one
locked robustness rule prevents claim A, for example a prevalence × budget regime
below the 0.98 joint-ratio floor or a legacy comparator with materially better
worst-joint robustness.

Permitted claim:

> Exploration-guarded dual-observer allocation improves average simulation
> performance but is not fully robust across the tested prevalence/budget regimes;
> deployment therefore requires explicit regime conditions or adaptive estimation
> not established here.

Do not describe V6 as generally robust.

### Level C — bias-control / safe-exploration claim only

Use if the general performance advantage fails while the frozen portfolio remains
within the TV ceiling and the mean joint ratio is not above uniform.

Permitted claim:

> Guaranteed exploration provides a principled bound on adaptive sampling
> distortion and prevents extreme concentration induced by fixed targeted
> ranking, but the tested observer portfolio does not establish a general recovery
> advantage.

The analytical mixture and finite-budget guarantees remain theoretical results.

### Level D — diagnostic / negative locked validation

Use if a single-arm removal strictly dominates full V6, the TV ceiling is
violated, or a remaining valid-execution failure pattern does not support A–C.

Permitted claim:

> The locked validation does not support superior dual-observer allocation. The
> defensible contribution is contradiction-guided development, explicit sampling
> safeguards, and a reproducible negative validation that localises where the
> stronger allocation claim failed.

If the frozen traces still show interpretable observer contrasts, they may be
discussed diagnostically. V7 does **not** contain a preregistered quantitative
threshold that would justify a separate claim level based on “observer
complementarity disappearance.”

## Invalid execution — no claim level

The following are execution-integrity failures rather than scientific outcomes:

- latent-truth / decision-input boundary failure;
- frozen runtime mismatch;
- world, pixel, trace, registry or provenance hash mismatch;
- wrong frozen observer commit or scientific implementation drift;
- runtime captured after seed/pixels/observer output;
- any other fail-closed condition that prevents a valid locked report/ledger.

In those cases **do not assign A, B, C or D** and do not manufacture a
“benchmark/falsification” claim from invalid evidence. Correct the execution
infrastructure only if doing so does not alter the frozen scientific generation;
otherwise start a new validation generation.

## Executable precedence

The pre-result mapping is:

1. hard gate passes → **A**;
2. arm-removal strict dominance or `max TV > 0.25` → **D**;
3. `max TV <= 0.25` and mean joint ratio `<= 1.0` → **C**;
4. `max TV <= 0.25`, mean joint ratio `> 1.0`, with regime-floor or legacy
   worst-joint failure → **B**;
5. any remaining valid-execution failure → **D**.

This matches `scripts/v7_evaluate_locked.py::_claim_level` exactly. The frozen
scientific evaluator itself remains unchanged at
`6860fa973ce8f25b25028f49723710e8a920709c`.

## Failure-to-claim mapping

| V7 outcome | Maximum claim | Interpretation |
| --- | --- | --- |
| all hard rules pass | A | frozen V6 survives locked generalisation |
| any regime joint ratio < 0.98, mean > 1 and TV passes | B | average gain, no full prevalence/budget robustness |
| legacy targeted comparator materially exceeds V6 worst-joint robustness, mean > 1 and TV passes | B | V6 is not the strongest tested allocator |
| mean joint <= 1 and TV passes | C | exploration/bias-control claim only |
| V6 arm-removal strictly dominates full V6 | D | full dual allocation unnecessary under locked test |
| TV > 0.25 | D | frozen allocation fails its sampling-distortion ceiling |
| other valid-execution hard-gate failure | D | negative locked validation / diagnostic framing |
| runtime / truth-boundary / provenance / hash failure | **no claim** | invalid V7 execution; fail closed |

## Specific handling of disagreement

V7 does **not** test a claim that disagreement itself should receive positive
allocation quota. V5 already falsified fixed scalar disagreement allocation, and
V6 development selected disagreement weight zero.

Therefore:

- V7 success does not rehabilitate direct disagreement allocation;
- V7 failure must not be repaired by adding disagreement quota under the same
  validation generation;
- disagreement may be discussed as a diagnostic and falsification variable if
  supported by valid frozen traces.

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

After a **valid** V7 result is produced, select the claim level mechanically from
the frozen A–D mapping. Do not edit this mapping to rescue a preferred conclusion.
Any revised method after V7 becomes a new generation requiring a new validation
generation.
