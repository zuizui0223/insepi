# Repository overview

This page points to the **current scientific state** of `interaction-sensing`. Historical modules remain in the repository for reproducibility. The active programme is now:

```text
V14b/V14c  frozen closed-world theory
V15-v2     active pre-data empirical bridge
```

## Current scientific object

The frozen V14 layer studies when a dynamic ecological observation can safely support one of three deviation-side conclusions:

```text
TARGET / NUISANCE / UNDETERMINED
```

with a separate baseline state outside the dynamic query.

Target and nuisance are positively defined and may coexist. `UNDETERMINED` is an epistemic decision region, not a biological process. V14c further separates:

- `NO_SUPPORTED_EVIDENCE` — neither frozen observer supports a safe conclusion; this does **not** by itself prove true information absence;
- overlap / attribution unresolved — evidence exists, but coexistence or attribution prevents a unique exclusive label.

Observability remains a separate measurement axis and must not be equated with `1 - nuisance`.

V15-v2 carries that boundary into empirical validation by separating:

```text
T   positive direct target evidence
C   positive target-coupled response evidence
N   positive exogenous nuisance evidence
O   primary-stream observation support
A-  optional independently validated target-absence evidence
```

`O` does not certify `A-`. Low target evidence under good observation support remains unresolved unless an independent absence channel supports the negative claim.

## Current frozen result

V14b freezes both observers before measurement and evaluates 30,625 dimensionless coordinates × 6 latent regimes × 32 fresh seeds = **5,880,000 closed-world worlds**.

Equal-grid/equal-regime output rates:

| State | Rate |
|---|---:|
| baseline | 0.2302328231 |
| target | 0.4287333333 |
| nuisance | 0.0876976190 |
| undetermined | 0.2533362245 |

About 89.4% of U is overlap/attribution rather than the historical no-support counter. The proposed dominant `Pi2 ~= 1` ambiguity ridge is not supported. The strongest visible boundary is `Pi3 = 0` versus `Pi3 > 0`, but V14c explicitly bounds that conclusion to the frozen structural rule `direct_target_signal_fraction > 0 -> target_supported`; it is not a field SNR threshold.

Key frozen files:

- `benchmarks/v14b_frozen_ternary_phase_surface_result.json`
- `benchmarks/v14b_frozen_ternary_phase_figure_data.json`
- `benchmarks/v14c_semantic_clarification_result.json`
- `docs/V14C_SEMANTIC_CLARIFICATION.md`
- `src/interaction_sensing/target_observer_v14b.py`
- `src/interaction_sensing/nuisance_observer_v14b.py`
- `src/interaction_sensing/ternary_decision_v14b.py`
- `src/interaction_sensing/ternary_semantics_v14c.py`

## Identification boundary

The current target observer is positive-only. Therefore non-target outputs do not certify biological target absence. The old `baseline + U` summary remains only as a legacy non-target-decision width.

Without an independent absence-certifying channel, output-implied target-prevalence bounds are `[P(TARGET), 1]`.

V15-v2 makes this boundary explicit in code. `TargetAbsenceEvidence` is a separate fail-closed contract. The default pre-data state is unavailable, so:

```text
O observable + low/zero target evidence
=> unresolved, not certified absence
```

The upper prevalence bound may be tightened only by a genuinely independent validated `A-` channel or by an explicit sampling/missingness model.

## Cross-repository architecture

PolliPi exports target evidence only. It does not export nuisance truth, observability truth, confirmed visitation, or biological absence.

PolliPi ordinal evidence `0 / 0.5 / 1` is not V14b `Pi3`, and low PolliPi evidence is not `A-`. The V14b phase surface is a synthetic InsePi result; empirical transfer requires later measurement/calibration.

## V15-v2 empirical bridge

V15-v2 is merged on `main` as the active pre-data real visit-validation layer.

Its main rules are:

1. `T`, `C`, `N`, `O`, and optional `A-` remain separate.
2. `O=observable` means the primary stream is sufficiently measurable to attempt inference; it does not itself support biological absence.
3. Certified negative evidence requires adequate `O` plus independent validated `A-`.
4. `O=unobservable` censors positive and negative biological interpretation.
5. The full system uses `ProcessPreservingObservationTriadPolicy`, preserving observable T+N superposition.
6. Naive low-score binary negatives are kept only as `forced_absence_call` comparators so their false-absence cost can be measured separately from false certified absence.
7. No real V15 data have been scored and no field threshold has been frozen.

Normative files:

- `benchmarks/v15_empirical_bridge_v2_contract.json`
- `docs/V15_EMPIRICAL_BRIDGE_V2.md`
- `src/interaction_sensing/target_absence.py`
- `src/interaction_sensing/v15.py`

The public empirical facade is `interaction_sensing.v15`; the root V14 API is not overwritten.

## Development history

The repository intentionally preserves failed and superseded generations as evidence:

- V5/V7: fixed disagreement/allocation ideas fail their frozen gates;
- V8: generality is conditional rather than universal;
- V9: protected probability sampling preserves inferential denominators;
- V10: real-pixel transfer is partial;
- V11: static contradiction localization fails;
- V12: controlled interventions recover conditional causal discrimination;
- V13: physical intervention protocol is frozen but result-pending;
- V14a/V14a2: dimensionless closed-world development rejects the simple dominant `Pi2 ~= 1` ridge;
- V14b: alternating target/nuisance development freezes by contradiction-type saturation and risk contracts;
- V14c: post-freeze semantic clarification weakens unsupported overclaims without rerunning the surface;
- historical V15 PR #37: superseded development branch;
- V15-v2: current empirical bridge aligned to the V14c absence boundary.

## Directory map

| Path | Role |
|---|---|
| `src/interaction_sensing/` | Current and historical sensing contracts, target/nuisance observers, V15 empirical components, ternary decision logic, simulations, intervention logic, and evaluation utilities. |
| `benchmarks/` | Frozen protocols/results plus current pre-data contracts and claim boundaries. |
| `docs/` | Current V14/V15 interpretation plus the full negative-result/development record. |
| `scripts/` | Reproducible protocol-specific runners and audits. |
| `tests/` | Unit tests and scientific-contract tests. |
| `analysis/` | Post-hoc analysis utilities retained from earlier observation-process work. |
| `configs/` | Earlier runtime/NoiseBench configuration material. |
| `models/` | Legacy trained target-detection weights. |
| `legacy/` | Earlier prototypes and baselines, not the current scientific ontology. |
| `provenance/frozen_github_workflows/` | Original generation-specific GitHub Actions YAML retained byte-for-byte but removed from active automatic execution after freeze. |

## Active execution surface

Generic PRs automatically run only:

- `.github/workflows/test.yml`

V13 remains result-pending and has one explicit manual-only preflight:

- `.github/workflows/v13-manual-preflight.yml`

Historical V6–V14b scientific workflows are provenance, not active CI. V15-v2 has no automatic scientific-result workflow: its present state is pre-data contracts, software, tests, and measurement design.

## Empirical next step

The next scientific task is not to reduce U by threshold tuning. It is to freeze a real-data V15 measurement design that can test:

- whether `O` can be calibrated independently from T/N and biological truth;
- whether any practical independent `A-` channel can be validated;
- the empirical cost of forced absence versus retained U;
- T/C/N/O performance on new recording days and focal scenes;
- block/exposure-level visit-rate inference without treating censored time as no-visit time.

If no valid `A-` channel can be justified, V15 must retain the target-presence upper bound at 1 rather than manufacture an absence rule from low target evidence.

## Claim boundary

V14b/V14c are closed-world frozen-observer results. V15-v2 is pre-data empirical design/software. None of these currently establishes field visitation accuracy, calibrated field observability, a validated target-absence channel, field prevalence, calibrated PolliPi probabilities, universal physical transition points, or universal superiority of the full T/C/N/O/A- architecture.
