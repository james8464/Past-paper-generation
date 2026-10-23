# French NSI V27 live comparison — 23 October 2026

## Result

One pinned V27 run passed automated checks on its first attempt with zero repairs. The marking mismatch in 3l is fixed: its printed question, answer and two quarter-point criteria now agree. Metadata is assessed in 3j, not rewarded again in 3l. **Overall manual fidelity remains HOLD**, not an educational or model-independent equivalence claim.

The run used the clean proposed source commit `02a9e9d` on PR #74, before its merge. Source was not edited during generation. This is a new live run, not a retained-package replay.

| Identity | Value |
|---|---|
| Prompt / seed | `fr-nsi-written-2027-v27` / `270100` |
| Implementation SHA-256 | `a2969ee4346bc7b33670123a470158256651cd027b933100ed4eecbd16665d76` |
| Model | `gemma4:12b` |
| Model digest | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` |
| Reference-index SHA-256 | `ec2339e6dffeba485f94d33d8e6f868e24cd2c40ad32830621201496ca32d594` |
| Completed UTC | `2026-10-23T21:53:56.528914+00:00` |
| Runtime / backend peak RSS | 138.312 seconds / 135,692,288 bytes, excluding Ollama |
| Subject | 13 A4 pages, 34 questions; SHA-256 `10acaa93dd2efde3c49267d2a9e1bdc15480acc2d0068f0d241f787636e59711` |
| Correction | 20 A4 pages; SHA-256 `f77d7a6998a5133cc6692fca7075b5b3e5b845456b05a1abdc35705a39781f92` |
| Assessment | SHA-256 `ca91f1507224d3afcc4c8b56d09ac14e46317cc107174b0bfc72c2b4b860b7e2` |
| Manifest | SHA-256 `a786c26ed4638c587e1f257e311f412214da096da5360af68e6884d025078869` |

All attempts, checkpoints, PDFs and renders are retained, ignored, under `tmp/pdfs/french-v27-marking-alignment-20261023/`. Older V26–V15 holds and V12–V14 failures remain unchanged.

## Page review and comparison

All 33 generated pages were rendered at 80 dpi with Poppler. Binary comparison of the rendered PNGs confirms subject pages 1–12 and correction pages 1–19 are identical to the previously reviewed V26 pages. The page-by-page findings in `french-nsi-v26-incident-timeline-live-diagnostic-2026-10-16.md` therefore remain applicable. The two changed pages, subject 13 and correction 20, were inspected visually in this run: readable text, table borders, answer/rubric association and footer; no clipping or overlap at inspected scale.

The same official comparator is retained locally: `Reference Corpus/france/nsi/nsi-2026-normal-metropole-jour-1.pdf`, SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`, [official source](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf). All its pages were reviewed in the prior V26 comparison; pages 1, 5 and 15 were re-inspected here against generated cover, security reasoning and database work. No official correction was compared.

| Dimension | Finding |
|---|---|
| Accuracy | Revised 3l correctly distinguishes arrival 20 versus deadline 19 and report delivery 28 versus deadline 29; terminal plaintext remains exposed before encryption/after decryption. Retained E2 SQL/state answers were read again: targeted updates and S0/S1/S2 counts are consistent with the documented task. |
| Marking | The known missing terminal criterion and repeated metadata reward are removed. Both 0.5 and 0.75 profiles are tested. This does not establish learner-calibrated mark granularity. |
| Layout | Changed pages are legible. Existing sparse E1 pages 4–5, E2 page 10 and E3 page 13 remain. E1 page 5 also prints the implementation-like label `route_double_fermeture`; this is less polished than the official paper's human-facing labels. |
| Question quality | The official paper sustains longer construction and interpretation across graph/tree/code/database contexts. V27 retains relatively compact finite tasks and substantial repeated tracing. Correctness checks do not demonstrate comparable difficulty or workload. |
| Structure | Three independent exercises, exact 18 technical plus distinct 2 indicative language points, non-official labels and French-only retrieval remain. The official 2026 paper is 16 pages/36 questions; those counts are diagnostic, not a target to reach by padding. |

## Checks and next gate

Final local suite: 2901 passed, 2 skipped. Ruff, repository hygiene, release-compliance metadata and diff checks passed. Retained V26 live assessment replay passed under the revised code. Protected Backend/macOS checks remain mandatory for PR #74.

Next engineering work should address human-facing table labels and overly fragmented candidate flow, then substantive construction depth. Do not increase page count with blank space. Keep the expensive final model matrix gated until source is frozen and the manual comparison passes. Teacher review, learner timing/mark calibration, accessibility and document-specific rights clearance remain external; no practical-component, examiner, Apple, school, regional or prize approval is claimed.
