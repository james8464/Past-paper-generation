# French NSI V18 network reasoning live diagnostic 9 October 2026

**One pinned training paper passed automated checks on its first attempt, but manual comparison keeps product fidelity on hold.** This is a written-component engineering diagnostic, not a teacher review, learner trial or model-selection result. Protected PR #50 introduced the version-isolated twelve-question network, process and security exercise and merged only after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #50, `09826554a54ef7500aff78565f00f3bd7991ea6f`; implementation SHA-256 `0c687ad86ddbef2114c1ce2630fcc8feb6f3d7d9c945fde4726bc820ae813676` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 139.696 seconds; backend peak RSS 135,004,160 bytes, excluding Ollama |
| Subject | Nine A4 pages, SHA-256 `d2672c670d8cd2320fffdc5d6ff95ef3d7b3ef841998123136540574bd4081fa` |
| Proposed correction | Fifteen A4 pages, SHA-256 `ac0c47ab0fb080e56bf0673d80776a620e4f2f54158fd326abb3d5539b898250` |
| Package and manifest | SHA-256 `f82151b0dff5ef7c3caf3cab7e7748d3c228bc6c5ee0cf5b772f3cbe7b0ddfa8`; `3b44b50a56a4ec097b7ef9da71e8a24a8deb83fb8a6ddaa6f38ebe243ad960f0` |
| Preserved local evidence | `tmp/pdfs/french-v18-network-reasoning-20261009/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v18-network-reasoning-20261009/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-b020fe1cdfa8/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of the generated subject and proposed correction and all sixteen official reference pages was rendered and visually inspected. Page and question counts are comparison signals, not a prescribed 2027 template.

| Measure | Official 2026 paper | V18 training subject |
|---|---:|---:|
| A4 pages | 16 | 9 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans in subject | Pages 2–5, 6–10, 11–16 | Pages 2–4, 5–6, 7–9 |

The new Exercise 3 has twelve connected questions and candidate working tables for pre- and post-change Dijkstra states, process recovery and security threats. Its materials appear near the questions that use them. The live subject does not print the expected answers. The proposed correction keeps inspected answers and their indicative credits together, including the route comparison in 3d. Both PDFs carry their non-official or proposed-correction labels; no obvious clipping or obscured table content was found at the inspected scale. The package records 6, 6.5 and 5.5 technical points across the three exercises, plus a distinct two-point indicative French-language component. These are automated and visual observations, not examiner or teacher validation.

The fidelity gap remains material. The official paper sustains linked contexts, figures, code and changing data across more pages. The generated Exercise 2 places all ten questions on one page; its final Exercise 1 and Exercise 3 pages each contain only a few short prompts. The twelve Exercise 3 items improve coverage but do not yet reproduce the depth or space for multi-step working evident in the official reference. The correction also ends with a sparse page for 3l. No page-count padding should substitute for deeper original tasks and appropriate working space. The indicative quarter-point criteria and the 3 h 30 duration still need an independent NSI teacher's judgement and a supervised learner timing/marking trial.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** Preserve this checkpoint alongside the V17, V16 and V15 live holds and the V12–V14 failed attempts. Further app-owned depth and page-flow work should be verified test-first, then assessed with another source-pinned live PDF and page-by-page official comparison before freezing shared source or launching the expensive UK/French matrix. Document-level rights and accessibility evaluation remain external gates. The practical component is unsupported; issues #4 and #8 remain open.
