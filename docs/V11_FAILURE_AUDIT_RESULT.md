# V11 post-result failure audit

## Boundary

This is a descriptive audit of the already frozen V11 negative result. It does **not** change:

- V11 claim **D**;
- V11 protocol SHA-256 `af358226f4afccff3bb148e90a30c5fe9a25c2170d3f223497a22fb3dd685080`;
- V11 canonical result SHA-256 `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`.

The audit asks why the preregistered static contradiction-state representation failed to transfer from development mechanisms to held-out mechanism subtypes.

## Main confusion pattern

The contradiction-guided classifier collapsed many held-out faults into `no_fault`:

- true `event_module`: **856/900** predicted `no_fault`;
- true `observability_module`: **776/900** predicted `no_fault`;
- true `shared_representation`: **538/900** predicted `no_fault`.

This explains its combination of:

- very low no-fault false intervention;
- very high wrong-module intervention among actual faults;
- poor repair transfer.

The method was conservative because it often refused to diagnose a fault, not because it correctly localised faults.

## Low/low state did not retain causal meaning

The key V11 shared-blind-spot cue was the `both_low` state plus protected audit.

For the true shared-representation class:

- development: among audited `both_low` blind probes, `P(event=1 and disturbance=1 | both_low)` ≈ **0.217**;
- held-out: the same quantity fell to ≈ **0.008**.

Therefore the low/low quadrant did not preserve a stable interpretation across mechanism subtype shift. A state that looked like a useful shared-miss diagnostic during development became almost non-specific in the held-out mechanism.

This is the central scientific reason not to tune the low/low threshold within V11.

## Centroid geometry shifted across mechanism subtype

The static nearest-centroid operationalisation also changed class geometry substantially between development and held-out mechanisms. In particular, the contradiction-guided representation expanded each probe into raw E/O, four quadrant indicators, audit/error features and a shared-miss indicator. After feature-wise z scaling, several derived coordinates represented the same underlying E/O variation multiple times.

The audit therefore supports the narrower interpretation:

> static observer-state geometry does not, by itself, identify which causal component failed.

It does **not** support the broader claim that early fusion is generally better. The comparator results themselves were heterogeneous: early scalar fusion had the highest V11 localisation accuracy, while observability-only had the best shared-blind-spot discovery and repair-positive rate.

## Development consequence

V12 therefore changed the **experiment**, not the V11 classifier:

1. intervene on a specified causal path;
2. compare its paired response with a matched placebo baseline;
3. preserve the E/O response vector;
4. choose a second intervention to separate the currently leading causal hypotheses.

V12 then achieved claim B, with the main dual-channel advantage appearing in one-intervention diagnostic efficiency rather than a large final-accuracy margin.

That generational sequence is deliberate:

`static contradiction state FAIL/D → controlled causal intervention B`

The next physical V13 protocol tests whether those paired intervention-response signatures exist on blinded same-stream physical blocks.
