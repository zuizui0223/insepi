# V15-v2 realised split and blinding manifest

## Purpose

Truth semantics are already frozen, but the actual development/held-out allocation cannot be frozen until the field inventory exists. This validator makes that remaining dependency explicit instead of allowing frame-level random splitting later.

## Independent unit

Every window carries an explicit `cluster_id`. Windows/frames inside the same cluster are not independent biological replicates and the entire cluster must belong to one split.

The intended cluster is a recording block such as recording day × focal scene/flower, retained explicitly in the final manifest.

## Held-out separation

The realised held-out manifest must satisfy both:

- recording days are entirely new relative to development;
- focal scenes/flowers are entirely new relative to development.

Passing only one of those boundaries is insufficient.

## Truth double annotation

The four frozen truth layers are:

- biological event;
- target-coupled response;
- exogenous nuisance;
- observation support.

Within every realised cluster, each truth layer must have at least 20% of windows preselected for independent double annotation before model scoring. The manifest records those selections; they are not chosen after disagreement or model output is visible.

## Provenance

Every row retains:

- unique window ID;
- cluster ID;
- recording day;
- focal scene ID;
- development/held-out assignment;
- primary clip SHA-256;
- reference clip SHA-256;
- preselected double-annotation layers.

## Current boundary

The validator is development-defined, but `split_blinding_protocol` is not yet FROZEN because no realised dataset manifest exists. The final sampling/power plan and actual field inventory must determine the allocation, after which the validated manifest itself must be committed and SHA-registered before held-out scoring.

No placeholder split counts as frozen.
