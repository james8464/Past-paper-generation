# French NSI V21 incident audit live diagnostic — 10 October 2026

**One pinned written training paper passed automated checks on its first attempt; manual product fidelity remains on hold.** This is an engineering diagnostic, not a teacher review, learner trial, accessibility approval or model-selection result. Protected PR #57 introduced the version-isolated eight-incident database audit and merged after Backend and macOS checks passed.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #57, `f4e26579b619c030ff883111ad77d2275aa9081c`; implementation SHA-256 `3fb2f520134869f00c76aeac32d9ff07bcbd8ff8e5b8863beadfdca4bcda034b` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 130.03 seconds; backend peak RSS 135,249,920 bytes, excluding Ollama |
| Subject | Nine A4 pages, SHA-256 `c20b2755b52fbbc867ae72ae58bc848c9da40ac57e1542ada593aeb0c8fe1a74` |
| Proposed correction | Eighteen A4 pages, SHA-256 `8e941356201856b31652203b638af3cbfdf34c95d68d1de12ba614b8d31c7b62` |
| Package and manifest | SHA-256 `ce45bdeed53a45b1164296b513573f5abe33282b4e258360e9f5f6ec22a2de1d`; `ba69680ca2ac572d8b556414285f0d84d9bd9bbf95e0f8fa34fe4daae08fbe26` |
| Preserved local evidence | `tmp/pdfs/french-v21-incident-audit-20261010/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v21-incident-audit-20261010/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-7427763876f3/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of both generated PDFs and all sixteen official pages was rendered and visually inspected with the PDF workflow. Counts indicate depth and space, not a required 2027 template. No official correction was compared.

| Measure | Official 2026 subject | V21 training subject |
|---|---:|---:|
| A4 pages | 16 | 9 |
| Independent written exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 12 = 32 |
| Exercise spans | Pages 2–5, 6–10, 11–16 | Pages 2–3, 4–6, 7–9 |

The official exercise spans develop linked figures, code, datasets and changing situations over successive pages. The V21 database audit adds genuinely staged work, but it does not yet match that sustained reasoning or provide enough candidate working space.

| Subject page | Visual finding and comparison |
|---:|---|
| 1 | Clear “Sujet d’entraînement — non officiel” cover, written scope and distinct 18-technical-plus-2-indicative-language scale. |
| 2 | E1 graph, faulty search code and link-outage context are legible, without visibly crossed or hidden labels. |
| 3 | All ten E1 questions and search working material crowd one page. The official E1 develops connected routing and security over four pages. |
| 4 | E2 database audit context and tables are legible. |
| 5 | E2 incident data, staged work table and 2a–2f are associated, but answer-working space is tight. |
| 6 | E2 2g–2j and state/function working tables are legible. This is more staged than V20, though still shallower than the official five-page E2. |
| 7 | E3 network, process and security context with linked materials is legible. |
| 8 | E3 intermediate questions and working tables remain associated; no visible clipping. |
| 9 | Only 3j–3l occupy the upper part of a mostly unused page, despite limited working space earlier. |

The proposed correction was checked for legibility, attribution and page flow, not against an official marking scheme.

| Correction page | Visual finding |
|---:|---|
| 1 | Teacher-facing “Corrigé proposé et barème indicatif” cover is separate from candidate instructions. |
| 2 | General marking guidance and separate indicative two-point French-language rubric are legible. |
| 3 | E1 context, graph and code reproduce the candidate materials without visible clipping. |
| 4 | E1 1a–1d answers and credit rows are legible. |
| 5 | E1 1e–1g answers and credits remain attributed. |
| 6 | E1 1h–1i answers and credits are readable. |
| 7 | E1 1j occupies a sparse page; its answer and credit stay together. |
| 8 | E2 context, schema and first data tables are legible. |
| 9 | E2 incident data and early answers/credits are legible. |
| 10 | E2 intermediate answers and credit rows remain associated. |
| 11 | E2 2f and its state material and credit are legible. |
| 12 | E2 2g and function material and credit are legible. |
| 13 | E2 2h–2j answers and credits are legible. |
| 14 | E3 context and opening answer/credit are legible. |
| 15 | E3 route and process answers/credits are attributed. |
| 16 | E3 intermediate process/security answers and credits are legible. |
| 17 | E3 later answers and credit rows remain attributed. |
| 18 | E3 3l and its credit occupy a sparse final page. |

No clipping, obscured graph labels or candidate-facing answer leakage was seen at the inspected scale. Automated source isolation, exact scoring and deterministic checks passed, but do not establish exam equivalence. The package contains exactly 18 technical points across the three exercises plus a distinct two-point indicative French-language component. Correction length mainly reflects answer/credit pagination, not candidate task depth.

**Decision: manual fidelity HOLD after an automated first-attempt pass.** V21's eight-incident audit improves E2 sequencing, yet E1 remains dense, E3 ends sparsely, and the subject still has less sustained multi-step reasoning and usable working space than the official comparator. Do not pad pages merely to match its count. Preserve this result alongside V20–V15 live holds and V12–V14 failed attempts. No French model is selected; the final UK/French matrix is premature while shared French source changes. Independent NSI teachers must judge correctness, marks and quarter-point granularity; a supervised learner trial must measure timing and ambiguity. Rights and accessibility checks remain external gates. The practical component is unsupported, and issues #4 and #8 remain open.
