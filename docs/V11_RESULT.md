# V11 result — naive contradiction-state localisation failed

## Locked outcome

The first preregistered V11 run is retained as a negative result.

- workflow run: `32696262650`;
- protocol SHA-256: `af358226f4afccff3bb148e90a30c5fe9a25c2170d3f223497a22fb3dd685080`;
- canonical result SHA-256: `654d0be81c459f11d35b37ca91fa7251f395e352a31f44993384bac92b1107c1`;
- artifact ZIP SHA-256: `e8a6d2fe913250a7a6e26fb968aeb6083356f724ebeaa55476ef6ba30f143428`;
- two complete runs under `PYTHONHASHSEED=11` and `97` were byte-identical;
- preregistered claim level: **D — no general localisation advantage**.

## Strategy results

| Strategy | Held-out localisation | Wrong-module intervention | Shared blind-spot discovery | No-fault false intervention | Stable-falsification probes | Repair positive transfer | Relative loss reduction |
|---|---:|---:|---:|---:|---:|---:|---:|
| contradiction-guided | 0.3469 | 0.8707 | 0.2511 | **0.0000** | 5.5903 | 0.1963 | 0.0953 |
| early scalar fusion | **0.5058** | 0.6448 | 0.4111 | 0.0422 | **4.9608** | 0.4737 | 0.2228 |
| event-only | 0.3497 | 0.6930 | 0.2489 | 0.5222 | 5.5731 | 0.5085 | 0.1858 |
| observability-only | 0.4475 | **0.5648** | **0.6744** | 0.5156 | 5.3692 | **0.6756** | **0.2745** |

The tested contradiction-guided representation therefore fails its own preregistered claim ceiling. It cannot be described as superior development guidance.

## What was falsified

V11 operationalised contradiction-guided development as:

1. retain event-evidence and observability-risk channels separately;
2. discretise them into four high/low diagnostic states;
3. expose a deterministic protected audit for some otherwise blind probes;
4. train a fixed nearest-centroid failure classifier on one mechanism subtype per failure class;
5. evaluate on a distinct held-out mechanism subtype;
6. choose a repair module from the predicted failure class.

That **specific operationalisation did not transfer**. In particular, the four-state/raw-channel representation did not make the held-out cause sufficiently identifiable. Shared-blind-spot discovery was only 0.251 and most non-null cases were sent to the wrong repair module.

## What was not falsified

This result does not show that early fusion is generally preferable, nor that separate observers are useless. The early-fusion strategy merely matched the geometry of this synthetic transfer problem better. Observability-only performed best on the held-out shared-failure subtype, indicating that the chosen held-out failure happened to remain strongly represented in the observability channel.

V11 also does not alter the independent facts already established elsewhere:

- fixed disagreement allocation was falsified in V5;
- the frozen 50/10/40 allocation failed locked V7;
- protected random exploration has analytical sampling guarantees;
- V9 supports protected exploration as a design-valid ecological reference sample;
- V10 is a separate real-pixel observability-transfer experiment.

## Diagnostic implication

The failure narrows the next hypothesis. **Observer disagreement or a four-quadrant state is not automatically cause-identifying.** A useful contradiction-guided development method needs interventions whose causal targets are known independently of the observer outputs.

Therefore the next generation should not tune V11 feature weights or classifiers. It should test a narrower causal proposition:

> When biological-event and observation-process factors are manipulated independently, does preserving their observer outputs separately help select the correct causal intervention and detect shared failures on fully held-out physical blocks?

That is a V12-style controlled physical / semi-physical validation question. V11 remains frozen as the falsification that motivates that change in experimental design.
