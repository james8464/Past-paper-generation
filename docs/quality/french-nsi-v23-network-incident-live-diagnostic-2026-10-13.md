# French NSI V23 network-incident live diagnostic — 13 October 2026

**One pinned written training paper passed automated checks on its first attempt; manual product fidelity remains on hold.** This is a single-paper engineering diagnostic, not model selection, teacher review, learner calibration, rights clearance or accessibility approval. Protected PR #63 introduced the version-isolated, causally linked routing/process/security E3 case study after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #63, `be7243589326c69ff3a0a5a4751efddee58f4491`; implementation SHA-256 `5489122ae42b8ed4a7da2fd13252ec6385f80d9e73b65e5b70b47f1682b57a54` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 136.186 seconds; backend peak RSS 158,908,416 bytes, excluding Ollama |
| Subject | Eleven A4 pages, SHA-256 `57e430ec9ed035baef504b7459208320453d7e7867ff29de1e47e2fc39272c7f` |
| Proposed correction | Eighteen A4 pages, SHA-256 `dadc66750aea081d45b04eca8f25bad51bbedbfc958636db9600b44063cae15e` |
| Package and manifest | SHA-256 `3356a35b1e8ab742a537c7f3e7817c2e50f3196e23666b97bb1b603a3ece4849`; `e66ef1ea012bcf2f55ecb53e8d14356136bdf80e6d2bd5dcf718dc376c48641a` |
| Preserved local evidence | `tmp/pdfs/french-v23-network-incident-20261013/runs/gemma4-12b/4eb23ef187e2/270100/result.json`, `attempt-001/`, checkpoints and artifacts under `tmp/pdfs/french-v23-network-incident-20261013/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-da42635c628e/` |

The comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained locally at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. All eleven generated subject pages, eighteen proposed-correction pages and sixteen official pages were rendered and visually inspected. The official correction was not compared. Page counts evidence depth and working space; they are not a prescribed 2027 template.

| Measure | Official 2026 subject | V23 training subject |
|---|---:|---:|
| A4 pages | 16 | 11 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–5, 6–8, 9–11 |

V23's E3 is a more coherent incident: a delayed M-27 packet follows a changed shortest route, then a resource deadlock and recovery, then encrypted reporting with separate confidentiality/authentication/metadata limits. Its before/after route table and recovery table are usable working surfaces. The official paper still sustains longer code, data and state reasoning, particularly over five E2 and six E3 pages. The generated E1 page 4 and final E3 page are sparse; E2 remains three pages. This is not cured by adding blank pages.

| Subject page | Visual finding |
|---:|---|
| 1 | Non-official written-only cover; 18 technical points and separate two indicative French-language points are stated. |
| 2 | E1 graph, scenario and 1a–1b legible. |
| 3 | E1 initial Dijkstra table, 1c–1f and code legible with working cells. |
| 4 | E1 after-closure table and 1g associated; lower page mostly unused. |
| 5 | E1 tree, 1h–1j and code legible. |
| 6 | E2 context, faulty join, agents and categories legible. |
| 7 | E2 eight incidents, join working table and 2a–2f associated. |
| 8 | E2 state/trace working tables, 2g–2j and code legible. |
| 9 | E3 scenario, link costs, before/after route table and packet deadline legible; no E3 question yet. |
| 10 | E3 3a–3h, recovery table and security cards associated; page is dense but legible. |
| 11 | E3 security-analysis table and 3i–3l legible; most of the lower page is unused. |

The proposed correction was checked for attribution, legibility and answer/credit association, not official marking-scheme equivalence.

| Correction page | Visual finding |
|---:|---|
| 1 | Non-official proposed-correction cover. |
| 2 | General marking guidance and separate indicative two-point French-language rubric. |
| 3 | E1 graph and 1a–1b answers/credits associated. |
| 4 | E1 initial route table and 1c–1d answers/credits associated. |
| 5 | E1 code and 1e–1f answers/credits associated. |
| 6 | E1 after-closure table, 1g answer/credit and tree legible. |
| 7 | E1 1h–1j answers/credits and code legible. |
| 8 | E2 context, join and source tables legible. |
| 9 | E2 incident table, 2a–2b answers/credits and join working table legible. |
| 10 | E2 2c–2e answers/credits associated. |
| 11 | E2 2f answer/credit and state table associated. |
| 12 | E2 2g answer/credit and function working table associated. |
| 13 | E2 2h–2j answers/credits associated. |
| 14 | E3 scenario, links and route/deadline tables legible. |
| 15 | E3 3a–3d answers/credits associated; after-change route, arrival and delay explicit. |
| 16 | E3 recovery table and 3e–3g answers/credits associated. |
| 17 | E3 3h–3i answers/credits with security tables associated. |
| 18 | E3 3j–3l answers/credits associated; last page sparse. |

All sixteen official pages were separately inspected: cover (1); E1 network figure and addressing (2–3), routing and security sequence (4–5); E2 board/transition figures (6), binary/XOR and code (7–8), graph/recursive follow-through (9–10); E3 argument-tree figure and model (11–12), recursive evaluation/code (13), relational schema (14), tables and queries (15–16). The comparison supports a depth and working-space HOLD, not a demand to mimic the official exercise topics. No clipping, obscured labels or visibly orphaned answer/credit appeared at the inspected scale.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** No French model is selected and the final UK/French matrix remains premature while shared French source is changing. Preserve V22–V15 live holds and V12–V14 failed evidence. Two independent NSI teachers must judge correctness and mark granularity; a supervised learner trial must measure timing and ambiguity. Per-document rights and accessibility remain external gates. The practical component is unsupported; issues #4 and #8 stay open.
