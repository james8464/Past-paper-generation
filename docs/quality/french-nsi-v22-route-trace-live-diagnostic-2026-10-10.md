# French NSI V22 route-trace live diagnostic — 10 October 2026

**One pinned written training paper passed automated checks on its first attempt; manual product fidelity remains on hold.** This is a single-paper engineering diagnostic, not model selection, teacher review, learner calibration or accessibility approval. Protected PR #59 introduced the version-isolated before/after route-trace exercise and merged after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #59, `b94f97da2fc7edcff5325d9d62b496ffa92a75c8`; implementation SHA-256 `a87b71948224a6ad9581a2e455d9596b8ee1d8bbe69781ac3cd283a9b193eb67` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 128.849 seconds; backend peak RSS 135,118,848 bytes, excluding Ollama |
| Subject | Eleven A4 pages, SHA-256 `bfc7112f86c782a8d0852b4b1bb0cd288e4a90d562824e052a8c64755b7d5803` |
| Proposed correction | Eighteen A4 pages, SHA-256 `15a3e84dccb808a5b3cecfc5282b5f463041c81ed6284c0946b3682bbfee1c50` |
| Package and manifest | SHA-256 `2f153f8fab36823783853e068de1b789b26c99e25f69473e821d69dd02707a56`; `4e0eb94d24673a764eb4eec810fa80c3bd8b051d43ce3179c6c7beee12359114` |
| Preserved local evidence | `tmp/pdfs/french-v22-route-trace-20261010/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v22-route-trace-20261010/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-56e19e759338/` |

The comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All eleven subject pages, eighteen correction pages and sixteen official pages were rendered and visually inspected. The official correction was not compared. Page counts are evidence of depth and space, not a mandated 2027 template.

| Measure | Official 2026 subject | V22 training subject |
|---|---:|---:|
| A4 pages | 16 | 11 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–5, 6–8, 9–11 |

V22's writable before/after Dijkstra tables make E1 materially more usable. The official exercises still develop linked figures, code, datasets and changing situations over longer sequences. The generated E2 and E3 are shorter, and working space is unevenly distributed.

| Subject page | Visual finding |
|---:|---|
| 1 | Non-official cover states written-only scope and the separate 18 technical plus 2 indicative French-language points. |
| 2 | E1 graph, labels and 1a–1b are legible. |
| 3 | Baseline Dijkstra per-node table, 1c–1f and code are legible; the table adds useful working space. |
| 4 | Post-closure Dijkstra table and 1g are associated, but the lower half is largely unused. |
| 5 | E1 tree, 1h–1j and code are legible without clipping. |
| 6 | E2 context and schemas are legible. |
| 7 | E2 incident dataset and 2a–2f are associated. |
| 8 | E2 working tables and 2g–2j are legible; E2 occupies three pages versus five official pages. |
| 9 | E3 network and 3a–3c are legible. |
| 10 | E3 3d–3i and process/security tables are associated. |
| 11 | Only 3j–3l occupy the top of a mostly blank final page. |

The proposed correction was checked for legibility, attribution and flow, not official marking-scheme equivalence.

| Correction page | Visual finding |
|---:|---|
| 1 | Separate teacher-facing “Corrigé proposé et barème indicatif” cover. |
| 2 | General guidance and distinct two-point indicative French-language rubric. |
| 3 | E1 context, graph and code are reproduced legibly. |
| 4 | E1 opening answers and credit are associated. |
| 5 | E1 route-table answers and credit are associated. |
| 6 | E1 later route-table answers and credit are associated. |
| 7 | E1 tree and final answer/credit are legible. |
| 8 | E2 context and schema are legible. |
| 9 | E2 data and opening answers/credit are legible. |
| 10 | E2 intermediate answers and credit are associated. |
| 11 | E2 staged state/function answer and credit are associated. |
| 12 | E2 later state/function answer and credit are associated. |
| 13 | E2 final answers and credit are legible. |
| 14 | E3 context and opening answer/credit are legible. |
| 15 | E3 route and process answers/credit are associated. |
| 16 | E3 intermediate process/security answers and credit are associated. |
| 17 | E3 later answers and credit are legible. |
| 18 | The final 3l answer/credit occupy a sparse page. |

No clipping, obscured labels or visibly orphaned answer/credit was seen at the inspected scale. Automated scoring, source isolation and deterministic checks do not establish exam equivalence. The correction's eighteen pages reflect answer/rubric pagination, not equivalent candidate task depth.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** V22 improves E1's before/after route working surface, but the subject remains less sustained than the official comparator, with compact E2 and sparse E3. Do not pad pages to match the official count. Preserve V21–V15 live holds and V12–V14 failed attempts. No French model is selected; the final UK/French matrix remains premature while shared French source changes. Independent NSI teachers must judge correctness and mark granularity, a supervised learner trial must measure timing and ambiguity, and rights and accessibility reviews remain external gates. The practical component is unsupported; issues #4 and #8 remain open.
