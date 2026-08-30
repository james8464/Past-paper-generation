# Current-family visual qualification — 26 August 2026

## Scope and claim

This record covers the 18 papers advertised by registry schema 3. It supports
the **visually calibrated** claim only. It does not claim official endorsement,
identical branding, equivalent difficulty, or empirical calibration.

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
