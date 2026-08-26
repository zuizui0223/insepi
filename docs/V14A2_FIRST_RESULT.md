# V14a2 first locked result

## Status

V14a2 has completed its first and preregistered closed-world scientific sweep without retuning.

- prefreeze design commit: `b88ad58c6db53b3bbc5bf5d00d3e54ade15ae32a`
- execution commit: `9d4467c6c93f5b51fe46b250ede4e4e10d3e4bb3`
- workflow run: `32921177706`
- artifact id: `9590040360`
- artifact SHA-256: `11c0409e163183395410271141928777310137711f74fee7e9e0f6e500e32b72`
- runtime: CPython 3.11.16 / NumPy 2.4.6
- coarse sweep: 30,625 coordinates, 612,500 truth-known deviation worlds
- focused collision sweep: 2,025 coordinates, 32,400 mixed-regime worlds

The raw response surfaces remain in the immutable workflow artifact. Repository files retain their exact hashes and the result receipt.

## Registered results

### Q1 — sampling and information absence: not supported

The preregistered coarse contrast predicted more `information_absent` outcomes at low `Pi6`.

Observed:

- low `Pi6`: `0.4048`
- high `Pi6`: `0.4048`

Therefore Q1 is **not supported** in V14a2.

This result is retained. It is not repaired by changing thresholds or adding lower sampling values after inspection.

### Q3 — `Pi2 × Pi5` collision interaction: not supported

The focused sweep tested whether temporal-scale collision near `Pi2 = 1` preferentially thickens essential ambiguity when the nuisance spatial scale also approaches the target scale (`Pi5 = 1`).

Registered contrast:

- ambiguity at `Pi5=1`, `Pi2=1`: `0.440586`
- ambiguity at `Pi5=1`, Pi2 shoulders: `0.441358`
- temporal-collision effect at `Pi5=1`: `-0.000772`
- temporal-collision effect at broad `Pi5`: `+0.006173`
- interaction: `-0.006944`

The interaction has the opposite sign from the prediction and is tiny relative to the background ambiguity level. Q3 is therefore **not supported**.

Under the preregistered Q4 rule, this strengthens rejection of the simple timescale-collision hypothesis rather than rescuing the negative V14a result.

## What the phase surface shows instead

The main geometry is not a narrow critical ridge at `Pi2 ~= 1`.

Across the balanced coarse factorial surface, mean indeterminacy was `0.715861`, decomposed into:

- information absence: `0.404800`
- essential ambiguity: `0.230155`
- model uncertainty: `0.080906`

The largest descriptive changes in mean undetermined rate were associated with:

1. latent process regime (`range ~= 0.544`);
2. observation-window ratio `Pi1` (`~0.363`);
3. coupled-response amplitude `Pi4` (`~0.315`);
4. direct-target amplitude `Pi3` (`~0.208`).

The marginal ranges for `Pi2` (`~0.038`) and `Pi5` (`~0.028`) were much smaller.

The strongest regime contrast was:

- nuisance only: mean undetermined `~0.406`
- target+nuisance coupled: `~0.902`
- target+nuisance superposed: `~0.950`

Thus the principal difficulty in this closed world is **process superposition under weak target-side evidence**, not equality of target and nuisance timescales.

## Broad ambiguity plateau

A post-result diagnostic slice was used only to understand the locked result; it is not a new preregistered claim.

Among temporally resolved, weak-direct/weak-coupled T+N worlds:

- mean undetermined rate: `0.996204`
- information absence: `0.555556`
- essential ambiguity: `0.439769`
- mean identifiability margin: `0.015460`

After additionally requiring mean observation support >= 0.2, information absence disappears, but the result becomes even clearer:

- mean undetermined rate: `0.991458`
- essential ambiguity: `0.989479`
- mean identifiability margin: `0.019932`
- post-result `Pi2 × Pi5` interaction: `-0.015625`

So the V14a2 response surface contains a **broad essential-ambiguity plateau** in observable weak-evidence superposition worlds. It is not centred on `Pi2=1`.

## Q1 post-result diagnosis

`Pi6` genuinely changes the generated sample count and target-route strength, but the categorical `information_absent` gate did not change across the registered `Pi6` grid.

The reason is geometric: the lowest sampled value was `Pi6=2`, giving

`target_sampling_support = 2/8 = 0.25`,

while the frozen information-support threshold was `0.20`. Thus `Pi6` alone never crossed the categorical support boundary when window and amplitude support were otherwise adequate.

This is a design limitation of the Q1 contrast, not evidence that sampling density is generally irrelevant. V14a2 remains negative for Q1; any redesigned sampling-boundary test requires a new generation.

## Additional boundary exposed

The overall `both_supported_rate` was only about `0.000296`. In the current reference observer, nuisance support rarely reaches the frozen `0.55` positive threshold even in true T+N worlds. The ontology permits target+nuisance superposition, but the current nuisance evidence representation seldom produces simultaneous high/high support.

This is a representation/calibration limitation to diagnose in later development; it must not be repaired inside the locked V14a2 result.

## Current scientific conclusion

The original working idea

> `Pi2 ~= 1` creates a special thick ambiguity band

has now failed twice: first in V14a, then under independent spatial-scale and sampling coordinates in V14a2.

The stronger result supported by the current closed worlds is different:

> **Indeterminacy is governed primarily by whether enough process-specific evidence exists and whether target and nuisance processes are superposed. Under weak but observable evidence, superposition produces a broad ambiguity plateau rather than a narrow timescale-collision boundary.**

This is a closed-world methodological result. It does not establish a field transition point, pollinator-detection accuracy, or a universal physical law.
