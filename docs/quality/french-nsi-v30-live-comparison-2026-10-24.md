# French NSI V30 live comparison - 24 October 2026

## Verdict

The targeted reasoning and response-flow change passes engineering review. E1 now progresses from route analysis to complete algorithm construction, a prefix-minimum invariant, boundary cases and the limits of a catalogue optimum. This replaces two repeated outage traces. Overall qualification remains **HOLD** pending materially different task-family variants and final supported-route live/manual evidence. This is not teacher validation, learner calibration or model-independent equivalence.

## Frozen-source live evidence

Exactly one live run used clean source `3316fbc`, implementation SHA-256 `639055d30d5f6fb3ed138d83a02aa13d219f4f55caed45b9b1f96dfe791478d6`, model `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, seed `270100`, and reference-index SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594`. It passed first attempt with zero repairs, completing at `2026-10-24T00:26:18.664312+00:00` in 142.287 seconds. Backend peak RSS was 136,036,352 bytes, excluding Ollama. Source was unchanged during generation.

The subject has 12 A4 pages and 34 questions; the proposed correction has 24 pages. Three independent written exercises, 18 technical points and a distinct 2-point indicative language rubric remain. All attempts, events, PDFs and renders remain ignored under `tmp/pdfs/french-v30-route-selection-20261024/`. Earlier live evidence and replay packages are preserved. No official PDF is bundled.

| Artifact | SHA-256 |
|---|---|
| Subject | `c2e2c9426f2ef8fc1fd34cbbc1dc26cbca500ea01791089885e3bb67bfd773a2` |
| Correction | `6fb6be6687b2f48ca623ef043c8c3db1a16c3e92df2d461323f934e4eb8b65e6` |
| Assessment | `1d8ccde5dabefa8dc1851b3ce74271f48955b3cc92787d14495cc8030134bd01` |
| Manifest | `dc335f7e5fa2a0ba24ead36bea354af4ed2069112eb55baf20856fb947767314` |

## Official comparison and correctness

Re-viewed the registered 2026 Metropole day 2 page 16 (PDF SHA-256 `885f3687ea83486efb9a17c08467a5fed6f7b11fb629ca65ba103240ddd37db9`). It progresses from a supplied graph-distance helper to constructing eccentricity and justifying a meeting-point decision. V30 uses that level of progression as a comparison, not its scenario or code: filter undirected closures, construct a minimum selector, justify its invariant and distinguish a catalogue minimum from a global graph minimum. The official paper also has legitimate whitespace; matching its 16 pages is not a quality target. This is a scoped fresh official comparison, not a new every-page audit or an official-correction comparison.

For this printed catalogue, independently summed costs are 23, 26, 30 and 52. Availability after A-B closes is no/yes/yes/yes; after E-F also closes it is no/no/yes/yes. The selected index is 2. Strict improvement preserves the first tied index; empty or wholly blocked catalogues return None. The helper checks both orientations and neither function mutates inputs. The four quarter-point criteria cover filtering/initialisation, strict minimum/ties, invariant/empty case/no mutation, and concrete result/global limitation. Assigned marks and times remain indicative, not calibrated.

## Every-page rendering review

Poppler 80-dpi renders were compared byte-for-byte with final V29 renders. Subject pages 1-3 and 6-12 and correction pages 1-3, 5, 9-24 are identical; their individual findings in the V29 comparison carry forward by exact image identity. All six changed pages were viewed directly:

| Page | Finding |
|---|---|
| Subject 4 | Blank catalogue, 1f exclusions, complete helper and full 1g construction/justification prompt together. No answer leakage. |
| Subject 5 | Tree, insertion, traversal and recursive construction remain together. Literal inline backticks removed from 1h/1i. Lower whitespace is retained, not padded. |
| Correction 4 | Initial Dijkstra facts unchanged; two quarter-point criteria retain distance and predecessor requirements for both fixations. |
| Correction 6 | Catalogue, all four cost/availability answers and 1f credit readable; supplied helper is whole. |
| Correction 7 | 1g instructions continue, then a labelled answer with whole selector, invariant, boundary/result explanation and all credit together. |
| Correction 8 | Tree/insertion/traversal and 1j prompt readable; inline backticks removed. Whole recursive answer and credit remain on unchanged page 9. |

No clipping, overlap, missing source or missing credit was observed. Normal and large-print content/word-bound tests supplement visual inspection. Subject page 4 is text-dense but readable; this does not establish learner timing or accessibility qualification. Correction continuation is labelled; no blank page was added.

## Verification and limits

The local full suite passed **2,948 tests, 2 skipped**, with five existing SWIG warnings, before final PDF task-ID/contract/phase tightening. Final targeted route/runtime tests passed **43 tests** after that tightening and added redaction/mutation assertions. Protected CI must verify the final PR head. Ruff, release compliance and diff checks passed. Retained V26, final V28 and final V29 replay passed; none is a new live run. Graphify AST was refreshed (8,986 nodes, 25,575 edges); 40 JSON sources yield no nodes and semantic document extraction was not refreshed.

Read-only self-review covered version dispatch, canonical evidence, independent enumeration, ties, reversed closures, empty/all-blocked inputs, preservation, marks/time, historical replay and PDF source/answer binding. This is not independent external review.

Next engineering work is substantive task-family variation across seeds, followed by frozen-source French and supported UK-route qualification. Accounting, Economics and Business findings need final-source evidence. The expensive final matrix remains gated while French fidelity is HOLD. Teacher review, learner calibration, per-document rights and accessibility qualification remain external. No full-app finalisation or Apple/school/regional approval is claimed.
