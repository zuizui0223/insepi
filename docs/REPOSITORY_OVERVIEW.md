# Repository overview

This page points to the **current scientific state** of `interaction-sensing`. Historical modules remain in the repository for reproducibility, but the active conceptual architecture is V14b/V14c rather than the older noise-first product framing.

## Current scientific object

The repository studies when a dynamic ecological observation can safely support one of three deviation-side conclusions:

```text
TARGET / NUISANCE / UNDETERMINED
```

with a separate baseline state outside the dynamic query.

Target and nuisance are positively defined and may coexist. `UNDETERMINED` is an epistemic decision region, not a biological process. V14c further separates:

- `NO_SUPPORTED_EVIDENCE` — neither frozen observer supports a safe conclusion; this does **not** by itself prove true information absence;
- overlap / attribution unresolved — evidence exists, but coexistence or attribution prevents a unique exclusive label.

Observability remains a separate measurement axis and must not be equated with `1 - nuisance`.

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

Key files:

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

Without an independent absence-certifying channel, output-implied target-prevalence bounds are `[P(TARGET), 1]`. Empirical tightening belongs to a later observability/absence-certification or sampling/missingness model, not to post-hoc V14b threshold tuning.

## Cross-repository architecture

PolliPi now exports target evidence only. It does not export nuisance truth, observability truth, confirmed visitation, or biological absence.

PolliPi ordinal evidence `0 / 0.5 / 1` is not V14b `Pi3`. The current V14b phase surface is a synthetic InsePi result; empirical transfer requires later measurement/calibration.

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
- V14c: post-freeze semantic clarification weakens unsupported overclaims without rerunning the surface.

## Directory map

| Path | Role |
|---|---|
| `src/interaction_sensing/` | Current and historical sensing contracts, target/nuisance observers, ternary decision logic, simulations, intervention logic, and evaluation utilities. |
| `benchmarks/` | Frozen protocols, receipts, result summaries, thresholds, seed registries, and claim boundaries. |
| `docs/` | Current interpretation plus the full negative-result/development record. |
| `scripts/` | Reproducible protocol-specific runners and audits. |
| `tests/` | Unit tests and scientific-contract tests. |
| `analysis/` | Post-hoc analysis utilities retained from earlier observation-process work. |
| `configs/` | Earlier runtime/NoiseBench configuration material. |
| `models/` | Legacy trained target-detection weights. |
| `legacy/` | Earlier prototypes and baselines, not the current scientific ontology. |
| `provenance/frozen_github_workflows/` | Original generation-specific GitHub Actions YAML retained byte-for-byte but removed from active automatic execution after freeze. |

## Active execution surface

Generic PRs should automatically run only:

- `.github/workflows/test.yml`

V13 remains result-pending and has one explicit manual-only preflight:

- `.github/workflows/v13-manual-preflight.yml`

Historical V6–V14b scientific workflows are provenance, not active CI. This prevents a repository-integration PR from accidentally rerunning frozen experiments.

## Empirical next step

The next scientific problem is not to force U lower. It is to determine whether real-camera observation support and target absence can be certified independently from biological event truth and nuisance labels. V13/V15 provide the physical and real-visit bridge for that question.

## Claim boundary

V14b/V14c are closed-world frozen-observer results. They do not establish field visitation accuracy, field prevalence, calibrated PolliPi probabilities, universal physical transition points, or universal irrelevance of positive direct-signal magnitude.
