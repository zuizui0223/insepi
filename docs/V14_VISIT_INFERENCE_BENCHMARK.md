# V14 visit-inference development benchmark

V14 tests a narrow but important consequence of the target–nuisance–observability model: **a non-detection is ecological negative evidence only when the focal interaction opportunity was observable**.

The benchmark compares three inference policies on identical synthetic worlds:

1. `target_only` — target evidence alone;
2. `target_plus_nuisance` — target evidence plus false/missed/attribution risk;
3. `triad` — target evidence, nuisance risk, and independent observation support.

The world varies three latent axes independently:

- insect/visit truth;
- nuisance mechanism;
- observation-support truth.

This deliberately creates both:

- low-nuisance but unobservable windows;
- high-nuisance but observable windows.

Therefore the benchmark can detect two opposite mistakes:

- counting an unobservable non-detection as absence;
- discarding every high-nuisance observation as if it were unobservable.

## Primary metrics

The benchmark does **not** compute one winner score. It reports separately:

- false absence among true visits;
- false positive visit candidates among true absences;
- contamination of the ecological denominator by unobservable windows;
- retention of genuinely observable opportunities;
- visit-candidate recall conditional on observable opportunities;
- censoring recall for truly unobservable opportunities.

## Diagnostic slices

`low_nuisance_unobservable`
: tests the failure that cannot be solved by defining observability as `1 - nuisance`.

`high_nuisance_observable`
: tests whether nuisance can be high while the opportunity remains measurable.

`masking_observable`
: isolates a nuisance that mainly increases missed-event risk without necessarily destroying the measurement channel.

`support_loss_low_target`
: tests whether low target evidence caused by measurement failure is incorrectly converted to biological absence.

## Claim boundary

This is a **development** benchmark. It validates the semantics and failure modes of the three-axis observation model, not field pollinator accuracy. The next empirical generation must provide independent insect/visit truth and independent observation-support truth, ideally with observer-blinded annotation.
