# V15-v2 four-layer truth annotation freeze

The four V15-v2 truth definitions are now frozen before held-out field scoring. They are annotation semantics, not fitted quantities, so postponing them until after development outcomes would only increase researcher degrees of freedom.

Frozen artifact:

`benchmarks/v15_truth_annotation_freeze_v1.json`

## Layer A — biological event truth

Annotators see the synchronised independent reference stream only.

Allowed states:

- `no_insect`
- `insect_in_context`
- `target_contact`
- `visit_event`
- unresolved

If the reference channel cannot resolve the event, truth stays unresolved; it is never converted to `no_insect`. A resolved `visit_event` carries a stable event ID.

## Layer B — target-coupled response truth

This is a separate causal-attribution pass on the reference channel.

States:

- absent
- present
- unresolved

`present` is allowed only when the independently completed biological ledger resolves `target_contact` or `visit_event`. If the response cannot be attributed to the insect, it remains unresolved rather than being called coupling.

## Layer C — exogenous nuisance truth

Annotators see the primary stream and physical nuisance logs when available, with biological reference truth hidden.

The primary representation is a positive, multi-label process-effect vocabulary:

- `mimic_target`
- `mask_target`
- `corrupt_attribution`
- `degrade_observation_support`

Target-driven local flower response is excluded from this layer. Optional physical cause descriptions may be retained, but causes do not replace the finite effect vocabulary.

## Layer D — primary-stream support truth

Annotators or physical measurements use only the primary stream plus the geometry/timing/photometric metadata required to assess:

- target-zone coverage
- target-zone visibility
- spatial resolution
- photometric sufficiency
- temporal continuity

Each component is `adequate / compromised / failed / unresolved`.

Overall truth is frozen as:

```text
any failed component       -> resolved UNOBSERVABLE
else any unresolved        -> support truth unresolved
else any compromised       -> resolved COMPROMISED
else                       -> resolved OBSERVABLE
```

Support may not use target score, nuisance score, biological truth or the support algorithm output.

## Common blinding and adjudication invariants

Across the four layers:

- algorithm outputs are hidden from truth annotation;
- unresolved labels remain unresolved;
- raw labels and disagreement indicators are retained;
- sampled double-annotation disagreements are adjudicated before scoring;
- cross-layer conflict is never reconciled automatically;
- there is no post-result agreement threshold that drops a truth layer or triggers observer retuning.

At least 20% is independently double annotated within each truth layer and realised independent block. Selection must be fixed by protected probability or deterministic hash sampling before model scoring.

## What is deliberately not frozen here

The registry item `split_blinding_protocol` remains development-defined rather than falsely marked complete. The following depend on the final sampling/power plan and realised dataset manifest:

- development versus held-out block assignment;
- realised recording-day / focal-scene allocation;
- final split proportion and cluster count.

Thus this step freezes **truth semantics and annotation blinding**, while leaving the realised split to a later pre-held-out freeze.

## Readiness after this step

Expected registry state:

```text
design_complete               true
frozen core items              6
development-defined core items 6
unset core items               0
held-out                       BLOCKED_SAFE
```

The remaining six core blockers all require realised allocation, development-only calibration, or predeclared numerical choices. No held-out result is created by this freeze.
