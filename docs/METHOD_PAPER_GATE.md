# Method-paper gate: exploration-guarded dual-observer ecological sensing

## Current submission hypothesis

The pre-empirical paper must not claim field accuracy. After the locked V5
falsification and V6 development, the current standalone methodological
hypothesis is:

> Ecological sensing under finite budgets can be made more robust to unknown
> event prevalence by keeping biological-evidence and observability-risk
> observers independent, guaranteeing a substantial uniform-exploration quota,
> and allocating separate observer-specific exploitation quotas rather than
> collapsing their outputs into one fixed scalar priority.

The frozen V6 candidate is:

```text
50% uniform exploration
10% PolliPi biological-evidence priority
40% InsePi observability-risk priority
 0% direct disagreement priority
```

Disagreement remains central to the **development method**—it exposed conflicting
assumptions and localised the failed allocation seam—but V5/V6 evidence does not
support using disagreement itself as a direct allocation quota.

## G1 — Independent implementations

- PolliPi and InsePi remain separately executable.
- Neither imports the other's decision logic.
- Common material is benchmark/world contracts and emitted traces.
- Agreement is never a tuning target.

**Status: PASS for the development architecture.**

## G2 — Pixel/provenance parity

- identical benchmark worlds have cross-repository fingerprints;
- observer decisions are generated independently from the same pixels;
- emitted traces carry source provenance;
- allocation consumes emitted observer outputs, not the sibling implementation.

**Status: PASS for V2/V4 development infrastructure.**

## G3 — Broad simulation coverage

Development evidence covers event presence/absence, wind, camera displacement,
shadow/illumination change, occlusion, blur, clutter, mixed disturbances,
intensity shifts and OOD lens contamination. Prevalence and sensing budget are
also varied explicitly.

**Status: PASS as development coverage.** V4 was inspected repeatedly and is not
claim-bearing final validation.

## G4 — Equal-budget competition and falsification

### V3

The first equal-budget comparison showed that fixed disagreement priority did not
beat uniform/InsePi hidden-error recovery. This was retained as a negative result.

### Locked V5

The user-reported one-shot V5 contained 180 conditions, three prevalence regimes,
three budgets, eight policies, 4,800 windows and 200 replicates. It **failed** its
pre-registered strong disagreement-allocation gate. Only balanced prevalence at
25% budget satisfied all reported conditions; rare/common regimes exposed
prevalence sensitivity and selection distortion.

The important retained result is that complementary observer signal still existed
across multiple disturbance families. V5 therefore falsified the scalar
allocation claim rather than observer independence itself.

**Status: fixed scalar disagreement allocation REJECTED.**

## G5 — V6 new policy generation

V6 changed the policy class instead of retuning V5:

- exact-budget quota allocation;
- a guaranteed positive uniform-exploration share;
- separate PolliPi and InsePi exploitation rankings;
- targeted-arm spillover returns to exploration;
- allocation is invariant to latent truth when observer outputs are held fixed;
- fitting compares candidates on shared sampled worlds;
- sparse fitting may remove an unnecessary arm.

High-resolution V4 development used 4,800 windows × 200 paired replicates across
three prevalence regimes and three budgets. The frozen candidate
`E=.50/P=.10/I=.40/D=0` achieved:

- worst paired joint event/error ratio to uniform: **1.00846**;
- mean joint ratio: **1.11642**;
- maximum disturbance-family TV: **0.21919**;
- regimes with both recovery ratios at/above uniform: **9/9**.

The nearby alternatives reveal a real trade-off rather than a flat optimum:

- E40/P10/I50 failed the TV ceiling (0.26567);
- E60/P10/I30 also passed but had lower worst/mean joint benefit;
- E70/P10/I20 lost hidden-error robustness at common prevalence.

**Status: V6 METHOD FROZEN FOR FUTURE VALIDATION.**
Allocator implementation commit:
`a8ac75991ab28fd74a3f3a5482304a2b127a97bc`.

## G6 — Exploration guarantee

V6 gives the uniform component a structural role. If an `alpha` fraction of
selected effort is uniform, the expected selected distribution satisfies

```text
Q = alpha U + (1-alpha)R
TV(Q,U) <= 1-alpha.
```

With frozen `alpha=.50`, V6 has a nontrivial analytical bound on selection bias in
addition to the empirical V4 development TV result. This theory directly targets
the V5 low-budget concentration failure.

**Status: IMPLEMENTED and unit-tested.**

## G7 — Ablations

Development comparisons include:

- uniform;
- PolliPi-only;
- InsePi-only;
- legacy scalar disagreement;
- OR;
- AND;
- forced four-arm portfolio;
- sparse portfolio;
- single-arm portfolios;
- PolliPi/InsePi/disagreement arm removals.

Arm-removal results were used diagnostically. They were not hidden when they made
simpler candidates look competitive.

**Status: STRONG FOR DEVELOPMENT; must be repeated in V7 with frozen rules.**

## G8 — Reproducibility ledger

Current public development evidence records:

- V4 world fingerprint
  `10e38358499b79829876752986492c6a69b3ab15ec7b6756e6ae7ad75b314193`;
- PolliPi V4 emitted-trace source commit
  `5541201b376689c32aaabeafbc8e7e9592150d23`;
- V6 allocator implementation commit
  `a8ac75991ab28fd74a3f3a5482304a2b127a97bc`;
- machine-readable V6 freeze manifest `benchmarks/v6_method_freeze.json`;
- frozen method note `docs/V6_METHOD_FREEZE.md`.

The user-reported frozen V5 method commits/hashes are recorded in
`docs/V5_FALSIFICATION_LEDGER.md`, but those local method commits are not currently
resolvable from the public GitHub repositories.

**Status: V6 public development reproducibility strong; V5/V7 final chain still
has a materialisation blocker.**

## What the development programme has falsified

The increasingly narrow falsification sequence is itself a result:

1. disagreement is not automatically useful just because two observers differ;
2. even when disagreement predicts real error mechanisms, a fixed scalar ranking
   can induce severe prevalence-dependent sampling distortion;
3. forcing every observer-derived signal to receive allocation budget is also
   unnecessary;
4. the best current development candidate preserves observer independence but
   uses disagreement diagnostically rather than as direct allocation.

This makes the method paper stronger than a simple winner-picking benchmark: the
architecture is being selected by explicit failed hypotheses.

## Final locked validation: V7

V7 is a new no-peek generation. The protocol is committed in
`docs/V7_LOCKED_VALIDATION_PROTOCOL.md`.

The strong V6 claim may be made only if locked V7 satisfies all pre-registered
rules, including:

- no core prevalence × budget regime with joint ratio below 0.98 to uniform;
- mean joint ratio >1.00;
- max disturbance TV <=0.25;
- worst-case robustness competitive with all frozen legacy baselines;
- neither PolliPi-arm nor InsePi-arm removal strictly dominates full V6;
- no truth leakage;
- full source/trace/report hashes preserved.

V7 is run once. Failure lowers the claim ceiling; it does not trigger tuning under
the same validation generation.

## Manuscript structure if V7 passes

1. **Observation problem:** biological process and observation process are not
   the same state variable.
2. **Independent observers:** PolliPi evidence vs InsePi observability.
3. **Contradictory development framework:** disagreement as diagnostic evidence.
4. **Falsification sequence:** V3 and locked V5 failures of scalar allocation.
5. **V6 method:** exploration-guarded dual-observer portfolio and TV guarantee.
6. **Development evidence:** V4 high-resolution stress tests and ablations.
7. **Locked V7 validation:** prevalence/budget robustness and baseline comparison.
8. **Scope:** no field-accuracy claim; empirical deployment is external validation.

## Current paper-readiness decision

**Not submission-ready yet.**

The method candidate is now frozen and the methods-paper story is coherent, but
claim-bearing validation has not been run. V7 remains **BLOCKED** because the
user-reported V5 frozen observer commits/evidence are local/unpushed and the final
V7 observer/generator/baseline provenance cannot yet be made fully reproducible.
No V7 seed or world has been generated.
