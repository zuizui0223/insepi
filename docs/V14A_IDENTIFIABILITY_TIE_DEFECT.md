# V14a identifiability tie defect retained as negative-generation evidence

During the pre-result V14a2 implementation audit, the inherited V14a model-relative identifiability margin exposed an edge-case representation defect.

The V14a rule was effectively:

```text
if best_distance == 0 and second_best_distance == 0:
    identifiability_margin = 1
```

When two or more process prototypes are exactly identical to the observation, the correct interpretation is the opposite: the best and second-best hypotheses are tied, so the separation margin is zero.

V14a is **not recomputed or rewritten**. Its registered P3 result remains "not supported" under the frozen V14a implementation. The defect is recorded because it can suppress essential-ambiguity counts in exactly degenerate parts of parameter space and is therefore a representation defect relevant to the next generation.

V14a2 fixes the edge case before its first scientific sweep:

```text
if best_distance == 0 and second_best_distance == 0:
    identifiability_margin = 0
```

A contract test requires this behavior. This correction is one reason V14a2 is a named new generation rather than a rerun of V14a.
