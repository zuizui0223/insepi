# V15-v2 development-only O calibration

## Why the historical thresholds are not enough

`PrimaryStreamSupportEstimator` currently carries 0.30 / 0.70 as development defaults. They are useful for software development but are not field-calibrated boundaries and cannot be carried into held-out V15-v2 by inertia.

## Calibration inputs

The calibration rule uses only:

- primary-stream support ceiling;
- independently collected resolved support truth;
- a predeclared maximum false-censor rate on truly observable development windows;
- a predeclared maximum false-observable rate on truly unobservable development windows.

It does not use biological target truth, PolliPi target output, nuisance output/truth or held-out support truth.

## Asymmetric risk rule

First choose the largest `unobservable_threshold` satisfying the declared false-censor budget on truly observable development windows.

Then choose the smallest `observable_threshold` strictly above that boundary satisfying the declared false-observable budget on truly unobservable development windows.

The interval between the two remains `COMPROMISED`.

If the declared budgets cannot produce a strictly ordered pair, calibration fails. The method does not collapse O into a binary state and does not relax a budget after seeing results.

## No numerical defaults

This implementation deliberately supplies no default risk budgets. Before a calibration run can become the frozen V15-v2 O contract, the two budgets must be justified and committed pre-data/pre-held-out.

The calibration output must then retain:

- both frozen budgets;
- both calibrated thresholds;
- development truth counts;
- achieved development false-censor/false-observable rates;
- source development manifest SHA;
- calibration artifact SHA-256.

Until those exist, `o_measurement_calibration` remains `development_defined` and held-out execution stays `BLOCKED_SAFE`.
