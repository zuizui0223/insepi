# V14b nuisance observer process-scale prefreeze

## Current location

The target observer is frozen after validation v2. This generation modifies only the nuisance observer.

The corrected V14a2 diagnosis showed that the frozen nuisance score ranks nuisance-only vs target-only perfectly (AUC 1.0) but almost never crosses the inherited 0.55 operational threshold (recall 0.015625). This is a score-scale mismatch rather than missing ranking information.

## Representation correction

The previous nuisance route multiplied positive nuisance-process evidence by nuisance observation support. That collapsed two conceptually distinct questions:

1. does the observed motion have nuisance-process structure?
2. was the nuisance process sufficiently sampled/covered to interpret it?

V14b separates them.

Positive nuisance-process evidence requires both:
- spatial coherence;
- restorative or stationary temporal structure.

The process support is their geometric mean. Sampling/window adequacy remains a separate nuisance-observation-support quantity.

## Freeze boundary

No target observer code or target-side semantics may change in this generation. The inherited 0.55 threshold is retained only as a development gate so the score-scale correction can be tested without post-result threshold tuning.

The low-spatial-coherence (`Pi5 < 1`) region is not required to become nuisance-positive. Residual ambiguity there is allowed.

## Validation before result

Fresh seeds 91001–91032 are fixed. Validation is limited to temporally resolved focused-grid coordinates.

Required before nuisance freeze:
- AUC nuisance-only vs target-only >= 0.90;
- AUC nuisance-only vs target-coupled >= 0.90;
- recall >= 0.80 at 0.55 for coherent nuisance (`Pi5 >= 1`);
- FPR <= 0.05 on target-only;
- FPR <= 0.05 on target-coupled;
- no new nuisance-side contradiction type.

No training or threshold search is allowed.
