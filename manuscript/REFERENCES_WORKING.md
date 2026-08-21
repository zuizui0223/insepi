# Working references for the standalone methods manuscript

This bibliography is deliberately small at the pre-V7 stage. Each entry is here
because it supports a specific conceptual distinction in the manuscript. Final
submission should verify journal style, page ranges, author lists and DOI metadata
against Crossref/publisher records.

## Disagreement-based acquisition

### Seung, Opper & Sompolinsky (1992)

Seung, H.S., Opper, M. & Sompolinsky, H. (1992). Query by committee. In
*Proceedings of the Fifth Annual Workshop on Computational Learning Theory*,
287–294. DOI: `10.1145/130385.130417`.

**Used for:** the neighbouring idea in which disagreement among committee members
is itself an acquisition criterion.

**Contrast with this paper:** our observers do not estimate one equivalent target;
V5 explicitly falsifies the assumption that their fixed scalar disagreement should
be a prevalence-robust acquisition priority.

## Independent implementations and software discrepancy

### Avizienis (1985)

Avizienis, A. (1985). The N-version approach to fault-tolerant software. *IEEE
Transactions on Software Engineering*, SE-11(12), 1491–1501.

**Used for:** independently developed program versions in fault-tolerant software.

**Contrast:** N-version designs seek redundancy for a shared specification,
whereas our observers intentionally encode non-equivalent scientific questions;
majority consensus is not the goal.

### McKeeman (1998)

McKeeman, W.M. (1998). Differential testing for software. *Digital Technical
Journal*, 10(1), 100–107.

**Used for:** same-input divergence as a way to expose implementation or
specification problems.

**Connection:** contradiction-guided development is closest in spirit to
differential testing, but the compared programs are intentionally different
observation models rather than equivalent compilers/implementations.

## Preferential and adaptive sampling in ecology

### Diggle, Menezes & Su (2010)

Diggle, P.J., Menezes, R. & Su, T.-l. (2010). Geostatistical inference under
preferential sampling. *Journal of the Royal Statistical Society: Series C
(Applied Statistics)*, 59(2), 191–232. DOI:
`10.1111/j.1467-9876.2009.00701.x`.

**Used for:** sampling locations/effort becoming stochastically related to the
process being inferred, and the resulting danger of naive inference.

### Conn, Thorson & Johnson (2017)

Conn, P.B., Thorson, J.T. & Johnson, D.S. (2017). Confronting preferential
sampling when analysing population distributions: diagnosis and model-based
triage. *Methods in Ecology and Evolution*, 8(11), 1535–1546. DOI:
`10.1111/2041-210X.12803`.

**Used for:** ecological diagnosis of preferential effort and the importance of
random/systematic designs where feasible.

### Henrys, Mondain-Monval & Jarvis (2024)

Henrys, P.A., Mondain-Monval, T.O. & Jarvis, S.G. (2024). Adaptive sampling in
ecology: Key challenges and future opportunities. *Methods in Ecology and
Evolution*, 15(9), 1483–1496. DOI: `10.1111/2041-210X.14393`.

**Used for:** current ecological framing of adaptive sampling, including the
challenge that targeted collection can make raw observations non-representative.

### Aubry et al. (2024) — optional supporting citation

Aubry, P., Francesiaz, C. & Guillemain, M. (2024). [Final title metadata to be
checked before citation.] *Ecological Modelling*, 492, 110707. DOI:
`10.1016/j.ecolmodel.2024.110707`.

**Potential use:** simulation evidence that preferential sampling can bias
population/mean estimates and that the effect depends on sampling effort.

**Status:** do not cite in final manuscript until title/author metadata are
reverified.

## Active learning in ecological image workflows

### Bothmann et al. (2023)

Bothmann, L. et al. (2023). Automated wildlife image classification: An active
learning tool for ecological applications. *Ecological Informatics*, 77, 102231.
DOI: `10.1016/j.ecoinf.2023.102231`.

**Used for:** ecological image analysis as an area where active selection can
reduce annotation effort.

**Contrast:** label-efficiency active learning and observation-design validity are
different objectives; our method concerns what the sensing system acquires or
audits under a finite budget.

---

# Citation logic by manuscript paragraph

## Introduction paragraph 2 — adaptive acquisition can bias the record

Primary citations:

- Diggle et al. 2010
- Conn et al. 2017
- Henrys et al. 2024

## Introduction paragraph 4 — neighbouring computational methods

- Seung et al. 1992 — disagreement acquisition / Query by Committee
- Avizienis 1985 — independent program versions / consensus fault tolerance
- McKeeman 1998 — discrepancy-based software testing
- Bothmann et al. 2023 — ecological active learning example

## Discussion 4.3 / 4.5 — exploration as measurement design

- Diggle et al. 2010
- Conn et al. 2017
- Henrys et al. 2024

Do not cite preferential-sampling papers as if they prove the exploration theorem;
they motivate the sampling-design problem. The theorem follows directly from the
mixture definition used in this paper.

---

# References still worth adding before submission

The final bibliography should be expanded selectively, not with a broad generic
camera-trap review dump. Priority searches:

1. ecological observation-error / imperfect detection literature that cleanly
   distinguishes biological state from observation process;
2. design-based or model-assisted inference under adaptive/preferential sampling;
3. edge/ecological camera methods that make acquisition decisions before storage;
4. active sensing / constrained acquisition methods with explicit exploration
   guarantees;
5. reproducible simulation or benchmark-overfitting literature relevant to locked
   generational validation.

Any added citation should have an explicit role in the argument and should not be
used to claim novelty by omission.
