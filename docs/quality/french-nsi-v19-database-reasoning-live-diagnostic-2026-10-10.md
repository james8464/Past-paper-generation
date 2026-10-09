# French NSI V19 database reasoning live diagnostic 10 October 2026

**One pinned training paper passed automated checks on its first attempt, but manual comparison keeps product fidelity on hold.** This is a written-component engineering diagnostic, not a teacher review, learner trial or model-selection result. Protected PR #52 introduced the version-isolated ten-question database reasoning sequence and merged after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #52, `9bc81dcea764a05c67b381a76f3df1aaf504fc69`; implementation SHA-256 `eda663af993dc740c93a831737e03a1fd1b279907fc9f2bb6b59bb0422538dc2` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 618.786 seconds; backend peak RSS 135,200,768 bytes, excluding Ollama |
| Subject | Nine A4 pages, SHA-256 `e178c8c092db9c1ec09c52848ee05c9b1b6e2ec76faaec06de91aa2b8cb9be83` |
| Proposed correction | Sixteen A4 pages, SHA-256 `5fd50cd975330e201d67aca9982396c21ee54ef4bf6d1621091983a5917c9cf3` |
| Package and manifest | SHA-256 `647aec4e4aed4d88def663fe4de4cdca84f309acd4c14b3aad4fa444f5c41a6c`; `7008659d4defb5ebe0d485f8982a56f5bf1dee4f0a2164ffc89421ed4677fe3b` |
| Preserved local evidence | `tmp/pdfs/french-v19-database-reasoning-20261010/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v19-database-reasoning-20261010/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-0f726d821df9/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of the generated subject and proposed correction and all sixteen official reference pages was rendered and visually inspected. Page and question counts are comparison signals, not a prescribed 2027 template.

| Measure | Official 2026 paper | V19 training subject |
|---|---:|---:|
| A4 pages | 16 | 9 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans in subject | Pages 2–5, 6–10, 11–16 | Pages 2–4, 5–6, 7–9 |

The database exercise now sequences integrity and joins, query construction, then state changes and Python debugging. Its printed tables and six incident rows support deterministic results. All ten prompts still occupy one subject page, however, leaving little room for working. The live subject does not visibly print locked answers. The proposed correction carries the expected answers and their indicative credits, with no obvious clipping or obscured table content at the inspected scale. Both PDFs carry the non-official or proposed-correction labels. The package records 6, 6.5 and 5.5 technical points across the exercises, plus a distinct two-point indicative French-language component. These are engineering and visual observations, not examiner or teacher validation.

The fidelity gap remains material. The official paper sustains linked contexts, figures, code and changing data across more pages. The generated Exercise 1 ends with four compact questions on a mostly empty page; Exercise 3 similarly ends with three short prompts, and the proposed correction has sparse final pages for Exercise 2 and 3. The questions remain less demanding in sustained multi-step reasoning than the official comparator. The French scope lines also contain unidiomatic missing articles, for example “sur étude d'un registre d'incidents” and “sur liaisons d'une station”; native-language review remains necessary. No page-count padding should substitute for deeper original tasks, appropriate working space and copy editing. The indicative quarter-point criteria and the 3 h 30 duration still need independent NSI teacher judgement and a supervised learner timing/marking trial.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Preserve this checkpoint alongside the V18, V17, V16 and V15 live holds and the V12–V14 failed attempts. Further app-owned depth and page-flow work should be verified test-first, then assessed with another source-pinned live PDF and page-by-page official comparison before freezing shared source or launching the expensive UK/French matrix. Document-level rights and accessibility evaluation remain external gates. The practical component is unsupported; issues #4 and #8 remain open.
