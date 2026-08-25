# V14 compatibility boundary: legacy risk-derived `UNOBSERVABLE`

The historical `interaction_sensing.noise.NoiseFirstPolicy` contains an
`ObservabilityState.UNOBSERVABLE` label. In that legacy baseline, the label is
assigned when the maximum of false-event, missed-event, and attribution risk
crosses a threshold.

V14 does **not** use that legacy state as its observation-support truth.

The meanings are different:

- legacy `NoiseFirstPolicy.UNOBSERVABLE` = **very high risk according to the
  nuisance baseline**;
- V14 `ObservationAvailability.UNOBSERVABLE` = **the focal interaction opportunity
  is not sufficiently measurable for presence/absence inference**, based on
  target-zone coverage, visibility, resolution, photometric sufficiency, and
  temporal continuity.

This distinction is required because:

```text
high nuisance risk + good target-zone support
    -> may still be observable, but confounded/audit-priority

low nuisance risk + failed target-zone support
    -> may be unobservable despite an apparently quiet scene
```

No locked result from V7–V13 is reinterpreted using the new V14 definition. A
future visit-validation generation must validate the V14 observation-support gate
against independent support/visibility truth.
