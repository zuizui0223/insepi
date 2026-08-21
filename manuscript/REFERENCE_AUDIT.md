# Reference metadata audit

Core conceptual references were checked against publisher, institutional or bibliographic records before final V7 execution. `REFERENCES_VERIFIED.bib` is the canonical working bibliography for the manuscript.

## Corrections to the earlier working list

- **Avizienis (1985):** formal DOI is `10.1109/TSE.1985.231893`.
- **Aubry, Francesiaz & Guillemain (2024):** title verified as *On the impact of preferential sampling on ecological status and trend assessment*, *Ecological Modelling* 492, 110707; it is no longer an unresolved optional-title placeholder.
- **Bothmann et al. (2023):** full nine-author list verified; *Ecological Informatics* 77, 102231.
- Diggle et al. (2010), Conn et al. (2017), Henrys et al. (2024), Seung et al. (1992), and McKeeman (1998) metadata were checked against publisher/institutional or DBLP records.

## Selective additions

Three references were added because they close specific conceptual gaps rather than broaden the bibliography indiscriminately.

1. **MacKenzie et al. (2002)** — supports the ecological distinction between biological state and observation/detection process. Use when motivating why non-detection is not equivalent to biological absence; it does not validate the present visual observer.
2. **Morris, White & Crowther (2019)** — supports structured simulation studies with known truth for evaluating methods. Use in the simulation-design section; the present locked-generation scheme is an implementation choice beyond their ADEMP guidance.
3. **Dwork et al. (2015)** — supports the general problem that repeated adaptive inspection of a holdout compromises naïve validation. Use only to motivate why a new untouched generation is required after development; do not imply that our V7 mechanism inherits the reusable-holdout theorem.

## Citation-role constraints

- Preferential-sampling papers motivate the observation-design problem; they do **not** prove the exploration-guard identities.
- Query by Committee demonstrates disagreement-based acquisition for models targeting a common task; it does **not** describe epistemically non-equivalent observers.
- N-version programming and differential testing motivate independent implementations/discrepancy detection; they do **not** establish ecological sampling validity.
- Occupancy literature motivates the state-versus-detection distinction; it does **not** turn `hidden_error_recall` into an observer-independent latent state.
- Simulation/holdout papers motivate known-truth evaluation and separation of development from final validation; they do **not** determine the V7 pass thresholds.

## Remaining reference work after V7

Only outcome-dependent citations should be reconsidered after V7. Do not add literature merely to reframe a failing locked result. Final formatting should be generated from `REFERENCES_VERIFIED.bib` using the journal style, and all DOI strings should be checked once more at submission time.
