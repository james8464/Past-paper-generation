# French NSI V17 graph and tree live diagnostic 8 October 2026

**One pinned training paper passed automated checks on its first attempt, but manual comparison still places product fidelity on hold.** This is a single-paper engineering diagnostic, not a model selection, teacher review or classroom validation. It uses the V17 graph/tree depth schema introduced by protected PR #47; the earlier [v17 network-depth diagnostic](french-nsi-v17-live-diagnostic-2026-10-08.md) is a distinct historical run.

| Identity | Recorded value |
|---|---|
| Route and seed | `fr-bac-general-nsi-written-2027`, `270100` |
| Merged source | Protected PR #47, `57af558eb3d1a76a254546c0c17f3d993c14f2ed`; implementation SHA-256 `deb21393098e6daa5bc061b902752629c9bb268499ce34a4ed2d7fbe6cdca179` |
| Model | Local `gemma4:12b`, digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| French-only reference index | `Reference Corpus/france/nsi/references.sqlite`, SHA-256 `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Result | `passed`, first attempt, zero repairs; 158.411 seconds; backend peak RSS 134,955,008 bytes, excluding Ollama |
| Subject | Eight A4 pages, SHA-256 `deeed8f69d0d8f05ea79451b139e089c077d1e348b82d41d7342981b56baf070` |
| Proposed correction | Thirteen A4 pages, SHA-256 `33f10db32a5d9a6141ad2dd6550213c90d0249ff1dc9cdf70903e18e36e8a682` |
| Package and manifest | SHA-256 `7e113124d4e4a7a1b6b3b859dd7d42f5471f4a66a4d76379bc4dbd2a891ec985`; `e49880b929130b87a81de293f3f0b8286c86960a348048e569a7235e0e824b47` |
| Preserved local evidence | `tmp/pdfs/french-v24-graph-tree-20261008/runs/gemma4-12b/4eb23ef187e2/270100/result.json`; artifacts under `tmp/pdfs/french-v24-graph-tree-20261008/artifacts/gemma4-12b/4eb23ef187e2/nsi-2027-270100-4d62836e3cf7/` |

The primary comparator is the [official 2026 Métropole day-one written paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf), retained at `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf` with SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`. Every page of the generated subject and correction and all 16 pages of the official comparator was rendered and visually inspected. Page and question counts are comparison signals, not a mandatory template for 2027.

| Measure | Official 2026 paper | V17 training subject |
|---|---:|---:|
| A4 pages | 16 | 8 |
| Independent exercises | 3 | 3 |
| Numbered questions | 10 + 11 + 15 = 36 | 10 + 10 + 6 = 26 |
| Exercise spans in subject | Pages 2–5, 6–10, 11–16 | Pages 2–4, 5–6, 7–8 |

The app-owned graph/tree case now develops ten connected questions across Dijkstra steps, breadth-first traversal, an ABR insertion and two code faults. Its network drawing and weight labels are legible, and the generated subject does not show the corrected code fragments. The proposed correction keeps the E1 questions and their rubrics together at the inspected page boundaries. Both PDFs display their non-official or proposed-correction labels. No out-of-page text or obvious clipping was found at the inspected scale. These are engineering and visual observations, not an educational correctness verdict.

The fidelity gap is still material. The generated E1 has more steps than V16, but its last four questions occupy a mostly empty page; E2's ten questions share one question page; and the final subject page contains only 3e and 3f. The official comparator develops each case through longer, staged contexts, diagrams, code and linked reasoning. The V17 proposed correction also separates the 3d rubric onto page 13 from its answer on page 12, leaving substantial white space. In the 2g rubric, literal Markdown code fences appear around an SQL answer; that is a visible formatting defect. The existing quarter-point credits and expected working still need an independent NSI teacher's judgement and a supervised learner timing trial.

**Decision: manual fidelity HOLD.** Preserve this automated pass alongside the V16, earlier v17 and v15 holds and the v12–v14 failed attempts. Fix the raw-markup rubric and page flow, deepen the original E3 sequence, then repeat a source-pinned live diagnostic and page-by-page official comparison before freezing source or starting the expensive UK/French matrix. Independent teacher review, learner calibration, document-level rights review and accessibility evaluation remain external gates. The practical component is unsupported. Issues #4 and #8 remain open.
