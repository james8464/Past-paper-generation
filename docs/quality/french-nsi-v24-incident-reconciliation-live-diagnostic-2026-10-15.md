# French NSI V24 incident-reconciliation live diagnostic — 15 October 2026

**One pinned training paper passed automated checks on its first attempt; manual paper fidelity remains on hold.** This is an engineering diagnostic, not model selection, teacher review, learner calibration, rights clearance or accessibility approval. Protected source PR #66 was merged at `a068c8fb1f2c49307c08fe8c2939317351a3441a` after Backend and macOS checks passed; primary `main` was fast-forwarded clean before the run.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Implementation SHA-256 | `beb975fc155aac55387ebd9d352b855a880a32a7c5ff4214e23f71cee40fb23f` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 236.88 seconds; backend peak RSS 136,265,728 bytes, excluding Ollama |
| Subject | Twelve A4 pages, SHA-256 `1db0f94112cbeb07eb84fdf156d7f70af475205f3b66790802bcccda2be2ed08` |
| Proposed correction | Nineteen A4 pages, SHA-256 `268f1091ff00c8a3f83532fb464075e92f114310e1b9dc55051b704a52513071` |
| Assessment and manifest | SHA-256 `015f26776d92a4b6558e4fb800a2a8aef994c9d55e04b7365c0896c9eacd68bf`; `8966a6ac53c85cb81c74a35a01a4b1f5fe46b8b0568406c8d5ef29ad7081c07d` |
| Preserved local evidence | `tmp/pdfs/french-v24-incident-reconciliation-20261015/runs/gemma4-12b/4eb23ef187e2/270100/result.json`, `attempt-001/`, checkpoints, artifacts and page renders under `tmp/pdfs/french-v24-incident-reconciliation-20261015/` |

The comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained locally at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf`, SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All twelve generated subject pages and nineteen proposed-correction pages were rendered and inspected visually. The sixteen official pages were inspected page by page in the V23 baseline review and were used here as the same frozen comparator. The official correction was not compared. Page counts illustrate depth and working space; they are not a 2027 template requirement.

| Measure | Official 2026 subject | V24 training subject |
|---|---:|---:|
| A4 pages | 16 | 12 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 12 + 12 = 34 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–5, 6–9, 10–12 |

V24's E2 is a genuine improvement over V23: it links a faulty join to data-integrity diagnosis, a corrected join and aggregate query, then a category-versus-agent code error across two copied database states and exact row-targeted updates. The candidate receives separate comparison, count and state-trace surfaces. This makes E2 four pages instead of three, but it does not establish official-paper equivalence. E1 page 4 is still mostly unused and its route/tree reasoning is shorter than the official comparator. E2 page 9 and E3 page 12 are sparse. The official paper sustains longer multi-step reasoning and response flow across its exercises. No blank-page padding is justified.

| Subject page | Visual finding |
|---:|---|
| 1 | Non-official written-only cover; 18 technical points and distinct two indicative French-language points stated. |
| 2 | E1 graph and first two questions legible. |
| 3 | Initial Dijkstra table, code and 1c–1f associated. |
| 4 | After-closure table and 1g associated; most lower area unused. |
| 5 | Tree data, code and 1h–1j legible. |
| 6 | E2 premise, faulty join and source tables legible. |
| 7 | Incident data, reconciliation table and 2a–2d associated. |
| 8 | Aggregate/state tables, code and 2e–2h associated; dense but legible. |
| 9 | 2i–2l complete the state comparison; most lower area unused. |
| 10 | E3 incident context, costs, route and deadline surfaces legible. |
| 11 | E3 3a–3h, recovery and security cards associated; dense but legible. |
| 12 | Security-analysis table and 3i–3l legible; most lower area unused. |

| Proposed-correction page | Visual finding |
|---:|---|
| 1–2 | Non-official correction cover and distinct indicative language rubric. |
| 3–7 | E1 graph, route and tree answers with item-level indicative credits; 1g and 1h transition is clear. |
| 8–10 | E2 context, integrity diagnosis and join comparison with item-level credits. |
| 11 | Corrected join and aggregate working surface; page is sparse. |
| 12–14 | Aggregate query, code, targeted updates and S0/S1/S2 traces associated with credits. |
| 15–19 | E3 route, recovery and security answers with item-level credits; last page is sparse. |

At inspected scale there is no visible clipping, obscured label or orphaned answer/credit. The proposed correction was checked for association and legibility, not official marking-scheme equivalence or independent pedagogical correctness.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Do not select a French model or run the final UK/French matrix while shared French source is changing. Continue original app-owned E1/E2 depth and candidate working-space improvements without padding, and preserve V23–V15 live holds and V12–V14 failed evidence. Two independent NSI teachers must judge correctness and mark granularity; a supervised learner trial must measure timing and ambiguity. Per-document rights and accessibility remain external gates. The practical component is unsupported; issues #4 and #8 stay open.
