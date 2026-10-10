# French NSI graph resilience V20 — versioned design

Status: approved-scope engineering design, 10 October 2026. It is not teacher, examiner or learner approval.

## Purpose and decision

The pinned V19 written subject passed automation but remains a manual fidelity hold: Exercise 1 ends with four compact questions on a sparse page, and its graph, breadth-first-search code, tree and search code are all introduced before the related tasks. The official 2026 Métropole paper is a comparator, not a 2027 page-count template. The next increment will make one original app-owned Exercise 1 case more sustained and place each source next to the reasoning it supports. It will not add blank pages or claim that matching the official page count proves quality.

V20 changes Exercise 1 only. Exercises 2 and 3 retain their V19 and V18 locked data, questions and credit. UK routes and V13–V19 checkpoints/packages remain readable under their original version identities. This is a separate, testable increment rather than a simultaneous rewrite of three exercises.

## Candidate sequence and app-owned facts

Exercise 1 remains a 70-minute, ten-question case involving the weighted six-vertex network, a breadth-first traversal, then a distinct binary search tree used by the same service. The case is staged:

| Stage | Questions | Candidate evidence |
|---|---|---|
| A: initial routes | 1a–1d | Read the degree of A; add the weights of a specified detour; complete two Dijkstra fixations with distances and predecessors; justify the initial minimum route. |
| B: traversal | 1e–1f | Trace the first two queue removals and full BFS order; identify and repair the one misspelled name in the supplied algorithm. |
| C: resilience | 1g | After one specified link on the initial minimum route is closed, exclude that link, derive a new minimum route and its weight, and compare it with the initial route. Equal total weights are possible and must be reported honestly; a different route is required. |
| D: tree | 1h–1j | Insert the fixed key by tracing comparisons, derive the infix order, then repair and trace the supplied search function. |

The new immutable V4 graph-resilience contract derives from the existing V3 graph/tree facts but does not edit the V3 contract. It selects the middle edge of the canonical initial A-to-F minimum path as the closed link, recomputes the altered graph with the deterministic tie rule, and stores the before/after paths, weights and BFS states in canonical JSON. The nine-link ladder remains connected after any one link closes. Construction rejects a changed seed, edge, route, predecessor, tree or source-code fact. The model only selects a finite scene and question/rubric wording IDs; it never supplies facts, executable code, answers or marks. No model-submitted SQL or Python is run.

Candidate materials appear at the point of use: the graph and faulty BFS listing with A/B; the outage statement with 1g; the tree table and short node-attribute legend with 1h; and the faulty search listing with 1j. The unused full `Noeud` class listing is omitted from the V20 candidate, not moved merely to occupy a page. Locked answers remain in the proposed correction only. PDF text and bounds checks must catch a missing or interchanged source, a lost question, answer leakage and an answer/credit orphan in normal and large print.

## Exact scoring and boundaries

The E1 technical allocation is still 5.5, 6 or 6.5 points according to the route's existing seed profile. The V20 ten-question profile is:

| Total | 1a | 1b | 1c | 1d | 1e | 1f | 1g | 1h | 1i | 1j |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.5 | .25 | .25 | 1 | .5 | .5 | .5 | 1 | .5 | .5 | .5 |
| 6 | .25 | .25 | 1 | .5 | 1 | .5 | 1 | .5 | .5 | .5 |
| 6.5 | .25 | .25 | 1 | .5 | 1 | .5 | 1 | .5 | .5 | 1 |

At 1a the prompt asks only for degree, not also neighbours and incident-weight sum; 1b asks for the cost of the named detour. The four quarter-point criteria at 1g cover removal of the specified link, the new route, its calculated weight, and comparison with the initial route. Every other criterion must match evidence actually requested by its prompt. The existing ten time estimates still sum to 70 minutes, but timing and mark difficulty require independent learner/teacher calibration. The complete written paper remains three independent Terminale NSI exercises, 210 estimated minutes, exactly 18 technical points plus a distinct two-point indicative French-language component. The practical component remains unsupported.

## Version, source and release gates

V20 has its own contract digest, finite prose catalogue digest, prompt version, model-selection schema, checkpoint identity, package replay and explicit pipeline/provider/runtime/PDF/benchmark dispatch. Unknown or mixed V20/V19 evidence fails closed; old package replay retains its old source and content identities. French retrieval remains strictly scoped to cleared French sources with no UK fallback, official-source provenance and holdout isolation. No uncleared reference is bundled; local privacy and non-official PDF labels remain unchanged.

Tests must recompute the graph and after-failure route across seeds, verify every exact-decimal credit profile, reject altered facts/selection IDs/printed sources, and replay representative V13–V19 and UK packages. Render normal and large-print fixtures, visually inspect every generated page against the official 2026 comparator using the PDF skill, obtain read-only review, and merge only after protected Backend/macOS checks. Then run one pinned French live diagnostic with retained attempts and hashes; do not start the final UK/French model matrix while shared source is changing or while manual fidelity is on hold. Human NSI teacher review, supervised learner timing/mark calibration, document rights and accessibility evaluation are separate external gates.
