# V15-v2 target field adapter freeze

## Purpose

V15-v2 needs a field-facing direct target-evidence interface without reintroducing the invalid implication that low target evidence certifies biological absence.

The source interface is PolliPi `main` at commit `f3b266897f3e9139e6c3fe9ce6b645e25371e092`, file:

`packages/analysis/src/pollipi_analysis/target_evidence.py`

with Git blob SHA-1:

`4be5f7c88edda1dda3b62e8a95529386d702bb47`

## Frozen mapping

```text
no_activity                   -> 0.0
environmental_noise           -> 0.0
uncertain_local_activity      -> 0.5
strong_visitation_candidate   -> 1.0
```

The scale is `ordinal-v14-reference`, not a calibrated probability.

## Inference boundary

The InsePi adapter carries this record only into the **direct positive target route**.

It does not expose an API that converts score 0 into:

- biological target absence;
- nuisance truth;
- observation-support failure;
- a confirmed no-visit state.

Likewise score 1 is not a confirmed biological visit.

`environmental_noise -> 0.0` therefore means only that PolliPi retained no direct positive target evidence at the stronger levels. Nuisance truth remains an independent InsePi quantity.

## Coupled route

The adapter creates no coupled evidence. `coupled_response_score` and `target_link_confidence` remain zero in the direct-only conversion. A coupled target route must come from its own V15 measurement and attribution procedure.

This prevents the direct PolliPi score from being reused as a second, non-independent target channel.

## Frozen vs not frozen

Frozen now:

- accepted PolliPi source states;
- exact ordinal mapping;
- scale identifier;
- `confirmed_visit=False` boundary;
- positive-only direct-route conversion;
- no negative inversion;
- cross-repository source commit and blob provenance.

Not established by this freeze:

- field target recall or precision;
- calibrated target probability;
- final field target high/low thresholds;
- coupled-response field calibration;
- biological absence certification.

Those remain empirical/calibration questions. Freezing the adapter prevents the meaning of the field input from changing after held-out outcomes are visible.
