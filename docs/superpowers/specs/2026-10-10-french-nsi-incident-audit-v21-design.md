# French NSI incident audit V21 — versioned design

Status: implementation design within the approved French written-paper scope, 10 October 2026. This is not teacher, examiner, learner or accessibility approval.

## Purpose and boundary

The pinned V20 subject passed automated checks but remains a manual fidelity hold: all ten database questions occupy one dense page, with little sustained use of the displayed data. The official 2026 Métropole paper sustains linked contexts, code and changing states across its exercises; its 16 pages are a comparator, not a 2027 target. This increment deepens one original, app-owned database exercise through traceable relational and algorithmic states. It does not add blank pages to imitate the reference.

V21 changes Exercise 2 only. V20 graph resilience, V18 network reasoning, UK routes, and V13–V20 saved packages keep their original identities and replay unchanged. The written paper remains three independent Terminale NSI exercises, 210 estimated minutes, exactly 18 technical points plus a distinct two-point indicative French-language component. The practical component is unsupported.

## Immutable case and candidate evidence

A new V3 incident-audit contract uses four agents, four categories and eight incidents. Names and category labels may vary with the seed, but the keys, references and statuses are fixed. The incident rows are:

| Incident | Agent | Category | Initial status |
|---:|---:|---:|---|
| 101 | 1 | 2 | ouvert |
| 102 | 1 | 3 | clos |
| 103 | 2 | 1 | clos |
| 104 | 3 | 2 | ouvert |
| 105 | 2 | 2 | ouvert |
| 106 | 3 | 1 | ouvert |
| 107 | 4 | 4 | clos |
| 108 | 4 | 3 | ouvert |

The initial category counts are 2, 3, 2 and 1; a separately labelled hypothetical fifth category has zero incidents. An attempted incident 109 with nonexistent agent 999 is rejected by the foreign key; a valid-agent alternative is a reasoning task, not an initial row. The existing faulty join equates `incident.id_agent` with `categorie.id_cat`; the correct join equates category keys. A faulty fixed Python counter counts `ouvert` instead of `clos`. Two distinct targeted SQL updates close incident 101 and then incident 105, defining states S0, S1 and S2. SQLite recomputes and locks the closed counts 3, 4 and 5. The faulty Python returns 5, 4 and 3; the corrected condition returns 3, 4 and 5. No model-authored SQL or Python is executed.

Candidate materials are staged by dependency rather than placed in a single preamble. The three initial tables and faulty join appear before Part A. A four-row join-comparison table with blank outcome cells appears at 2c; it does not disclose the category labels. The grouped-count and two-update tasks form Part B/C. A blank S0/S1/S2 state table appears at 2g, followed by the supplied faulty Python and blank trace table at 2h. Every material appears before its first dependent prompt and never in the answer-only portion of the candidate PDF. The proposed correction carries exact derived values and credits.

## Ten linked tasks and exact scoring

| Phase | Questions | Requested evidence |
|---|---|---|
| A — relations and joins | 2a–2d | Name primary/foreign keys and their guarantee; reject the proposed invalid insert and choose a valid reference; trace the true categories of 101, 102, 107 and 108; compare four faulty-join labels with the correct labels and isolate the wrong condition. |
| B — queries | 2e–2f | Write the corrected ordered join and justify eight result rows; construct a left-join grouped count, derive 2/3/2/1 from the printed data, and explain the hypothetical empty fifth category's zero. |
| C — state and debugging | 2g–2j | Write two targeted updates and derive closed totals S0→S1→S2; trace the faulty fixed function's 5/4/3 returns and a failing assertion; repair the condition and trace 3/4/5; check the empty-list result and why no first-element access occurs. |

Each question asks for the evidence it is credited for; a rubric may not demand an unstated extra explanation. The 70-minute E2 time estimates remain `(6, 6, 7, 7, 8, 8, 7, 7, 7, 7)`. Exact-decimal technical profiles are:

| E2 total | 2a | 2b | 2c | 2d | 2e | 2f | 2g | 2h | 2i | 2j |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5.5 | .25 | .5 | .5 | .5 | .75 | 1 | .5 | .5 | .75 | .25 |
| 6 | .25 | .5 | .75 | .5 | .75 | 1 | .75 | .5 | .75 | .25 |
| 6.5 | .25 | .5 | .75 | .75 | .75 | 1 | .75 | .75 | .75 | .25 |

Quarter-point criteria split multi-part tasks; the criteria must be auditable against the printed state and timed by learners before educational acceptance. The seed's existing paper-level allocation chooses one of these three profiles and preserves the 18-point technical total.

## Version and publication gates

V21 has a separate immutable V3 contract digest, finite native-French prose catalogue digest, selection schema and prompt identity. The model selects only registered scene/question/rubric IDs; it cannot supply rows, source code, answers, marks or free-form instructions. Checkpoints, packages, provider/pipeline/runtime/PDF/benchmark dispatch and source hashes are explicit. A missing or mixed V21/V20 identity fails closed. V13–V20 and UK package/state replay remain unchanged.

Normal and large-print PDF tests must reject missing or interchanged initial rows, join/state/trace tables, faulty source snippets, question IDs, phase labels, answers or credit. They must verify material-to-question association, subject answer exclusion, readable bounds and correction answer/credit grouping. French reference retrieval remains strictly scoped to eligible French sources, with provenance and holdout isolation and no UK fallback. Local privacy and the non-official subject/proposed-correction labels remain unchanged.

Fixture PDFs are not live evidence. After test-first implementation and read-only review, merge only through protected Backend/macOS checks, run one source/model/reference-pinned French live diagnostic, retain every attempt and artifact hash, and inspect every generated page against all official 2026 pages with the PDF skill. A manual hold remains possible even after an automated pass. Do not launch the final UK/French matrix while shared source changes or manual fidelity holds. Independent NSI teachers, supervised learners, document-rights review and accessibility evaluation remain external gates.
