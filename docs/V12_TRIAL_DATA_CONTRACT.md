# V12 physical trial data contract

**Design infrastructure only — not yet the locked V12 protocol.**

V12 uses process-level separation so intervention truth cannot enter observer decisions accidentally.

## 1. Controller domain — treatment truth allowed

The acquisition controller receives the full randomised trial plan.

```text
controller/
  full_trial_plan.json
  event_controller_logs/
  disturbance_controller_logs/
  external_sensor_logs/
```

The full plan contains day/camera/scene block, development/held-out split, disturbance family/intensity, event intervention and disturbance intervention.

The controller must write the captured clip to an **opaque trial-id filename** such as:

```text
captures/v12-<opaque-id>.mp4
```

No treatment word, event flag, disturbance flag, family, intensity, split, day, scene or block label is permitted in the observer-facing filename.

## 2. Observer domain — treatment truth forbidden

The observer environment receives only:

```text
observer_bundle/
  observer_manifest.json
  clips/
    v12-<opaque-id>.mp4
```

Each manifest record contains exactly:

- schema;
- opaque `trial_id`;
- clip path;
- clip SHA-256.

It does **not** contain:

- event intervention;
- disturbance intervention;
- disturbance family/intensity;
- development/held-out split;
- day/camera/scene/block;
- actuator logs;
- external sensor values;
- human annotations.

PolliPi and InsePi are run independently from this same observer bundle. Their outputs are separate truth-free traces keyed only by `trial_id`.

The observer process must not mount or receive the controller truth directory. This is stronger than relying on code discipline alone.

## 3. Evaluation domain — join after inference

Only after both truth-free observer traces are complete may the evaluator read:

```text
evaluation_bundle/
  observer_E_trace.jsonl
  observer_O_trace.jsonl
  intervention_truth.jsonl
  full_trial_plan.json
  clip_hash_registry.json
```

The evaluator joins all sources by opaque `trial_id`, verifies clip hashes, checks that every physical treatment cell is complete/balanced, and estimates the preregistered factorial causal response contrasts.

## 4. Field biological annotation domain

For the later real-pollinator component, human annotators receive raw opaque clips but **not** PolliPi/InsePi outputs or causal diagnostic labels. Human event annotations are written to a separate ledger and joined only at evaluation.

The physical proxy event-controller truth and real-pollinator human truth are never conflated. Bench causal validation cannot be promoted into a field biological-detection-accuracy claim.

## 5. Hash/provenance requirements

Before observer execution, record SHA-256 for:

- full trial plan;
- randomisation-plan generator commit/file;
- every clip;
- observer manifest;
- controller logs and external-sensor logs.

After observer execution, additionally record:

- PolliPi trace;
- InsePi trace;
- intervention truth ledger;
- response-contrast report;
- evaluation receipt.

A mismatch invalidates the execution rather than being silently repaired.

## 6. Protected random audit

Natural/field clips that are not controlled interventions retain a preregistered probability-sample audit path independent of both observer scores. This is the only route by which an apparent low/low agreement can be distinguished from a shared miss without assuming that agreement means truth.
