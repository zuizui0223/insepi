# V14c semantic clarification of the locked V14b surface

V14c does not rerun or retune V14b. The locked 5,880,000-world surface remains immutable.

## 1. `INFORMATION_ABSENT` is too strong a historical name

The frozen V14b decision layer labels a dynamic case as `INFORMATION_ABSENT` when neither frozen positive observer is safely supported and the target observer is not in its explicit indirect-only state.

That operational fact means only:

> no supported target or nuisance evidence under the frozen observers.

It does **not** by itself prove that the observation contained no target/nuisance information. The same output could arise from true information absence, representation failure, model limitation, or an unswept evidence channel.

V14c therefore uses the scientifically weaker label:

`NO_SUPPORTED_EVIDENCE`.

The historical V14b result is not rewritten. Any future claim of true `information_absence` requires an independent identifiability or observability test.

## 2. The historical `baseline + U` quantity is not target-presence partial identification

V14b reported:

`visit_presence_partial_identification_width = baseline_rate + undetermined_rate`.

This is a useful descriptive measure of how much output is neither an explicit TARGET nor an explicit NUISANCE decision, but it is not a logically complete target-presence identification width.

Why: the V14b target observer is positive-only. `TARGET` certifies target support, while `NUISANCE`, `BASELINE`, and `UNDETERMINED` do not certify target absence. In particular, target-present worlds can map to nuisance or baseline when the direct target channel is absent.

Therefore, without an independent target-absence-certifying channel, the safe prevalence bounds implied by V14b outputs are:

`p(target) in [P(TARGET), 1]`.

For the locked global surface:

- lower bound = 0.4287333333;
- upper bound = 1.0;
- safe width = 0.5712666667.

The historical 0.4835690476 value is retained and renamed:

`legacy_non_target_decision_width`.

A later generation may tighten the upper bound only by adding and independently validating a target-absence-certifying channel or an explicit missingness/sampling model.

## 3. Pi3 is a structural channel-availability boundary in V14b

The frozen V14b target rule is deliberately structural in the closed generator:

`target_supported = direct_target_signal_fraction > 0`.

Consequently, the strong Pi3=0 versus Pi3>0 phase split is partly built into the observer semantics. The correct claim is:

> Under the frozen structural direct-channel observer, the availability of a direct attribution channel dominates the final phase geometry.

The result does **not** show that positive direct-signal amplitude is universally irrelevant, nor that empirical SNR has a discontinuity at exactly zero.

## 4. What remains unchanged

- target observer;
- nuisance observer;
- family-wise alpha = 0.05;
- nuisance threshold;
- Pi1-Pi6 grid;
- latent regimes;
- measurement seeds;
- ternary state assignment;
- locked 5.88M-world surface and SHA-256;
- negative Pi2≈1 result;
- conclusion that overlap/attribution and evidence scarcity must not be collapsed.

V14c is therefore an interpretive correction, not a new performance generation.
