# Frozen V5 falsification ledger

This document records the locked V5 result that motivated the V6 generation.
The method commits named below were reported as frozen local commits and are not
resolvable from the public GitHub branch at the time this V6 branch was created.
Accordingly, this file is a provenance/claim-boundary record, not a substitute
for publishing the underlying locked V5 artifacts.

## Frozen identifiers

- PolliPi method: `d58d0a86034a6c2d53f90efbe4245370fd7cd2e9`
- InsePi method: `980813bab996909020140fad5bd83b055eb3db9c`
- V5 world fingerprint: `9a604a9646efbfaba8e123e0adc58d0f7a82993eec2ab5d56ede8fea5fa4f8b5`
- PolliPi trace SHA-256: `56ec4de0b710273ee47e500d6b1d7f92c50ba40274619528f857e133633385c0`
- Cross-report SHA-256: `a6d1f30b3d18707e83cb5d0d5f60581d06fdf42f7bbe485fb0992079f3ce495e`
- reported PolliPi tests: 104 passed
- reported InsePi tests: 66 passed

The reported V5 rule was that method code was not changed after V5 inspection.
V6 therefore exists as a separate method generation and must not overwrite or
reinterpret V5 as if it were a calibration run.

## V5 design reported at freeze

- 180 conditions
- three event-prevalence regimes
- three sensing budgets
- eight policies
- 4,800 windows per run
- 200 replicates

## Locked result

The fixed scalar disagreement allocation failed its pre-registered one-shot V5
gate, with ten failed items. Only balanced prevalence at the 25% budget passed all
of the reported conditions.

Important failures included:

- rare prevalence at 10% and 25% was outside the Pareto frontier and lost to a
  single-view removal;
- at common prevalence and 25% budget, InsePi-only achieved higher hidden-error
  recall;
- at 10% budget, disturbance-distribution total-variation distortion reached
  approximately 0.833 in some settings.

At the same time, complementary observer signals were still present in roughly
six to seven disturbance families per prevalence regime.

## Claim that V5 falsified

V5 did **not** falsify the usefulness of independent biological-evidence and
observability observers. It falsified the stronger allocation claim:

> Collapsing independent-observer disagreement into one fixed scalar ranking is
> sufficient to create a prevalence-robust finite-budget allocation policy.

The failure was reported to localise at the `allocation_score()` seam rather than
at independent-observer parity or the falsification gate.

## Consequence for V6

V6 must not tune the scalar disagreement weights against V5. It changes policy
class instead:

- preserve independent observers;
- retain disagreement as one information channel;
- guarantee non-zero uniform exploration;
- allocate separate quotas to multiple observer arms;
- fit portfolio shares only on explicitly designated development/calibration
  worlds;
- require a new locked validation generation (V7) after V6 method freeze.

## Publication ceiling

Until the frozen local V5 commits and artifacts are published or independently
materialised, V5-specific hashes and counts should be described as externally
frozen evidence rather than as reproducible outputs of this public V6 branch.
The V6 branch must never silently regenerate or modify V5 and then reuse the V5
label.
