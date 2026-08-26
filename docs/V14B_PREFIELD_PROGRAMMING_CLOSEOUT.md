# Visible interaction, latent noise, and the observational third state

## Result

The pre-field programming result is closed at V14b. In one frozen synthetic
universe, an interaction-directed target process and an exogenous nuisance
process are generated independently, may coexist, and are read by independently
frozen target and nuisance observers. Their final intersection is retained as a
reason-tagged undetermined state rather than forced into target absence.

The result supports this bounded claim:

> Rejection is not adequately represented by one unconditional model-failure
> rate. In the frozen closed-world generator, it is a reason-tagged estimand over
> observation conditions and process regimes. It must therefore be measured as
> a phase surface and must not be silently recoded as target absence.

This does not claim that every rejection is desirable. Model inadequacy can also
produce rejection. The contribution is the separation needed to ask which part
is observation-conditioned and which part remains a model-development problem.

## One universe, two process families, one observation layer

The physical state is one of:

- baseline;
- target only;
- nuisance only;
- target with a target-caused local response;
- target and nuisance superposed;
- target, nuisance and target-caused response combined.

The target generator is a localized entry--dwell--exit actor process. It may
trigger a local scene response after interaction. The nuisance generator is a
stationary mean-reverting spatiotemporal field whose generation is not
conditioned on the target event. "Interaction-directed" is an operational
generator definition; the simulation does not infer animal intention.

Observation support is conceptually separate from physical state. An unavailable
view is not a third physical cause. If the view is unavailable, a quiet scene
cannot safely be called baseline and a moving scene cannot safely be assigned to
target or nuisance.

The frozen V14b measurement does not fully cross an explicit unavailable-`O`
factor with every physical state. It measures deviation-side U; baseline remains
`no-query` and is retained in partial-identification width rather than silently
treated as target absence. V15 implements a separately measured `O` layer in
software, but that estimator remains pre-data and uncalibrated. Therefore the
cross-state observation layer is part of the programming architecture, not a
completed V14b simulation result.

## Independent evidence and final intersection

The target observer reads the direct actor channel and retains an indirect-only
local response as unattributed. The nuisance observer reads positive spatial and
temporal nuisance-process structure while keeping nuisance observation support
separate. Neither observer consumes the other's output.

Their frozen intersection produces:

- `baseline`: no dynamic attribution question is triggered;
- `target`: only target evidence is supported;
- `nuisance`: only nuisance evidence is supported;
- `U_information_absent`: a deviation is visible but neither process is safely
  supported;
- `U_overlap_or_attribution`: both processes are supported, or only an
  unattributed local response is available.

Simultaneous target and nuisance processes are legitimate physical
superposition. `U_overlap_or_attribution` appears only because the requested
final attribution is exclusive.

## Estimand

The primary object is

```text
R_U(pi, z) = Pr(decision = U | Pi1,...,Pi6, latent regime z).
```

The reported marginal surface uses the prefrozen equal weighting of regimes and
measurement seeds. It is not a universal field rejection rate; changing field
prevalence would change the marginal.

The two reason-specific surfaces are measured separately. Visit presence is
partially identified by a lower bound equal to definite target rate and an upper
bound equal to one minus definite nuisance rate. Its width is baseline rate plus
total U rate.

## Frozen evidence

The one-shot surface contains 30,625 coordinates, 183,750 coordinate-regime
rows and 5,880,000 simulated worlds. The canonical and cached-equivalent runs
produced the same phase-surface SHA-256:

```text
1d2c7c1f8f7370aad3cdde4d9d9d47bf318b2a057b6f788d3a48df9ea8d16c34
```

Across the prefrozen uniform grid and regime weighting:

- total U rate was `0.253336`;
- `89.44%` of U was overlap/attribution and `10.56%` was information absence;
- mean partial-identification width was `0.483569`;
- the specified binary coercion had false-positive rate `0` and false-negative
  rate `0.3569`.

That binary result applies only to the prefrozen rule mapping U and baseline to
target-absent. It is not a proof of superiority over every possible binary
classifier.

## Observation-conditioned geometry

The strongest measured boundary was structural availability of the direct actor
channel. In target-present worlds, `Pi3=0` versus positive `Pi3` changed:

| Quantity | `Pi3=0` | positive `Pi3` mean |
|---|---:|---:|
| U rate | 0.453723 | 0.196100 |
| forced-binary false-negative rate | 1.000000 | 0.196100 |
| partial-identification width | 0.803875 | 0.196100 |

U also varied across observation-window `Pi1`, relative-timescale `Pi2`, and
sampling `Pi6`. More observation did not simply drive U downward: added evidence
could expose process coexistence and move cases from hidden/baseline states into
overlap/attribution U. This is why total U cannot be interpreted as an
unconditional defect count.

The predicted sharp `Pi2` critical ridge was not found. `Pi2` showed only a
shallow nonmonotonic maximum near one. This negative result is retained; the
dominant boundary was direct actor-channel availability rather than a universal
target--nuisance timescale collision.

## Reproduction and freeze boundary

The closeout is rebuilt only from committed JSON evidence:

```text
python scripts/build_v14b_prefield_programming_closeout.py \
  --output rebuilt_closeout.json
```

The builder verifies the locked surface identity, world count, family-wise
alpha, nuisance threshold, observer-retuning flag and all four freeze rules. It
does not execute the simulator or either observer. Canonical JSON hashes make
the verification independent of checkout newline conventions.

The interaction-directed wording is an explicit post-result operational
synthesis of the prefrozen generator and estimand. It adds no acceptance
threshold and does not upgrade the result to animal-intention recognition,
field prevalence, field accuracy or a universal observation threshold.
