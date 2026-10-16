# French NSI V26 incident-timeline live diagnostic — 16 October 2026

**One pinned training paper passed automated checks on its first attempt; manual paper fidelity remains on hold.** This is an engineering diagnostic, not model selection, teacher review, learner calibration, rights clearance or accessibility approval. Protected source PR #72 merged at `eafa735618f1ef0ec7566500a0baa77a5e861a9d` after Backend and macOS checks passed; primary `main` was fast-forwarded clean before this run.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Implementation SHA-256 | `ce23b1b58d105830e3f7fb383242412fda6f22e0304cd7d58d0968c13dc51e15` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 384.42 seconds; backend peak RSS 129,957,888 bytes, excluding Ollama |
| Subject | Thirteen A4 pages, SHA-256 `80948b458314acc709549182aa13514b3e87210420b317f5ce77aa3b15e2489e` |
| Proposed correction | Twenty A4 pages, SHA-256 `60984069cbacede20294ccdca90fa33163ebd3a88820f800428658c40e9868ea` |
| Assessment and manifest | SHA-256 `c67438768d4ca01a93debfe134c9b934ad3e141b5685a075c7288667ae50a88a`; `b320201214d07e551b81fdea2bf03a5c715fdafe92028c97ba79a96f508af746` |
| Preserved local evidence | `tmp/pdfs/french-v26-incident-timeline-20261016/runs/gemma4-12b/4eb23ef187e2/270100/result.json`, `attempt-001/`, checkpoints, artifacts and all page renders under `tmp/pdfs/french-v26-incident-timeline-20261016/` |

The comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained locally at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf`, SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All thirteen generated subject pages and twenty proposed-correction pages were rendered and inspected visually, alongside all sixteen official comparator pages. The official correction was not compared. Page and question counts are diagnostic indicators of depth and response flow, not a rigid 2027 template or a reason to pad pages.

| Measure | Official 2026 subject | V26 training subject |
|---|---:|---:|
| A4 pages | 16 | 13 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 12 + 12 = 34 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–6, 7–10, 11–13 |

V26 adds an original recovery timeline to E3. After the changed route delays the packet, the candidate must calculate the release of resource B, finish of processing, restart of P2 and delivery of the encrypted report, then distinguish the packet's missed deadline from the report's separate met deadline. The app owns the timing facts and validates the finite wording, package replay and printed tables. This is a causal-reasoning improvement over V25, not evidence of official-paper equivalence. The chronology still fits on the same three E3 pages, and the subject retains substantial unused space elsewhere.

| Subject page | Visual finding |
|---:|---|
| 1 | Non-official written-only cover; exact 18 technical plus distinct two indicative language points stated. |
| 2 | E1 context, weighted graph and 1a–1b legible. |
| 3 | Initial Dijkstra table, code and 1c–1e associated. |
| 4 | First-closure Dijkstra table and 1f associated; much lower space unused. |
| 5 | Second-closure route/cost/comparison surface and 1g associated; most of the page unused. |
| 6 | Tree table, code and 1h–1j legible. |
| 7 | E2 premise, faulty join and source tables legible, but lower half sparse. |
| 8 | Incident data, comparison table and 2a–2d associated. |
| 9 | Aggregate/state tables, code and 2e–2h associated; dense but legible. |
| 10 | 2i–2l end the state comparison; much lower space unused. |
| 11 | E3 timed incident context, links and route table legible. |
| 12 | Chronology table, 3a–3f and process working table associated. |
| 13 | 3g–3l, message/security tables legible; lower area unused. |

| Proposed-correction page | Visual finding |
|---:|---|
| 1–2 | Non-official correction cover and separate indicative language rubric. |
| 3–8 | E1 graph, outage tables, answers and item credits associated; page 8 is sparse. |
| 9–15 | E2 reconciliation, aggregate query, code, updates and state traces associated with credits; pages 12 and 15 are sparse. |
| 16–20 | E3 timed route/recovery/security answers and credits associated; 3g correctly reports t=20, 22, 26 and 28, and 3l distinguishes deadlines t=19 and t=29. |

At inspected scale there is no visible clipping, obscured label or orphaned question/table/credit. One marking-quality gap remains: question 3l asks for two deadline comparisons *and* both metadata and compromised-terminal limitations, but its 0.5-point indicative rubric names only the deadlines and metadata. A future version should align the prompt, answer and credits without mutating V26 replay. This correction is not independently pedagogically validated and was not compared against an official marking scheme.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Do not select a French model or run the final UK/French matrix while shared French source is changing. Next prioritize the 3l rubric mismatch, original app-owned E2/E3 depth and candidate response-flow improvements without blank-page padding; preserve V25–V15 live holds and V12–V14 failed evidence. Two independent NSI teachers must judge correctness and mark granularity; a supervised learner trial must measure timing and ambiguity. Per-document rights and accessibility remain external gates. The practical component is unsupported; issues #4 and #8 stay open.
