# French NSI live fidelity diagnostic — 8 October 2026

**One source-pinned paper passed engineering checks on its first attempt; product fidelity remains on hold.** This is a live diagnostic, not the final UK/French model matrix, teacher approval or evidence of learner benefit.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | protected PR #39, `816eb1e48c120b1baa72c0dddcacec4130eca048`; implementation SHA-256 `fc5e0213d0f075adbf7f487f45afd9a4ce6ec894cf214ce5b2b092e9101e6610` |
| Model | local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 387.954 seconds; backend peak RSS 134,791,168 bytes, excluding Ollama |
| Subject | seven A4 pages, SHA-256 `e6b1be0bce75bd8756c77d0084b98680d14751df8dd48ece87bbbb75b396d035` |
| Proposed correction | eleven A4 pages, SHA-256 `a02a9fbefd2f61980d960b79109135a596bbd3ed731fc22be9cf9a7cfdfd4c2f` |
| Manifest | SHA-256 `6f7f562ce55d7dad32717e22a8e26c7cb819fee257460440dfa72b7424769d22` |
| Preserved local evidence | `tmp/pdfs/french-v17-depth-20261008/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v17-depth-20261008/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-2aeeabacd973/` |

The primary visual comparator is the [official 2026 Métropole day-one paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained locally at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every generated subject and correction page was rendered and visually inspected. Official pages 2, 6, 11, 14 and 16 were inspected as representative opening, middle and closing pages of the three exercises; official pages 2–16 were rendered. Page count is a comparison signal, not a mandatory 2027 template.

| Measure | Official 2026 paper | Generated training subject |
|---|---:|---:|
| A4 pages | 16 | 7 |
| Independent exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 6 + 6 + 6 = 18 |
| Subject exercise span | pages 2–5, 6–10, 11–16 | pages 2–3, 4–5, 6–7 |

The seven-link network is a substantive extension of the earlier four-link case, and the generated calculations agree with the locked data. The rendered PDFs show no obvious clipped text, missing glyphs, broken table or blank trailing page. Required non-official and proposed-correction labels are present. These are limited engineering and visual observations, not a teacher's judgement of level or marking fairness.

Material fidelity gaps remain. Subject page 7 contains only question 3f with large unused space; exercise 2 ends around halfway down page 5. The graph in exercise 1 has crossed edges and clustered numeric labels. The Dijkstra solution on correction page 10 is a dense inline paragraph rather than a legible step table; correction page 2 is sparse. Compared with the official paper, all three generated exercises still have shorter, less developed reasoning sequences for a stated 210-minute paper. A learner time trial and independent teacher marking are required to evaluate that mismatch.

**Decision: manual fidelity HOLD.** Retain this first-attempt live engineering checkpoint and all earlier accepted and failed attempts, including the v15 six-page diagnostic and v12–v14 failures. Improve original app-owned exercise depth and graph/solution presentation, then run another pinned French live diagnostic with page-by-page comparison before freezing source or starting the expensive final UK/French matrix. Human NSI teacher review, supervised learner calibration, document-level rights review and accessibility evaluation remain external gates. The practical component is unsupported. Issues #4 and #8 remain open.
