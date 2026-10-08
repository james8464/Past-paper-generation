# French NSI V16 live diagnostic 8 October 2026

**One source-pinned training paper passed automated checks, but its resemblance to the written baccalauréat remains on hold.** This is a single-paper engineering diagnostic, not the final model comparison or evidence of classroom suitability.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #44, `836b9a3b2eb5d9f8c8f2bc42260ffe5ea8ab25d6`; implementation SHA-256 `a75cf65775f5393d65203ff02d43aa3cd567f86b23426119c4aaf0622600d5be` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 428.415 seconds; backend peak RSS 134,840,320 bytes, excluding Ollama |
| Subject | Seven A4 pages, SHA-256 `de08d2955c721e83b7c4eb92b53f096052c2fd4c0df199f8196dd437641354e4` |
| Proposed correction | Twelve A4 pages, SHA-256 `566d0df88433897207cd0da559cc6adc255391e6defb7b00be542024b0c66c36` |
| Manifest | SHA-256 `d0e9116ec151c6330ff462295086c93f2a266750635fc981ac90a067a8f9c3fc` |
| Preserved local evidence | `tmp/pdfs/french-v21-database-20261008/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v21-database-20261008/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-d1a3cd75747d/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of the generated subject and correction was rendered and visually inspected. The official paper's structure was reviewed against its rendered pages; page count is a comparison signal, not a mandated template for 2027.

| Measure | Official 2026 paper | Generated training subject |
|---|---:|---:|
| A4 pages | 16 | 7 |
| Independent exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 6 + 10 + 6 = 22 |
| Subject exercise span | Pages 2–5, 6–10, 11–16 | Pages 2–3, 4–5, 6–7 |

V16 increased the app-owned database sequence from six to ten questions. Its fixed incident tables, SQL results and Python debugging answers agree with the locked contract, and the candidate-facing context no longer discloses the foreign-key answer to 2a. The graph labels are legible, the Dijkstra trace is broken into rows, and 3e and 3f appear together. Both PDFs carry their required non-official or proposed-correction labels. No clipped text, broken table or missing glyph was apparent at the inspected scale. Those are engineering and visual observations, not a teacher's verdict on correctness, difficulty or marking fairness.

The fidelity gap remains material. All ten database questions fit on one subject page, while the official comparator's second exercise develops eleven questions across five pages. The generated final subject page holds only 3e and 3f with extensive unused space. E1 and E3 remain brief for a stated 210-minute paper. In the proposed correction, the rubric for 1b starts on the next page, as does the rubric for 3d. These splits are readable but weaken page flow. A teacher must assess whether the short prompts, quarter-point credits and worked solutions support the intended level; a supervised learner trial must measure actual completion time.

**Decision: manual fidelity HOLD.** Retain this automated pass alongside the v17 and v15 holds and the v12–v14 failed attempts. Deepen original app-owned E1 and E3 reasoning, improve subject and correction page flow, then repeat one pinned live diagnostic and official page-by-page comparison before freezing source or starting the expensive UK/French matrix. Independent NSI teacher review, learner calibration, document-level rights review and accessibility evaluation remain external gates. The practical component is unsupported. Issues #4 and #8 remain open.
