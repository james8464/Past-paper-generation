# Current-family visual qualification — 26 August 2026

## Scope and claim

This record covers the 18 papers advertised by registry schema 3. It supports
the **visually calibrated** claim only. It does not claim official endorsement,
identical branding, equivalent difficulty, or empirical calibration.

**31 August qualification status:** subsequent live/content checks reopened
Accounting source/marking and Computer Science solver/objective defects. The
historical deterministic visual results below are not current all-route live
or content sign-off. See the continued-qualification record at the end.

The qualification used fixed-seed deterministic packages so renderer geometry
could be isolated from model variability. Each question paper and mark scheme
was compared with same-role pages from at least three locally held reference
years. Official PDFs, generated PDFs, raster pages, and overlays remain local
and untracked.

## Automated evidence

- Qualification rasterisation: 600 DPI, 5 mm non-printable boundary.
- CI reproduction: 300 DPI, 4.2 mm non-printable boundary.
- Aggregate registered similarity: 0.708 at both resolutions.
- Primary documents: 36 (18 question papers and 18 mark schemes).
- Contact-sheet artifacts: 152 at each resolution.
- Print failures: 0.
- Every primary PDF has a structure tree, embedded fonts, safe-print content,
  selectable text, valid reading order, sufficient monochrome contrast, and
  rules at or above the configured minimum width.
- Every document and observed page role met its versioned floor in
  `Resources/fidelity-thresholds.json`.

| Family and paper | Question paper | Mark scheme | Outcome |
|---|---:|---:|---|
| AQA Accounting 1 | 0.709 | 0.650 | Pass |
| AQA Accounting 2 | 0.708 | 0.706 | Pass |
| AQA Business 1 | 0.710 | 0.689 | Pass |
| AQA Business 2 | 0.731 | 0.706 | Pass |
| AQA Business 3 | 0.720 | 0.707 | Pass |
| AQA Economics 1 | 0.755 | 0.734 | Pass |
| AQA Economics 2 | 0.748 | 0.718 | Pass |
| AQA Economics 3 | 0.690 | 0.756 | Pass |
| AQA Computer Science 1 | 0.691 | 0.711 | Pass |
| AQA Computer Science 2 | 0.694 | 0.707 | Pass |
| OCR Computer Science 1 | 0.749 | 0.665 | Pass |
| OCR Computer Science 2 | 0.740 | 0.666 | Pass |
| OCR Economics 1 | 0.791 | 0.627 | Pass |
| OCR Economics 2 | 0.745 | 0.630 | Pass |
| OCR Economics 3 | 0.727 | 0.663 | Pass |
| Pearson Edexcel Economics A 1 | 0.733 | 0.655 | Pass |
| Pearson Edexcel Economics A 2 | 0.730 | 0.703 | Pass |
| Pearson Edexcel Economics A 3 | 0.725 | 0.682 | Pass |

## Manual review

The six worst-page overview sheets collectively covered every primary
document. The reviewer checked cover hierarchy, candidate fields, typography,
margins, rules, barcodes, folios, question numbering, mark placement, answer
space, tables, diagrams, graphs, page density, continuation pages, scheme grids,
level tables, clipping, overlaps, broken labels, and malformed pages. The
per-document contact sheets were used to confirm page-role coverage and inspect
the specific role flagged by the audit.

No blocking layout defect remained. AQA Computer Science Paper 2 and Pearson
Edexcel Economics A Papers 1–3 passed after their cover, page furniture,
answer-space, table/graph, and scheme layouts were moved onto the measured
shared profiles. AQA Economics footers were subsequently moved inside the 5 mm
qualification margin and the complete 600-DPI matrix was rerun.

The largest remaining visual differences are intentional: Paper Creator uses
neutral branding and omits protected exam-board logos, legal notices, and
candidate-identifying material. OCR end pages and some scheme covers therefore
score lower than content pages. These differences are recorded in the
thresholds and are not presented as defects or as official papers.

## Evidence locations

The reproducible metric files and image artifacts are intentionally ignored by
Git:

- `tmp/fidelity/deterministic-role-metrics-v13-ci.json`
- `tmp/fidelity/artifacts-v13-ci-300/`
- `tmp/fidelity/deterministic-role-metrics-v16-qualification.json`
- `tmp/fidelity/artifacts-v16-qualification-600/`
- `tmp/fidelity/deterministic-role-metrics-68b45e1-ci.json`
- `tmp/fidelity/artifacts-68b45e1-ci-300/`

Durable, reviewable policy and qualification evidence is versioned in:

- `Resources/fidelity-thresholds.json`
- `Resources/print-profiles.json`
- `Resources/generator-registry.json`
- `docs/ASSESSMENT_QUALITY.md`

## Outstanding non-visual gates

All 18 empirical gates remain false. Live two-seed model variability and blind
review by independent subject specialists are separate evidence requirements;
they cannot be inferred from deterministic visual qualification.

## 30 August Paper 2 mark-scheme regression check

A fresh 300-DPI audit caught a real regression after repetitive examiner
boilerplate was removed from AQA Computer Science Paper 2: the mark scheme
retained its measured 35-page structure but its registered document score fell
to 0.648, below the 0.679 release floor. The renderer and floor were left
unchanged. Each of the 35 sub-questions instead received question-specific
standardisation guidance covering acceptable equivalents, required units or
syntax, and the misconceptions that must not receive credit.

The package was regenerated through `tools/live_generation_matrix.py` with
seed 8464 and audited at 300 DPI with the CI print profile. The question paper
scored 0.680 and the mark scheme 0.702. All font, tagging, safe-print, contrast,
rule-width and reading-order checks passed. Manual review of all five mark
scheme contact sheets found no clipping, collision, malformed table or broken
continuation page. This is deterministic visual and content-structure evidence
only; it does not change the outstanding empirical gates above.

The same commit was then used to regenerate the complete 21-job advertised
matrix (18 full papers and three topic question banks). All jobs completed with
fresh manifests. The full 300-DPI audit passed every versioned document and
page-role floor with aggregate registered similarity 0.708. All six worst-page
overview sheets were reviewed; no clipping, collision, broken rule, malformed
visual, missing page furniture or unsafe print placement was found. The lower
OCR scheme end-page scores remain the documented neutral-branding difference,
not a missing content page.

## 30 August shared-renderer and economics-scheme qualification

Commit `8fee27c` was qualified after the shared AQA/OCR header and measured-panel
migrations and after restoring item-specific AQA Economics guidance and
source-relevant Edexcel Economics marking points. A clean fixed-seed matrix
(`26083030`) completed all 21 advertised routes: 18 complete papers and three
AQA Computer Science question-bank routes.

The complete matrix passed the locked document and page-role thresholds at
both resolutions without changing `Resources/fidelity-thresholds.json`:

- 300-DPI CI profile: aggregate 0.707, 18 paper families, 36 primary PDFs,
  151 contact sheets and zero print failures;
- 600-DPI qualification profile: aggregate 0.706, the same 18 families and 36
  primary PDFs, 151 contact sheets and zero print failures;
- AQA Economics Paper 2 mark scheme: 0.726 at 300 DPI and 0.725 at 600 DPI;
- Pearson Edexcel Economics A Paper 1 mark scheme: 0.654 at both resolutions.

The AQA and OCR production migrations were first compared against the previous
fixed-seed PDFs and produced no text, font, bounding-box or page-size changes
across all 28 affected documents. The newly changed economics mark-scheme
contact sheets and their same-role official comparisons were then inspected at
page level. Marking grids, continuation rows, level tables and mark columns fit
without clipping, collision or broken rules; the restored guidance remains
question-specific rather than repeating common boilerplate.

Local reproducible evidence:

- `tmp/pdfs/dsl-final-fixed-2026-08-30/`
- `tmp/fidelity/dsl-final-fixed-2026-08-30-ci.json`
- `tmp/fidelity/dsl-final-fixed-2026-08-30-ci-artifacts/`
- `tmp/fidelity/dsl-final-fixed-2026-08-30-qualification.json`
- `tmp/fidelity/dsl-final-fixed-2026-08-30-qualification-artifacts/`

This is deterministic engineering and visual evidence. It does not change the
empirical difficulty gates: independent subject review and representative
student-response evidence are still required before claiming equivalent
difficulty.

## 31 August continued qualification

### Accounting Paper 1

The accepted seed-26083031 content was replayed using the production atomic
render transaction. Scoped 300/600-DPI audits passed all unchanged document and
page-role floors and print policies, with aggregate scores 0.685/0.684. This
corrects an earlier QA replay which had bypassed that transaction and omitted
PDF accessibility tags; the original live export was tagged. It is a replay,
not new AI generation, and predates the shareholder source correction.

| Manual field | Observation / outcome |
|---|---|
| Typography, page furniture, numbering, marks | Baseline contact sheets show consistent placement; automated font embedding/print policies pass. Pixel-identical layout is not claimed. |
| Cover, instructions, answer space, continuation pages | All 36 question pages overviewed; no clipping apparent at contact-sheet scale. Neutral branding remains intentional. |
| Tables and sources | Existing shareholder source did not match model input. New contract preview at `c538e93` supplies coherent figures, but page 28 has a collided header and malformed currency grouping. Fix required. |
| Question demand and objective balance | Accounting wrongly inherits AO4; official AO3 includes evaluation. Objective and downstream demand correction remains open. |
| Mark-scheme completeness | All 26 baseline pages overviewed. New preview's last three shareholder reasoning points are absent from the PDF, and general front matter is repeated. Fix required. |
| Source/solver parity | Independent code review found a derived equity total supplied only to the solver and separately written source prose. Fix required. |
| Print | Saved-content baseline passes both resolutions; this does not establish new source content validity. |
| Reviewer outcome | Not finalised. Engineering/visual passes are insufficient while content and calibration defects remain. |

Both Accounting papers were regenerated at seeds 42, 20260830 and 26083031 after
`c538e93`: six preview package checks passed. The three changed source pages
were inspected individually, plus the affected scheme pages; these previews
are not live AI-authorship evidence. Review fixes are tracked under programme
Task 7.A, with broader objective/guidance corrections tracked separately.

Evidence: `tmp/pdfs/excellence-accounting-replay-tagged-26083031/`,
`tmp/fidelity/excellence-accounting-tagged-300.json`,
`tmp/fidelity/excellence-accounting-tagged-600.json`,
`tmp/pdfs/excellence-shareholder-<seed>/`, and
`tmp/fidelity/excellence-shareholder-pages/`.

**Correction at `a92f2c5`:** the source-contract defects above are now fixed.
Candidate/solver/PDF facts agree, the derived solver-only total is removed, all
eight scheme points render, amounts have explicit units, and header words fit
their own padded cells. Both papers passed three-seed previews after the source
repair; the final header-only change passed three more Paper 1 previews. The
controller inspected each final source page. Scoped final 300/600-DPI checks
passed unchanged thresholds and print policies, scores 0.681/0.680, with zero
failures. Evidence: `tmp/pdfs/excellence-shareholder-round2-<seed>/` and
`tmp/fidelity/excellence-shareholder-round2-{300,600}.json`. The full backend
suite passed 857 tests, with 2 skips. Objective calibration and repetitive
general guidance remain unresolved; the family is still not finalised.

### 1 September H1 task/source/demand qualification

H1's bounded Economics, Business and shared review-contract scope is accepted
through `ff16a3f`; this is not whole-paper or product qualification. The final
backend suite passed 1,722 tests with two expected skips, the warning-strict
macOS build passed, and Graphify was updated. The nine affected routes produced
27 deterministic three-seed builds containing 60 PDFs and 27 JSON packages;
the controller manually checked the changed AQA/OCR Economics and AQA Business
question pages after measured tariff, choice-gutter and margin-note regressions.

The independent source review completed all bounded repair rounds with no
remaining Critical, Important or Minor findings. Candidate text, selected-answer
contracts, figures and keys now project from shared typed sources; all 15
supported selected operations have explicit unit, precision and domain policy.
Raw model cognitive-operation observations remain distinct from versioned,
candidate-hashed public-task evidence, which is recomputed at resume and export.

Fresh committed-source live controls passed without editing or normalising model
responses:

- Edexcel Economics Papers 1, 2 and 3 selected transactions:
  `f3b8b05e31d221debc4ff30cdf14cfa4aa65e7fd92c187bcbf3c19c07888ba5c`,
  `01d733fc82bf74f4c93c7f887621012c009dbc5fd73643d06ed73fe8d0e57ce8`,
  and `d964d440a27df7cbdc9e3ba0432b69270e58d47c76afa02f216047bdb6aed295`.
- AQA Computer Science SQL SELECT and INSERT transactions at `ff16a3f`:
  `018ad1946605b35f70c596734a2ffd6c6775d9558bfeb1368787de5096d76383`
  and `85b6eaf0582e6ae056e83b2c0c6fc0d53d0b7edacd5b9965c9d1523fb3072bb1`.

The earlier SQL failures at `f386af4`, `de977c9` and `266f912` remain retained
as failed evidence. They exposed a provider schema that omitted the canonical
`program`, `design` and `trace` tokens and a raw-boundary `null` loophole; both
were corrected fail-closed. H2's content-bound review identity and saved-package
presentation are independently review-clean through `0878b3f`; this is a bounded
implementation acceptance, not a new live or whole-family qualification. H3,
complete two-seed paper qualification and external examiner/learner evidence
remain required before finalisation.

### Computer Science Paper 2

The fresh live AQA run at base seed 26083031 stopped safely at its first final
independent-solution reconciliation after authoring/content-review of 14 question
groups. No PDFs were released. A focused captured probe then demonstrated an
incorrect classification answer passing because closed labels were treated as
a non-exhaustive open response. Source sufficiency and objective calibration
also need correction. This run is retained as a failed qualification attempt,
not omitted from the evidence: `tmp/pdfs/excellence-phase7-live-26083031/` and
`tmp/excellence-cs-solver-probe.json`.
