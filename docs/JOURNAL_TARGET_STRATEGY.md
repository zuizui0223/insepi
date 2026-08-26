# Journal target strategy for the simulation-only methods paper

## Primary target — Methods in Ecology and Evolution

The current paper architecture is best aimed first at **Methods in Ecology and
Evolution (MEE)** if V7 supports at least a substantive methodological claim.

MEE explicitly prioritises new methods and methodological approaches over the
biological results of applying them. Its current author guidance also states that
new computational methods normally should be tested using simulations or benchmark
data and that broad applicability across taxa/systems should be demonstrated.

That fits the intended paper only if we frame the contribution at the sensing and
measurement-design level rather than as flower-visitor software.

### What MEE requires from this project

1. **Method, not workflow glue.** The paper cannot read as PolliPi + InsePi wired
   together. The methodological object must be the contradiction-guided,
   exploration-guarded sensing architecture and its falsification protocol.
2. **General property simulation.** V7 should test broad disturbance/process
   properties, not only hand-crafted flower scenes.
3. **Formal properties.** The exploration-guard theorem should be part of the main
   method, not hidden in supplement.
4. **Broad transferability.** Camera traps, acoustic sensing, nests, phenology and
   interaction monitoring should be described as domains sharing the same
   observation-process problem, without claiming untested accuracy.
5. **Reproducible implementation.** Source commits, canonical pixels, traces,
   deterministic locks, hashes and runnable examples must be easy for another
   group to use.
6. **Clear domain of applicability.** State when exploration-guarded dual-observer
   allocation is appropriate and when a simpler uniform or single-observer policy
   is sufficient.

### MEE claim threshold

- V7 Level A: strong MEE Research Article candidate.
- V7 Level B: still plausible if the conditional regime/domain is scientifically
  clear and the theory/general framework remains strong.
- V7 Level C: possible but would need the exploration-guard theory and preferential
  sampling connection to carry more of the paper.
- V7 Level D/E: MEE becomes less certain unless contradiction-guided method
  development is shown to generalise convincingly beyond these two programs.

## Secondary target — Ecological Informatics

**Ecological Informatics** is a strong second target if the final emphasis is more
on autonomous sensor architecture, image-based monitoring, edge data acquisition,
uncertainty and software evaluation.

Its scope explicitly includes novel concepts/tools for ecological monitoring,
sensor- and multimedia-based data acquisition, digital image processing and
uncertainty analysis.

Compared with MEE, the manuscript could retain more implementation detail about
edge-camera contracts, trace provenance and monitoring infrastructure.

### When to prefer Ecological Informatics

- V7 yields a useful sensor-engineering result but weaker broad methods theory;
- reviewers are likely to see the contribution primarily as computational
  monitoring architecture;
- field deployment/software implementation becomes a larger share of the paper;
- the generality argument is strongest across sensing systems rather than across
  ecological inference methods.

## Manuscript adaptation by target

### For MEE

Lead with:

```text
measurement process -> adaptive sampling bias -> epistemically distinct observers
-> locked falsification -> exploration guard -> general method properties
```

Keep Raspberry Pi / flower-camera details as implementation examples or supplement.

### For Ecological Informatics

Lead with:

```text
edge sensing constraints -> target/noise observer separation -> provenance-safe
same-pixel benchmark -> finite-budget allocation -> OOD sensor disturbances
```

Retain more architecture diagrams and runtime details.

## Simulation-reporting standard

MEE has published guidance emphasising simulation-based validation of complex
methods and transparent reporting of simulation studies. The current repository
already contains unusually strong ingredients for this standard:

- explicit data-generating process;
- deterministic scenario registries;
- known latent truth;
- development versus locked-validation generations;
- negative results retained;
- comparator/ablation registry;
- paired Monte Carlo worlds;
- multiple evaluation metrics rather than one accuracy score;
- source and artifact hashes;
- pre-result claim ceilings.

The manuscript should present these as part of methodological rigor, not as GitHub
implementation trivia.

## What must be strengthened before MEE submission

1. Finish one-shot V7 without contaminating it.
2. Demonstrate broad property-level disturbance coverage rather than biological
   realism alone.
3. Show the exploration theorem in the main text.
4. Provide at least one minimal tutorial/example showing how a third observer pair
   could implement the same contracts, even if no new empirical dataset is used.
5. Separate observer-relative detection-error recovery from observer-independent
   disturbance coverage in all figures and tables.
6. Make the applicability decision explicit:
   when should a user choose uniform, single-observer, or dual-observer guarded
   allocation?

## Current recommendation

Prepare the manuscript to **MEE standards first**. This forces the method to be
broader and more theoretically explicit. If the eventual V7 claim ceiling or
editorial fit is weaker than hoped, the same package can be rebalanced toward
Ecological Informatics without changing the locked scientific evidence.
