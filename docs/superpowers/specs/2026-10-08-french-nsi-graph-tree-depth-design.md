# French NSI graph/tree depth — versioned design

Status: implementation design, 8 October 2026. This is not a claim that a paper
has passed teacher review or examination-fidelity assessment.

## Purpose and boundary

The pinned V16 live paper passed engineering checks but remains on a manual
fidelity hold: its first exercise has six short questions across two pages,
whereas the official 2026 Métropole comparator develops its first exercise over
four pages. Page count and question count are comparison signals, not 2027
rules. The aim here is to give the existing original graph/BST case a
substantive, checkable reasoning sequence, without padding it with unsupported
facts or copying an official question. Exercise 2, Exercise 3, the UK routes and
all earlier French package identities remain unchanged.

## Decision

Introduce written prompt version `fr-nsi-written-2027-v17` with a separate
immutable Exercise 1 depth contract and finite French prose. Leave the V16
graph/tree contract and its six-question catalogue byte-for-byte compatible
for package replay. V17 alone uses ten questions, `1a`–`1j`, in three parts:

| Part | Questions | Required reasoning |
|---|---|---|
| A · weighted graph | 1a–1d | Read neighbours/degree and incident costs; add the weights of the displayed detour A–C–E–F; trace initial Dijkstra relaxations with predecessors; derive and justify the minimum A–F route. |
| B · breadth-first traversal | 1e–1g | Show queue/visited state after two dequeues; identify and repair the fixed `visin` NameError; give the corrected full visit order and explain why marking visited before enqueue prevents repeats. |
| C · binary search tree | 1h–1j | Trace insertion and identify the child position; compute inorder after insertion; correct a fixed one-line comparison error in an app-owned BST search function, then trace a search for the inserted key and explain the ordering invariant. |

The displayed graph remains six vertices and nine weighted edges; the BST
remains five keys plus an insertion key. The contract derives every expected
value, including Dijkstra intermediate state, chain cost, BFS queue state,
insertion and search correction, from these application-owned facts. Model
output selects only scene and wording IDs and echoes claimed results; it cannot
invent graph edges, code, marks or correct answers. A full candidate question,
solution and indicative rubric are rendered by the application. Canonical
answers are exact and carry quarter-point criteria; their wording is not
treated as human approval.

For each allocation (5.5, 6 or 6.5 technical points), all ten questions
receive 0.5 point. Question 1c receives another 0.5 for every allocation;
question 1e receives another 0.5 at 6 or 6.5; question 1j receives another
0.5 at 6.5. Thus the first-exercise total remains exact and the three-exercise
paper still sums to 18 technical points plus a distinct indicative two-point
French-language component. Exercise 1 keeps its 70-minute estimate; question
time estimates sum to 70 and are not claims of measured learner timing.

## Interfaces and compatibility

- `GraphTreeDepthContract` is a new immutable canonical JSON record. Its
  constructor derives facts from the pinned seed and the existing app-owned
  graph/BST generator, recomputes every expected result, and rejects a changed
  field or mismatched seed. It never executes model-submitted code.
- A separate V17 catalogue exposes a finite selection schema for `1a`–`1j`,
  validates every ID/form, and renders native French prompts, canonical answers
  and quarter-point indicative rubrics. Every printed claim must be supported
  by the contract and checked during package validation/replay.
- Prompt, contract, catalogue digest, reference-index hash, source version and
  output hashes remain part of evidence identity. V16 and older packages
  dispatch to their old handlers; V17 rejects unknown or mixed identities.
- Runtime, PDF, CLI and benchmark dispatch advertise V17 only when every gate
  knows its contract. No UK source fallback or practical-component claim.
- PDF flow must keep each question with its leading answer space and identify
  rubric continuations by question ID. No forced whole-block pagination that
  creates mostly blank pages. Standard and large print both need measured
  bounds and visual inspection.

## Acceptance and limits

Tests first: deterministic seed range, malformed/tampered contracts, exact
credits and timing, schema rejection, native French rendering, identity/replay,
old-package compatibility, UK smoke tests, PDF bounds and continuation labels.
Run full backend/macOS protected checks and a read-only review before merge.
Only after the shared source is stable, run one pinned local-model V17 diagnostic,
retain all attempts and hashes, inspect every generated page against the
official comparator, and update the English Occitanie evidence truthfully.

Neither more questions nor a clean automated pass qualifies the paper by
itself. Independent French NSI teachers, learner time/mark calibration, rights
clearance and accessibility evaluation remain explicit external gates. The
written component alone is in scope.
