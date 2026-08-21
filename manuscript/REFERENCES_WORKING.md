# Reference working index

The earlier free-text working bibliography has been superseded by:

- `REFERENCES_VERIFIED.bib` — publisher/institutionally verified core metadata;
- `REFERENCE_AUDIT.md` — correction log, citation roles and prohibited over-interpretations.

The bibliography remains intentionally selective. Its role is to locate the method relative to disagreement-based acquisition, independent implementations/differential testing, preferential/adaptive ecological sampling, observation error, active learning, simulation-study design and adaptive validation.

## Manuscript citation map

### Introduction — ecological state versus observation process

- MacKenzie et al. (2002): non-detection is not equivalent to absence when detection is imperfect.

### Introduction — preferential/adaptive acquisition can bias the record

- Diggle, Menezes & Su (2010)
- Conn, Thorson & Johnson (2017)
- Henrys, Mondain-Monval & Jarvis (2024)
- Aubry, Francesiaz & Guillemain (2024), where a direct simulation example is useful

### Introduction — neighbouring computational methods

- Seung, Opper & Sompolinsky (1992): Query by Committee / disagreement acquisition
- Avizienis (1985): N-version programming
- McKeeman (1998): differential testing
- Bothmann et al. (2023): active learning in an ecological image workflow

### Methods — simulation and locked validation rationale

- Morris, White & Crowther (2019): structured known-truth simulation evaluation
- Dwork et al. (2015): general danger of adaptive reuse/inspection of holdout evidence

## Boundaries

Preferential-sampling literature motivates sampling-design risk but does not prove the exploration theorem. Occupancy literature motivates the state/detection distinction but does not validate the present observers. Dwork et al. motivates preserving an untouched final validation generation; the present V7 protocol is not an application of the reusable-holdout algorithm.

All final citation metadata should be drawn from `REFERENCES_VERIFIED.bib`, not from older commits of this file.
