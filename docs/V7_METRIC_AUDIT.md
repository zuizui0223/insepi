# V7 metric audit — avoid circular interpretation

## Why this audit exists

The V5/V6 development programme uses `hidden_error_recall` as a primary allocation
endpoint. That name can be misread as if the simulator contains a world-intrinsic
binary variable called "error". It does not.

The primary hidden-error endpoint is **observer-relative**: latent ground truth is
compared with the PolliPi biological-evidence decision, and the allocation policy
is scored on whether its selected audit windows recover those detection or
attribution failures.

This is a legitimate audit-policy question:

> If PolliPi is the biological evidence stream whose errors must be audited, where
> should limited additional observation effort be spent to discover its hidden
> failures?

It is not equivalent to the stronger statement:

> These windows are intrinsically erroneous independently of the observer.

The manuscript must preserve that distinction.

## Primary locked endpoint

`hidden_error_recall` retains the same V6/V7 hard-gate role so the preregistered
validation target is not changed after V6 method freeze.

Its semantics are:

- latent true visit + no PolliPi candidate -> missed-event audit target;
- latent no visit + PolliPi candidate -> false-event audit target;
- PolliPi candidate under clutter -> attribution audit target.

Thus the truth labels are latent, but the existence of a detection error is
necessarily defined relative to the observer being audited.

In text and figures, prefer **PolliPi detection-error recall** or
**observer-relative hidden-error recall** on first use.

## Added observer-independent secondary endpoints

V7 now also records two metrics that use only latent world labels and the selected
indices. They never inspect PolliPi state or InsePi risk outputs.

### Disturbance-window recall

```text
selected non-clean disturbance windows / all non-clean disturbance windows
```

This answers whether a policy broadly covers the simulated observation-process
perturbations rather than merely targeting places where one observer happens to
fail.

### Disturbed true-event recall

```text
selected true-visit windows under non-clean disturbance /
all true-visit windows under non-clean disturbance
```

This asks whether biologically real events remain represented when observation
conditions are difficult.

These metrics are secondary diagnostics. They do **not** alter the already frozen
V7 pass/fail rules.

## Why they are not new hard gates

Making new secondary endpoints mandatory after V6 development would shift the
validation target. Instead V7 reports them transparently and uses them to qualify
interpretation.

Examples:

- If V6 passes the primary hard gate but has unusually poor disturbance-window
  recall, the paper must discuss selective coverage rather than imply universal
  disturbance auditing.
- If V6 improves observer-relative hidden-error recall but not disturbed true-event
  recall, the gain should be described as targeted detector-error auditing, not as
  general preservation of difficult biological events.
- If both secondary metrics improve or remain comparable to uniform, the
  anti-circular interpretation is stronger: V6 is not merely exploiting the
  particular definition of PolliPi failure.

## Relationship to disturbance TV

Disturbance-window recall and TV answer different questions.

- recall asks **how much** of the disturbed timeline is audited;
- TV asks **how distorted the composition** of selected disturbance families is
  relative to the full timeline.

A policy can have high disturbed-window recall while overconcentrating on one
family, or low recall while preserving family proportions. Both should be shown.

## Claim language

Avoid:

> V6 recovers hidden ecological errors.

Prefer:

> V6 recovers latent-truth detection errors of the biological-evidence observer
> under finite audit budgets.

Then separately report observer-independent disturbance coverage and true-event
coverage under disturbance.

This language keeps the method claim aligned with what the simulator actually
identifies and removes an avoidable circularity objection without changing the
frozen allocation policy or V7 hard gate.
