# interaction-sensing / InsePi

## Current purpose

`interaction-sensing` develops an error-aware ecological observation framework that asks a stricter question than ordinary target classification:

> Given a dynamic observation, when is there enough evidence to support a target process, a nuisance process, or neither uniquely enough to justify a forced label?

The current scientific programme has two layers:

```text
V14b/V14c  frozen closed-world theory
    baseline + TARGET / NUISANCE / UNDETERMINED

V15-v2     active pre-data empirical bridge
    T + C + N + O + optional independent A-
```

Target and nuisance are defined positively and are **not complements**. They may coexist. Observability is a separate measurement question; high nuisance is not the same thing as low observability. V15-v2 further separates observation support from biological absence certification.

## Current design principles

1. **Baseline is outside the ternary question.** A resting state is not treated as an undecidable dynamic event.
2. **Target and nuisance are independently positive.** `not target` does not define nuisance, and `not nuisance` does not certify target.
3. **Superposition is legitimate.** Simultaneous target+nuisance evidence is preserved rather than tuned away.
4. **Undetermined is an epistemic output.** It is not a third biological process and is not forced into absence.
5. **No support is weaker than information absence.** V14c calls this `NO_SUPPORTED_EVIDENCE`; proving true information absence requires an independent identifiability/observability test.
6. **Observation support is not absence evidence.** In V15-v2, good `O` means the primary stream is measurable enough to attempt inference; it does not turn low target evidence into biological absence.
7. **Certified target absence requires an independent channel.** V15-v2 represents this as optional `A-` (`TargetAbsenceEvidence`). Its default pre-data state is unavailable.
8. **Operational boundaries are risk contracts, not inherited raw scores.** The frozen V14b nuisance decision uses a family-wise false-certainty budget `alpha = 0.05`.
9. **Development freezes before measurement.** Failed hypotheses and failed generations remain in history rather than being post-hoc repaired.
10. **Dimensionless ratios define the closed-world phase space.** The frozen V14b surface uses `Pi1`–`Pi6` rather than field-specific pixel/time constants.

## Locked V14b result

The frozen target and nuisance observers were measured over:

```text
30,625 Pi coordinates x 6 latent regimes x 32 fresh seeds
= 5,880,000 truth-known closed-world worlds
```

Locked equal-grid/equal-regime state rates:

```text
baseline      0.2302328231
target        0.4287333333
nuisance      0.0876976190
undetermined  0.2533362245
```

Historical V14b U counters were `0.0267528912` for the branch then named `information_absence` and `0.2265833333` for overlap/attribution. V14c weakens the first term to **no supported evidence** because an observer failing to support T or N does not prove that discriminating information was absent from the world.

The main closed-world findings are:

- about 89.4% of U is overlap/attribution rather than no-supported-evidence under the frozen design weighting;
- the originally predicted dominant `Pi2 ~= 1` timescale-collision ridge was **not supported** and remains retired;
- longer `Pi1` does not monotonically erase U because additional observation can reveal coexistence/attribution conflict;
- `Pi3 = 0` versus `Pi3 > 0` is a strong boundary **under the frozen structural target rule** `direct_target_signal_fraction > 0 -> target_supported`; it is not evidence for a universal field SNR discontinuity.

Forcing all non-target outputs to target absence yields zero target false positives in this closed generator but a target false-negative rate of `0.3569` among latent target-present worlds under the frozen uniform weighting.

See:

- `benchmarks/v14b_frozen_ternary_phase_surface_result.json`
- `benchmarks/v14c_semantic_clarification_result.json`
- `docs/V14C_SEMANTIC_CLARIFICATION.md`

## Identification boundary

The frozen target observer is **positive-only**. Therefore `NUISANCE`, `BASELINE`, and `UNDETERMINED` do not certify target absence.

The historical `baseline + U` quantity is retained only as `legacy_non_target_decision_width`, not as strict visit-presence partial identification.

Without an independently validated target-absence channel, the safe output-implied global bounds are:

```text
p(target) in [P(TARGET), 1]
          = [0.4287333333, 1]
```

V15-v2 does not silently tighten this bound. Its default `TargetAbsenceEvidence.unavailable()` means:

```text
O = observable + low/zero target evidence
!= certified absence
=> unresolved unless independent A- supports absence
```

A future empirical generation may tighten the upper bound only through a genuinely independent validated `A-` channel or an explicit sampling/missingness model.

## PolliPi relationship

PolliPi is the target-evidence side of the cross-repository architecture. Its current main branch exports an ordinal target-evidence adapter without asserting nuisance truth, observability, confirmed visitation, or biological absence.

Important boundary:

- PolliPi evidence `0 / 0.5 / 1` is **not** V14b `Pi3`;
- PolliPi `environmental_noise` means target evidence was not retained strongly enough by that observer, not that nuisance truth was established;
- low PolliPi evidence is not an `A-` absence channel;
- the 5.88M-world V14b result is a synthetic closed-world InsePi result, not a field validation of the current PolliPi classifier.

## Empirical bridge: V13 and V15-v2

The closed-world V14b/V14c result is not a field accuracy claim.

- **V13** remains a result-pending physical intervention protocol. Its active GitHub Action is manual-only; historical V13 workflow YAML is preserved as provenance.
- **V15-v2** is the active pre-data real visit-observation bridge. It separates:
  - `T`: positive direct target evidence;
  - `C`: positive target-coupled response evidence;
  - `N`: positive exogenous nuisance evidence;
  - `O`: primary-stream observation support;
  - `A-`: optional independently validated target-absence evidence.

The full V15 system uses the process-preserving V14b policy, so observable high target + high nuisance evidence remains target-positive with nuisance audit rather than being forced into an exclusive conflict state.

Naive binary comparators are retained only to measure the cost of forced decisions. Their low-score negatives are recorded as `forced_absence_call`, not certified negative evidence.

Normative V15-v2 files:

- `benchmarks/v15_empirical_bridge_v2_contract.json`
- `docs/V15_EMPIRICAL_BRIDGE_V2.md`
- `src/interaction_sensing/target_absence.py`
- `src/interaction_sensing/v15.py`

## Repository structure

- `src/interaction_sensing/` — current and historical sensing contracts, observers, decision layers, simulations, and evaluation utilities.
- `benchmarks/` — frozen protocols, receipts, result summaries, and current pre-data contracts.
- `docs/` — method development, negative results, frozen-generation reports, and current V14/V15 interpretation.
- `scripts/` — reproducible generation/evaluation helpers for the corresponding protocols.
- `tests/` — normal package and scientific-contract tests.
- `provenance/frozen_github_workflows/` — byte-preserved generation-specific workflow YAML removed from active GitHub Actions after its scientific generation was frozen.
- `legacy/` — earlier prototype/runtime material retained for provenance and baselines.

Earlier NoiseBench, noise-source, portfolio, design-inference, real-pixel, causal-intervention, and physical-validation generations remain part of the evidence history. They should not be mistaken for the current V14b ontology or V15-v2 empirical bridge simply because their code remains importable.

## Active CI

Generic pull requests run only the normal unit/contract test workflow:

```text
.github/workflows/test.yml
```

The only active generation-specific workflow is:

```text
.github/workflows/v13-manual-preflight.yml
```

and it is `workflow_dispatch` only. Frozen V6–V14b scientific workflows are preserved under `provenance/frozen_github_workflows/` and cannot re-run merely because a future PR touches historical files.

## Quick start

```bash
python -m pip install -e ".[runtime,analysis,dev]"
pytest
```

V15-v2 has a dedicated public facade:

```python
import interaction_sensing.v15 as v15
```

## Claim boundary

V14b/V14c conclusions are **closed-world, frozen-observer statements**. V15-v2 is **pre-data empirical design/software**, not a field result. The repository currently does not establish field visitation accuracy, calibrated field observability, a validated target-absence channel, field prevalence, a calibrated PolliPi probability, a universal physical transition point, or universal superiority of the full T/C/N/O/A- architecture.
