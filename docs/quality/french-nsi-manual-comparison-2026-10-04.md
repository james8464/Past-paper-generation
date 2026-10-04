# French NSI manual comparison — 4 October 2026

**Decision: not validated; not suitable for unreviewed classroom use.** This is a
manual product audit, not an examiner or teacher endorsement. No complete live
2027 paper was produced by the source-pinned v10 diagnostic, so its content
cannot be represented as a visually compared live paper.

## Evidence and scope

| Item | Identity | Role |
|---|---|---|
| Official 2026 Métropole, day 1 | `nsi-2026-normal-metropole-jour-1.pdf`; SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b` | Historical structure/layout reference, **not** a complete 2027 scoring template |
| Existing four-page local PDF | `tmp/pdfs/french-fidelity-20260930/sujet.pdf`; SHA-256 `c5002f9cbdbb956dbaea77eb5790c577ac625b4f0dd3a7659f5274956acc5f97` | Synthetic renderer fixture, **not** a successful AI-generated paper |
| Live v10 diagnostic | `tmp/qualification-fr-nsi-2027/diagnostic-20261004-v10-gemma4/benchmark-summary.json`; implementation `edf553526fd68471e56c4f0dd0af2a9011d4f4c70c6ee2e722707156f65daa71`, Gemma digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`, seed 270100 | 0/1 complete papers; raw accepted/rejected exercise drafts retained in its checkpoint |
| Merged-main Qwen diagnostic | `tmp/qualification-fr-nsi-2027/diagnostic-20261004-merged-qwen35/benchmark-summary.json`; implementation `d9b188f103efd02c0ce6dc7ffb5e7456c49aaf2251c9468174455a8e63bb32d1`, Qwen digest `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`, seed 270100 | 0/1 complete papers; all three exercise-1 drafts rejected for invalid credit allocations |

I rendered and inspected all four pages of the local fixture and pages 1–4 of
the official paper. I read the accepted live exercise and the three rejected
database-exercise drafts in their checkpoint. The 2025 and 2024 Métropole day-1
reference PDFs contain 17 and 15 pages respectively; the 2026 paper contains
16. This is context, not a page-count target for 2027.

## Content comparison

The official 2026 paper opens with a detailed network scenario and a labelled,
data-bearing diagram on page 2. Pages 3–4 continue the same situation with
concrete CIDR addresses, a configuration file, a traceroute, and successive
questions whose answers depend on supplied values. The local fixture instead
has six near-identical graph-cost tasks on page 2, six generic database tasks
against a two-column table on page 3, and six generic packet tasks without
data on page 4. It is a renderer smoke test, not a candidate educational
artifact. Its 494 extracted words versus 3,678 in the official paper quantify
the difference in supplied context, but do not alone measure quality.

The rest of the official paper demonstrates why isolated short prompts are
insufficient. Exercise 2 (pages 6–10) develops one nine-token game from binary
state encoding through XOR operations, functions, a configuration graph and
graph-search choice. Exercise 3 (pages 11–16) uses a debate platform for tree
methods and then a relational schema with concrete `SELECT`, self-`JOIN`,
`INSERT`, `UPDATE` and `DELETE` tasks. Later questions reuse definitions,
figures and code supplied earlier. The exercise-level scores are 6, 6 and 8;
the published historical paper does not print a credit beside each subquestion.
The 2027 two-point language rule means that exact 2026 scoring cannot simply
be copied into a new practice profile.

The v10 live attempt is more substantive but still fails correctness:

- Exercise 1, question 1c says the shown breadth-first traversal may stop
  prematurely when a cycle exists. Its code continues while the queue is
  nonempty, skips already visited vertices and therefore does **not** stop
  early because of a cycle. Its answer diagnoses possible duplicate queue
  entries, which is a performance issue, not the claimed failure. The
  automatic item-level review accepted it.
- Question 1d asks for a depth-first trace but invokes an alphabetical tie
  rule for equal *distance*. Distance is not the DFS choice criterion; the
  intended neighbour ordering needs to be stated directly.
- Question 1e requests an entire recursive insertion function for one point.
  Its proposed answer calls `Noeud(valeur)` without defining that constructor
  anywhere visible to the student; the requested API and credit are not
  self-consistent.
- Question 1f juxtaposes a five-key search tree with a 1,000-item unsorted
  list, assumes the tree is balanced without giving its shape, and presents
  logarithmic search as unconditional. That comparison is underspecified.
- All six exercise-1 deterministic item checks remained unresolved. Positive
  AI reviewer flags therefore did not constitute independent proof.
- Exercise 2 failed three times. The first draft did not link named SQL tables
  to questions. The later drafts supplied contradictory figure IDs; manual
  inspection also found an accented SQL relation name in one query not matching
  the declared unaccented table, and a purported SQL error that was actually
  a valid query needing a different task definition. No PDF was published.

These are item-level correctness and marking problems, not cosmetic defects.
The new narrow regression gates reject the observed false cycle diagnosis,
undefined `Noeud` constructor and unsupported logarithmic BST advantage; they
do not prove other algorithm questions correct. A stronger executable witness
for debugging claims and human review remain necessary.

The subsequent Qwen run also published no PDF. Its first draft assigned zero
credit to one marking criterion, the second had the same error, and the third
had marking credits that did not sum to the question's planned points. Manual
inspection of its rejected first draft found self-editing language inside a
question ("Non, reformulons"), an asserted route contradicted by its own graph,
and a non-rectangular table. Those drafts are evidence of failure, not a basis
for visual qualification. A bounded, hash-recorded marking-only repair has
been added for future runs; it does not silently alter points or certify the
meaning of marking criteria.

## Visual comparison

Both PDFs use A4 geometry (about 595 × 842 points). The local cover resembles
the official cover's centred hierarchy, but its practice/non-official status
and independent footer must remain conspicuous. The fixture puts each short
exercise on one largely empty page. The official pages use denser, staged
paragraphs, subheadings, monospaced code/configuration, figure captions and
explicit numbered tasks. The fixture graph is small, sparse and uncaptioned;
the official page-2 network diagram occupies a substantial part of the page
and its labelled elements are used by later questions. The current renderer
fixture therefore cannot establish realistic pagination, code wrapping,
diagram legibility or page-to-page continuity for a full AI paper.

The official 2026 paper supplies no official detailed correction in this local
comparison. I did **not** score the proposed marking material against an
official scheme or claim official marking equivalence. The 2027 practice
profile has a distinct indicative two-point language component; the 2026
paper is historical and cannot prove its precise 2027 presentation.

## Release gate

Do not call the French route a validated product. First obtain a complete
identity-pinned live paper, inspect every page and every solution against its
own data and relevant official references, run the predeclared model/task
matrix, and resolve all high-severity defects. Then arrange the planned two
independent French NSI teacher reviews on six stratified papers. Learner
timing/difficulty calibration and accessibility/hardware checks remain
separate gates. A self-audit can reject defects; it cannot manufacture those
external approvals.
