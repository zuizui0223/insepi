# V6 observer-portfolio allocation

## Why V6 is a new method generation

Locked V5 falsified the fixed scalar disagreement allocator. The failure was not
that PolliPi and InsePi lacked complementary information: complementary signals
remained across multiple disturbance families. The failed claim was narrower:

> a single fixed scalar ranking of independent-observer disagreement is robust
> enough to allocate finite sensing effort under prevalence shift.

V6 therefore does **not** retune the old `allocation_score()`. It changes the
allocation policy class.

## Policy architecture

For a total audit/capture budget `B`, V6 partitions the budget into four quotas:

```text
B = B_exploration + B_pollipi + B_insepi + B_disagreement
```

The arms remain separate:

1. **uniform exploration** — unbiased windows, with a strictly positive floor;
2. **PolliPi evidence** — strong/uncertain biological-candidate evidence;
3. **InsePi observability** — false/missed/attribution risk;
4. **structured disagreement** — conflict-specific audit cases.

Each arm ranks windows only within that arm. There is no global scalar score.
Targeted arms are interleaved with independent quotas. If a targeted arm has no
positive unique candidates left, its unused quota spills to uniform exploration
rather than being reassigned to another targeted observer.

This design directly addresses the V5 failure mode in which one scalar ranking
could concentrate nearly all selected effort in a narrow disturbance subset.

## Hard invariants

V6 must satisfy all of the following:

- exploration weight is strictly positive;
- the allocator satisfies the exact budget;
- allocation never reads latent `true_visit`, true disturbance labels, or V5
  outcome labels;
- PolliPi and InsePi remain separately executable;
- disagreement is one portfolio arm, not the central decision variable;
- V5 method code and V5 evidence remain frozen;
- V6 fitting may use only explicitly designated development/calibration worlds.

The test suite includes a counterfactual check: flipping every latent
`true_visit` value while holding emitted observer outputs constant must not change
which windows V6 selects.

## Development-only weight fitting

`fit_minimax_portfolio()` searches a constrained simplex of portfolio shares.
The default constraint set guarantees:

```text
exploration >= 0.30
PolliPi arm  >= 0.10
InsePi arm   >= 0.10
disagreement >= 0.10
```

Weights are selected on calibration rows only using a lexicographic minimax
objective across explicit prevalence and budget regimes:

1. maximise the worst regime's `min(event recall, hidden-error recall)`;
2. minimise the worst disturbance total-variation distortion;
3. maximise mean joint recall.

This avoids replacing the old hand-fixed scalar with a new arbitrary weighted
sum. Development fitting may use latent truth for *evaluation of candidate
portfolio shares*, but the deployed selector never sees latent truth.

## V6 development grid

The initial development matrix is:

```text
prevalence: 0.10, 0.50, 0.90
budget:     0.10, 0.25, 0.50
```

V4 and any already-inspected V5 output are development evidence only. Neither may
be described as a final untouched validation after V6 development.

## Required baselines

Before method freeze, V6 must be compared against at least:

- uniform sampling;
- PolliPi-only priority;
- InsePi-only audit priority;
- legacy fixed disagreement ranking;
- candidate OR risky;
- candidate AND risky;
- V6 with disagreement arm removed;
- V6 with PolliPi arm removed;
- V6 with InsePi arm removed.

The key question is not whether V6 wins every single metric. It must occupy a
non-dominated region of the event-recovery / hidden-error-recovery / resource-cost
/ sampling-distortion frontier across prevalence and budget changes.

## V7 locked validation

V7 is the next claim-bearing validation generation. It must not be rendered or
inspected until:

1. PolliPi observer code is frozen to an explicit commit;
2. InsePi observer code and V6 allocator are frozen to an explicit commit;
3. portfolio weights and all baselines are frozen;
4. pass/fail criteria are committed;
5. V7 seeds/world manifest are generated deterministically from the frozen
   method commits (or another precommitted non-selectable procedure).

V7 is run once. After first V7 inspection, method code must not be changed for
that claim. If V7 fails, V6 is falsified or its claim ceiling is narrowed; a V8
method change requires a new validation generation.

## Interpretation if V6 succeeds

The intended claim is no longer "disagreement is the best priority score." It is:

> Independent observers provide complementary information, but robust finite-
> budget sensing requires a portfolio that preserves prevalence-agnostic
> exploration while allocating separate quotas to biological evidence,
> observability risk, and structured disagreement.

That claim is deliberately stronger than a benchmark-specific score improvement
and narrower than a claim of field accuracy.
