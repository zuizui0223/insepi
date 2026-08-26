# V15 — Layer-separated truth collection

V15 uses four truth layers, but they must **not** be collected as one cognitively coupled judgement.

## Pass A — biological truth

Input shown to annotator: synchronised independent reference stream only.

Output:
- `no_insect`
- `insect_in_context`
- `target_contact`
- `visit_event`
- or unresolved.

The primary system-under-test stream, target score, nuisance score and support estimate are hidden.

## Pass B — target-coupled response truth

Input shown: reference stream needed to evaluate whether a local target/flower response was caused by the focal insect interaction.

Output:
- present
- absent
- unresolved.

A positive label is valid only when the independently completed biological ledger resolves target contact or a visit. The pass may use the frozen biological adjudication for this logical consistency check, but never system predictions.

## Pass C — exogenous nuisance truth

Input shown: primary stream and physical nuisance logs only. Reference biological truth is hidden.

Output is multi-label:
- mimic target
- mask target
- corrupt attribution
- degrade observation support.

Target-driven flower response is excluded by definition; it belongs to Pass B if causally supported.

## Pass D — primary-stream observation support

Input shown: primary stream plus geometry/timing/photometric metadata needed to assess the five support requirements. Reference biological truth and nuisance labels are hidden.

Annotate/measure:
- target-zone coverage
- target-zone visibility
- spatial resolution
- photometric sufficiency
- temporal continuity.

The question is counterfactual and biological-label-free:

> If a focal visit opportunity occurred during this window, did the primary stream preserve enough information to observe it under the operational visit definition?

This pass must never use low target evidence as proof of poor support or use known biological presence as proof that support was adequate.

## Join order

Each pass produces a separate ledger with window ID and channel-specific clip SHA-256. Layer-specific disagreements are adjudicated before the ledgers are joined.

`join_layered_truth()` then verifies:
- matching window IDs;
- matching reference clip hashes for biological/coupling truth;
- matching primary clip hashes for nuisance/support truth;
- positive coupling is consistent with resolved target contact/visit truth.

It never resolves a cross-layer conflict automatically.

## Why this matters

Without layer separation, an annotator who knows that a visit occurred from the reference camera may unconsciously rate the primary camera as more observable. Conversely, knowing that the primary stream is badly occluded may bias a biological annotation toward absence. Separate passes preserve the distinction between **what happened** and **whether the system-under-test could have observed it**.

## Double annotation

The V15 minimum independent double-annotation fraction remains 20% before final scoring. For the final protocol, allocation of the double-annotated subset across days/scenes and truth layers must be frozen before held-out scoring. No numerical agreement threshold is invented at this stage.
