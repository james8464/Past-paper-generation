# French NSI V20 graph resilience live diagnostic — 10 October 2026

**One pinned written training paper passed automated checks on its first attempt. Manual product fidelity remains on hold.** This is an engineering diagnostic, not a teacher review, learner trial or model-selection result. Protected PR #55 introduced the version-isolated graph-link-outage sequence and merged after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #55, `7cfa500179e1ca658aef23fc55ea4c0c9fb82461`; implementation SHA-256 `93af88d00e400606e0432510d2999ae3c29f9d921e58b254f569d419e48e3eb5` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 128.567 seconds; backend peak RSS 135,446,528 bytes, excluding Ollama |
| Subject | Eight A4 pages, SHA-256 `9c8acc3f2a3cfa35c5504332777bd37d46c98177b7c835c6f64e156d808a3a93` |
| Proposed correction | Seventeen A4 pages, SHA-256 `adda833f316f91abaa5f575acc2f0268c0cfd76e894127b70ed518fb87111349` |
| Package and manifest | SHA-256 `1598e534bd86243a75fab95bb131706972d5d5227f64925c427c04acba8e0358`; `90c7f256c60dd0e6450e5871fce8b68650dbc9e987ba1c20c7c5f37547ce10bc` |
| Preserved local evidence | `tmp/pdfs/french-v20-graph-resilience-20261010/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v20-graph-resilience-20261010/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-9909afb1747f/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of both generated PDFs and all sixteen official pages was rendered and visually inspected with the PDF workflow. Page and question counts are signals of depth and space, not a prescribed 2027 template. There was no official correction comparator in this check.

| Measure | Official 2026 subject | V20 training subject |
|---|---:|---:|
| A4 pages | 16 | 8 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–3, 4–5, 6–8 |

All sixteen official pages were inspected: cover page 1, the linked IP/routing/security exercise on pages 2–5, the binary/game graph exercise on pages 6–10, and the tree/SQL exercise on pages 11–16. The official exercise spans develop linked figures, code and changing data over successive pages. The generated subject log below compares the corresponding exercise span rather than demanding the same page count or task order.

| Subject page | Visual finding and comparison |
|---:|---|
| 1 | Independently branded cover clearly says “Sujet d’entraînement — non officiel”; three-hour-thirty-minute written scope is stated. |
| 2 | E1 graph-link-outage context, faulty BFS code and labelled graph are legible; no crossed or hidden edge labels were seen. The official E1 develops its linked material across four pages. |
| 3 | All ten E1 questions, the working table and search code share a dense page. The new outage arithmetic is visible, but candidate working space and sustained task depth remain limited. |
| 4 | E2 context, faulty SQL/Python and agent/category tables are legible. Official E2 spans five pages with more staged material. |
| 5 | Six incident rows and all ten E2 questions fit on one page. The data and phases are associated, but there is little room for working. |
| 6 | E3 network context, link and Dijkstra tables, and 3a–3c are legible; official E3 develops across six pages. |
| 7 | Questions 3d–3i and their working tables stay associated without visible clipping. |
| 8 | Only 3j–3l appear in the upper part; most of the final page is unused despite limited working space earlier. |

The correction was checked for legibility, attribution and page flow, not against an official marking scheme.

| Correction page | Visual finding |
|---:|---|
| 1 | Teacher-facing “Corrigé proposé et barème indicatif” cover is distinct from candidate instructions. |
| 2 | General marking guidance and the separate indicative two-point French-language scale are legible. |
| 3 | E1 context, graph and code reproduce the candidate materials without visible clipping. |
| 4 | E1 1a–1d answers and credit rows are attributed and legible. |
| 5 | E1 1e–1g answers and credit rows remain associated. |
| 6 | E1 1h–1i answers and credit rows are readable. |
| 7 | Only E1 1j occupies the page; its answer and credit remain together. |
| 8 | E2 context, faulty SQL/Python and category tables are legible. |
| 9 | Incident data and 2a–2c answers with credits are legible. |
| 10 | E2 2d–2e answers and credits are present, with unused space. |
| 11 | E2 2f–2h code, state and credit rows are readable. |
| 12 | Only 2i–2j occupy the page; credits are attributed, but much of the page is empty. |
| 13 | E3 context and 3a answer/credit are legible. |
| 14 | E3 3b–3e answers and credits, with process working material, are legible. |
| 15 | E3 3f–3h answers and credits remain attributed. |
| 16 | E3 3i–3k answers and credits remain attributed. |
| 17 | Only 3l and its credit table appear near the top of a mostly blank page. |

No clipping, obscured graph labels or candidate-facing answer leakage was seen at the inspected scale. The package records 6, 6.5 and 5.5 technical points across E1–E3, exactly 18, plus a distinct two-point indicative French-language component. Automated source isolation, scoring and deterministic checks passed; they do not establish exam equivalence. V20's graph outage makes E1 more substantive, but ten questions are now crowded onto one page. E2 remains compact; E3 ends sparsely. The proposed correction's 17 pages mostly reflect answer/credit pagination, not a 17-page candidate reasoning sequence. The subject has fewer questions and far less sustained multi-step development than the official comparator. Do not pad pages solely to approach a reference count; improve original task depth and usable working space together.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Preserve this result alongside V19–V15 live holds and V12–V14 failed attempts. No French model is selected; a final UK/French matrix is premature while shared French source changes. Independent NSI teachers must judge correctness, marks and the indicative quarter-point granularity; a supervised learner trial must measure timing and ambiguity. Document rights and accessibility checks remain external gates. The practical component is unsupported, and issues #4 and #8 remain open.
