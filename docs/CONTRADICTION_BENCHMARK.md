# PolliPi × InsePi contradiction benchmark

## Aim

This benchmark treats disagreement between two ecological sensing philosophies as
a development signal rather than immediately forcing consensus.

- **PolliPi** seeks compact local visitation evidence and suppresses broad scene
  disturbance when allocating capture effort.
- **InsePi** preserves disturbance as an observation-process variable and asks
  whether a frame/window is clean, confounded, audit-priority, or unobservable.

The projects remain independently executable. They share only a stable latent
scenario contract and portable JSONL traces.

## V1 scenario contract

Schema: `pollipi-insepi-contradiction-v1`

```text
quiet_absence
clean_visit
wind_absence
wind_visit
shake_absence
shake_visit
shadow_absence
shadow_visit
occluded_visit
blurred_visit
clutter_visit
unknown_visit
```

Each scenario defines `true_visit`, `noise_source`, `noise_confidence`, and
`event_visibility`. InsePi converts the noise condition into its existing
`NoiseObservation` and runs `NoiseFirstPolicy` unchanged.

The sibling PolliPi implementation independently converts the same latent
condition into PolliPi mesh evidence and runs its current mesh classifier.
`simulation.disagreement` joins the two result traces only after both projects
have made their own decisions.

## V1 disagreement taxonomy

The trace comparator currently distinguishes:

- `supported_candidate`
- `supported_absence`
- `shared_noise_detection`
- `visit_suppressed_where_observation_is_risky`
- `candidate_requires_audit`
- `missed_visit_in_unreliable_window`
- `pollipi_miss_under_clean_observation`
- `false_candidate`
- `candidate_under_confounding`
- `mixed_interpretation`

A score of `>= 0.8` marks a high-value disagreement for audit in this simulation.
It is not a probability and should not be interpreted as calibrated confidence.

## First V1 prediction

Under the current independent policies, the canonical 12-scenario contract is
expected to contain **six high-disagreement cases**:

1. true visit + vegetation motion;
2. true visit + camera shake;
3. true visit + moving shadow;
4. true visit + multi-object clutter;
5. true visit + occlusion;
6. true visit + blur/focus loss.

The first four are the strongest philosophical conflict: PolliPi suppresses the
broad/diffuse event channel while InsePi says the same window deserves audit.
Occlusion and blur are different: PolliPi preserves faint local uncertainty and
InsePi independently elevates missed-event risk, so the systems are more
complementary than contradictory there.

## Rules for parallel development

1. Do not import PolliPi into InsePi's sensing logic or vice versa.
2. Do not tune one project merely to increase agreement.
3. Preserve each project's native outputs in the trace.
4. Treat recurrent disagreements as hypotheses about the observation process.
5. Promote a disagreement into a shared/new module only after truth/audit shows
   that it predicts a systematic error or resource-allocation gain.

## Next benchmark layers

- **V2 shared visual world:** same rendered pixels, separate front ends.
- **V3 fixed-record replay:** real flower-camera sequences with manual visit and
  observation-condition labels.
- **V4 budget competition:** fixed sampling vs PolliPi candidate-priority vs
  InsePi audit-priority vs disagreement-priority at equal storage/power.

The target result is not maximal agreement. The target is evidence that
**where the systems disagree is more informative than where either system is
confident alone**.
