# PR stack and provenance-preserving merge order

This document is an integration contract for the PolliPi/InsePi methods-paper stack. It is not scientific evidence and does not alter V6/V7 logic.

## Why merge strategy matters

Several scientific claims and reproducibility ledgers refer to exact commit SHAs. A squash merge or rebase rewrites ancestry and can make those SHAs harder to preserve as part of the integrated history. For this stack, use **merge commits** rather than squash/rebase when integrating the scientific generations.

Do not merge any part of the stack merely to unblock V7. The exact frozen V5 observer objects must first be recovered unchanged as `frozen/v5-method` in their own repositories, and the one-shot V7 result must be preserved before the final publication stack is integrated.

## Current stack

### PolliPi

1. PR #57 — historical V1–V5 biological-observer benchmark and emitted-trace evidence
   - base: `main`
   - head: `feature/contradiction-sim-v1`
2. PR #58 — thin canonical V7 pixel-artifact adapter
   - base: `feature/contradiction-sim-v1`
   - head: `feature/v7-locked-artifact-adapter`

### InsePi

1. PR #20 — historical V1–V5 disagreement benchmark; scalar-allocation hypothesis falsified
   - base: `main`
   - head: `feature/contradiction-sim-v1`
2. PR #21 — frozen V6 exploration-guarded portfolio + V7 one-shot infrastructure
   - base: `feature/contradiction-sim-v1`
   - head: `feature/observer-portfolio-v6`
3. PR #22 — deterministic pre-V7 Main Figures 1–5
   - base: `feature/observer-portfolio-v6`
   - head: `feature/method-paper-figures`
4. PR #23 — MEE manuscript/SI/anonymisation/finalization/release packaging
   - base: `feature/method-paper-figures`
   - head: `feature/mee-submission-package`

## Preconditions before integration

All of the following must be true:

- PolliPi `frozen/v5-method` points exactly to `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`.
- InsePi `frozen/v5-method` points exactly to `980813bab996909020140fad5bd83b055eb3db9c`.
- V7 one-shot has executed once from the READY lock and emitted the immutable evidence ledger/report.
- The downstream publication finalizer has consumed that exact V7 run and produced its finalization receipt.
- No V6 observer/allocation scientific code was modified after its freeze boundary.
- Required CI is green on the heads being integrated.

The software-licence choice can be completed before submission, but it is not a reason to alter the scientific merge order.

## Provenance-preserving integration order

### PolliPi

1. Merge PR #57 into `main` using **merge commit**.
2. Retarget PR #58 from `feature/contradiction-sim-v1` to `main`.
3. Inspect the retargeted diff: it should contain only the thin V7 artifact adapter/test layer relative to the newly integrated benchmark base.
4. Re-run required PolliPi CI.
5. Merge PR #58 into `main` using **merge commit**.

### InsePi

1. Merge PR #20 into `main` using **merge commit**.
2. Retarget PR #21 from `feature/contradiction-sim-v1` to `main`; inspect the diff and re-run CI.
3. Merge PR #21 into `main` using **merge commit**.
4. Retarget PR #22 from `feature/observer-portfolio-v6` to `main`; verify that the diff is publication-figure code/evidence only, then re-run CI.
5. Merge PR #22 into `main` using **merge commit**.
6. Retarget PR #23 from `feature/method-paper-figures` to `main`; verify that there are zero scientific-method changes under `src/interaction_sensing/...`, then re-run full unit + MEE packaging CI.
7. Merge PR #23 into `main` using **merge commit** only after the final V7 publication transform and release package have been preserved.

## Required checks after each retarget

- `mergeable=true`.
- No unexpected files appear because of the new base.
- Exact frozen scientific SHAs referenced in ledgers/docs remain resolvable.
- No result-dependent text is regenerated from development data.
- V7 report/ledger/finalization hashes remain unchanged.

## Do not do

- Do not squash or rebase scientific-generation PRs.
- Do not cherry-pick frozen scientific commits into a new generation and call them the same freeze.
- Do not delete `frozen/v5-method` until archival provenance is permanently secured elsewhere.
- Do not rerun V7 because integration changed branches; the preserved one-shot result remains the scientific result.
- Do not edit claim wording after V7 outside the preregistered claim ceiling/finalizer.

## Final release checkpoint

After both repositories are integrated, verify the release checklist, create the immutable release/tag/archive, record DOI/version identifiers, and update the final Data/Code Availability statement without changing the scientific result.