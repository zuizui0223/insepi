# Figure and table production plan

The main-text figures should tell the falsification story before they display the
final candidate. Do not lead with V6 as though it had been the original hypothesis.

## Figure 1 — Two observation questions, one sensor stream

**Purpose:** establish the conceptual method before implementation details.

Panels:

- **A. Raw observation stream.** One ecological scene feeds two independently
  executable programs.
- **B. Biological-evidence axis.** PolliPi-like observer asks whether local evidence
  supports a candidate event.
- **C. Observability axis.** InsePi-like observer asks whether false-event,
  missed-event or attribution risk makes the window difficult to interpret.
- **D. Same pixels, separate traces.** Hidden truth is inaccessible during observer
  decisions and used only downstream for simulation scoring.
- **E. Contradiction categories.** supported candidate; supported absence;
  candidate under confounding; suppression versus audit risk; possible miss under
  unobservable conditions.

Main visual rule: **no arrow from disagreement directly to acquisition**. Show
contradiction first as a development/falsification channel.

## Figure 2 — Method generations and explicit falsification

**Purpose:** make the paper visibly non-post-hoc.

Horizontal sequence:

```text
V1 policy contradictions
  -> V2 identical pixels
  -> V3 disagreement allocation: negative
  -> V4 observer diagnosis/development
  -> V5 scalar disagreement: LOCKED FAIL
  -> V6 policy-class change + exploration guard
  -> V7 one-shot locked challenge
```

For each generation show:

- hypothesis;
- whether data were development or locked;
- pass/fail;
- what was allowed to change next.

Highlight V3 and V5 in the same visual weight as positive development stages.

## Figure 3 — V5 falsification surface

**Purpose:** headline negative-result figure.

Layout: 3 × 3 prevalence-by-budget grid for fixed scalar disagreement.

For each cell show:

- Pareto membership;
- joint event/error performance relative to uniform;
- dominant/competing policy if the candidate failed;
- disturbance TV.

Annotations required:

- rare 10% and 25%: outside frontier / beaten by single-view removal;
- common 25%: InsePi-only higher hidden-error recall;
- 10% budget: show the extreme TV ≈ .833 concentration case;
- only balanced 25% satisfies the complete fixed-disagreement gate.

Side panel: complementary observer signals remain in 6–7 disturbance families,
visually separating “observer complementarity survives” from “allocation fails”.

## Figure 4 — Failure localisation and policy-class change

**Purpose:** explain why V6 is not retuning V5.

Left:

```text
PolliPi evidence -----\
                       > fixed allocation_score -> one ranking -> prevalence-sensitive concentration
InsePi risk ----------/
```

Cross out the scalar seam, not either observer.

Right:

```text
                ┌ uniform exploration (guaranteed)
finite budget ──┼ biological-evidence quota
                └ observability-risk quota

disagreement -> diagnostic/falsification channel only
```

Include exact quota spillover rule: exhausted targeted quota returns to uniform
exploration, not another targeted arm.

## Figure 5 — V6 candidate frontier and analytical guard

**Purpose:** show both empirical development and transferable theory.

Panel A: focused candidates U40/P10/I50, U50/P10/I40, U60/P10/I30,
U70/P10/I20 plotted in coordinates:

- x = max TV (lower is better);
- y = worst joint ratio (higher is better);
- point size or label = mean joint ratio.

Draw locked development boundaries at worst joint=1 and TV=.25. Mark U50 as
frozen and U60 as a passing alternative, making selection sensitivity transparent.

Panel B: exploration mixture diagram `Q = αU + (1−α)R`.

Panel C: three guarantees:

- exact TV contraction;
- support/coverage lower bound;
- importance-ratio upper bound.

Do not use language such as “optimal”.

## Figure 6 — Locked V7 outcome

**Status:** DO NOT BUILD FROM A FINAL V7 WORLD BEFORE ONE-SHOT EXECUTION.

Template only:

- columns = prevalence .1/.5/.9;
- x-axis = budgets .1/.25/.5;
- ratio-to-uniform panels for event and PolliPi-relative hidden-error recall;
- TV panel;
- frozen V6, arm removals, uniform and legacy baselines;
- secondary observer-independent disturbance coverage panel;
- final claim-level badge A–E generated from the execution ledger.

Every number must be read from the immutable V7 report.

---

# Main tables

## Table 1 — Observer contracts

Columns:

1. observer role;
2. scientific question;
3. input;
4. primary output;
5. acquisition interpretation;
6. characteristic failure;
7. forbidden interpretation.

Rows:

- biological-evidence observer;
- observability-risk observer.

## Table 2 — Generational evidence ledger

Columns:

- generation;
- hypothesis;
- shared input level;
- development vs locked;
- primary result;
- permitted next change;
- evidence identifier/hash.

This table should contain V1–V7 and is the easiest place for reviewers to audit
benchmark reuse.

## Table 3 — V7 hard rules and claim consequences

Columns:

- rule;
- threshold;
- scientific reason;
- failure interpretation;
- maximum claim level.

Use `V7_CLAIM_CEILING.md` exactly. Do not revise after V7.

---

# Supplementary package

## Figure S1 — Complete V2 same-pixel state matrix

Rows = scenarios; columns = PolliPi state, InsePi state/risk, latent event,
contradiction category.

## Figure S2 — V4 family-level observer performance

Show PolliPi candidate recovery and InsePi disturbance-risk recall separately,
including the retained lens OOD miss.

## Figure S3 — V6 development search history

Show forced four-arm, sparse, arm-removal, single-arm screens and focused
high-resolution candidates. This documents that direct disagreement went to zero
rather than being manually deleted after the fact.

## Figure S4 — Selection-distribution distortion

Compare full disturbance distributions with samples from uniform, single-observer,
legacy disagreement and frozen V6 at each budget.

## Figure S5 — Generic guarded-portfolio parity

Demonstrate exact selection parity between the frozen PolliPi/InsePi wiring and the
generic evidence/observability reference API on representative test worlds.

## Table S1 — Complete scenario/disturbance registry

List V1/V2/V4 development conditions and the seed-independent V7 family contract.
Do not include final V7 seeds before execution.

## Table S2 — All V5 policy metrics

Include all policies and all prevalence × budget regimes, not only failures
mentioned in the main text.

## Table S3 — V6 candidate weights considered

Preserve every candidate family that influenced method selection. Separate
screening results from high-resolution focused comparison.

## Table S4 — Reproducibility ledger

Include:

- method commits;
- generator commit;
- allocator commit;
- evaluator/materializer commits;
- world-spec hashes;
- baseline hash;
- V5 evidence hashes;
- V7 artifact/trace/report hashes after execution;
- unit-test counts and CI run identifiers.

---

# Production order

Before V7, figures 1–5 and Tables 1–3 can be prepared from frozen/development
evidence. Figure 6 and V7 rows in supplementary outputs remain templates only.

Recommended production sequence:

1. Figure 2 generation timeline;
2. Figure 3 V5 falsification surface;
3. Figure 4 failure localisation;
4. Figure 5 V6 + theorem;
5. Figure 1 conceptual overview;
6. V7 only after the immutable ledger exists.

This order prioritises the scientific argument over decorative architecture.
