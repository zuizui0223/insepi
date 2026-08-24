# Causal diagnostic identifiability

## Setup

Let a hidden failure class be `c`, an allowed diagnostic intervention be `j`, and the expected response of `K` epistemically distinct observer channels be

\[
\mu_{c,j}\in\mathbb{R}^K.
\]

For a selected intervention set `J`, define the concatenated intervention signature

\[
S_c(J)=\bigoplus_{j\in J}\mu_{c,j}.
\]

This document concerns **controlled diagnostic interventions in a research/software system**. It is not a general claim of causal identification from observational data.

## Proposition 1 — intervention signatures identify only distinguishable classes

Two failure classes `c` and `d` are distinguishable by the selected intervention set if and only if

\[
S_c(J)\neq S_d(J).
\]

If their signatures are identical for every selected intervention, no deterministic classifier operating only on those responses can distinguish them without additional information.

This is why static observer disagreement was insufficient in V11: the observed state representation need not uniquely encode the hidden cause.

## Proposition 2 — scalar fusion can destroy identifiability

Suppose a multi-channel response is projected to one scalar before diagnosis:

\[
z_{c,j}=a^\top\mu_{c,j}.
\]

For two failure classes, the projection loses their distinction under intervention `j` whenever

\[
a^\top(\mu_{c,j}-\mu_{d,j})=0.
\]

If this holds for all selected interventions, the scalar representation makes the two classes observationally identical even though the original response vectors differ.

A simple example is the mirrored pair

\[
\mu_{A,j}=(u,v),\qquad \mu_{B,j}=(v,u).
\]

Under equal 50/50 fusion,

\[
\tfrac12(u+v)=\tfrac12(v+u),
\]

so the scalar response is identical. The unfused two-vector remains distinguishable whenever `u != v`.

This does **not** imply that every fusion loses useful information. It states the exact condition under which a particular projection does.

## Proposition 3 — more interventions can restore identifiability

A single intervention may leave two classes with the same response signature while a second intervention separates them. Therefore diagnosis and experiment selection should be separated:

1. use responses already observed to rank the remaining failure hypotheses;
2. choose the next intervention whose predicted signatures separate the leading alternatives most strongly;
3. update the diagnosis only after observing that new response.

V12 instantiates this with a development-centroid model:

- first intervention: maximise the minimum pairwise centroid separation across all remaining classes;
- later intervention: take the two nearest current hypotheses and maximise their centroid separation among the remaining interventions.

The algorithm is implemented generically in `interaction_sensing.causal_diagnostics`.

## Protected random audit has a different role

A protected random audit can reduce the admissible hypothesis set without identifying the cause. For example, an independent audit may establish `fault_present = false`, in which case no repair experiment is needed. If it only establishes `fault_present = true`, the causal class still must be identified from interventions.

Thus the method retains two distinct safeguards:

- **controlled interventions** for causal failure localisation;
- **protected random audit** for blind-spot/no-fault safety and representative checking.

Neither is replaced by observer disagreement itself.

## Relation to the generational evidence

- V5: scalar disagreement allocation was falsified.
- V7: frozen 50/10/40 allocation failed locked validation.
- V11: static contradiction-state localisation failed under mechanism-subtype shift.
- V12: controlled interventions restored high held-out identifiability, with claim B because final dual-channel accuracy exceeded early fusion only modestly; the stronger advantage appeared in one-intervention diagnostic efficiency.

The generational conclusion is therefore narrower than “keep channels separate at all times.” It is:

> Preserve distinct hypotheses until the experiment has extracted the information needed to discriminate them; fuse only when the projection is known not to remove distinctions relevant to the current decision.

## Boundary before physical validation

The response signatures in V12 were synthetic and preregistered. A physical validation must establish that real manipulations produce reproducible intervention signatures under blinded held-out blocks. Until then, the propositions above are information/geometry statements and V12 is proof-of-identifiability evidence, not field-performance evidence.
