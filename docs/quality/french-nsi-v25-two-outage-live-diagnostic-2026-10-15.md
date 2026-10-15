# French NSI V25 two-outage live diagnostic — 15 October 2026

**One pinned training paper passed automated checks on its first attempt; manual paper fidelity remains on hold.** This is an engineering diagnostic, not model selection, teacher review, learner calibration, rights clearance or accessibility approval. Protected source PR #69 merged at `62671faac948594b4f05cc2a3c7768feb6713efe` after Backend and macOS checks passed; primary `main` was fast-forwarded clean before this run.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Implementation SHA-256 | `007dfc6ee900c33d15ec56070d027b13a009d9ab43d0f4b62b86194aefdf1c3a` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 229.272 seconds; backend peak RSS 139,804,672 bytes, excluding Ollama |
| Subject | Thirteen A4 pages, SHA-256 `9fadd4feeec41f665b0c03ad85cf2f9bafbb3ee86addb2d83c4cb59458f115db` |
| Proposed correction | Twenty A4 pages, SHA-256 `f5457397071dd959325f8494fa26c50424e5cb554cf1c574ff65f39fe01c3c15` |
| Assessment and manifest | SHA-256 `c0f9e90d9b8b7366673bb8cbd827dd9b497f80087813f7974f1d896821d80c16`; `dd688437a6030d0e03156a723f0460e0e1ae23eaede32ffd0de572a320be09e1` |
| Preserved local evidence | `tmp/pdfs/french-v25-two-outage-20261015/runs/gemma4-12b/4eb23ef187e2/270100/result.json`, `attempt-001/`, checkpoints, artifacts and all page renders under `tmp/pdfs/french-v25-two-outage-20261015/` |

The comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained locally at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf`, SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All thirteen generated subject pages and twenty proposed-correction pages were rendered and inspected visually, alongside all sixteen official comparator pages. The official correction was not compared. Page and question counts indicate depth and response flow; they are not a 2027 template requirement.

| Measure | Official 2026 subject | V25 training subject |
|---|---:|---:|
| A4 pages | 16 | 13 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 12 + 12 = 34 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–6, 7–10, 11–13 |

V25 adds an original, causally linked second network outage to E1. The candidate must retain the first closure, trace the new state, derive a surviving minimum route, sum its weights and compare the result with the first-outage route. An immutable contract independently checks the graph and answer; the subject keeps each new working table with its question and rejects leaked route or cost text. This is a genuine reasoning improvement over V24, while E2 and E3 retain their previous content. It is not evidence of official-paper equivalence: the added E1 page is largely unused, and E2/E3 remain short compared with the comparator's sustained multi-step progression. No blank-page padding is justified.

| Subject page | Visual finding |
|---:|---|
| 1 | Non-official written-only cover; exact 18 technical plus distinct two indicative language points stated. |
| 2 | E1 context, weighted graph and 1a–1b legible. |
| 3 | Initial Dijkstra table, code and 1c–1e associated. |
| 4 | First-closure Dijkstra table and 1f associated; much lower space unused. |
| 5 | Second-closure route/cost/comparison surface and 1g on the same page; most of the page unused. |
| 6 | Tree table, code and 1h–1j legible. |
| 7 | E2 premise, faulty join and source tables legible. |
| 8 | Incident data, comparison table and 2a–2d associated. |
| 9 | Aggregate/state tables, code and 2e–2h associated; dense but legible. |
| 10 | 2i–2l finish the state comparison; much lower space unused. |
| 11 | E3 incident context, costs, route and deadline surfaces legible. |
| 12 | E3 3a–3h and recovery/security cards associated. |
| 13 | Security-analysis table and 3i–3l legible; most lower space unused. |

| Proposed-correction page | Visual finding |
|---:|---|
| 1–2 | Non-official correction cover and separate indicative language rubric. |
| 3–8 | E1 graph, staged outage tables, answers and item-level indicative credits associated; second-outage answer and rubric are present. |
| 9–15 | E2 context, reconciliation, aggregate query, code, targeted updates and state traces associated with indicative credits. |
| 16–20 | E3 route, recovery and security answers with item-level credits; final page is sparse. |

At inspected scale there is no visible clipping, obscured label or orphaned question/table/credit. The proposed correction was checked for association and legibility, not official marking-scheme equivalence or independent pedagogical correctness.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Do not select a French model or run the final UK/French matrix while shared French source is changing. Continue original app-owned E2/E3 depth and candidate response-flow improvements without padding; preserve V24–V15 live holds and V12–V14 failed evidence. Two independent NSI teachers must judge correctness and mark granularity; a supervised learner trial must measure timing and ambiguity. Per-document rights and accessibility remain external gates. The practical component is unsupported; issues #4 and #8 stay open.
