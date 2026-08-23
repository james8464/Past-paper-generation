# Measured Paper Fidelity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise structural and visual fidelity across every supported paper by replacing duplicated answer/blank-page geometry with measured board profiles and by qualifying changes with page-role-aware comparisons and manual contact sheets.

**Architecture:** Extend the existing fidelity audit to classify comparable page roles and report stable-content scores. Add one renderer-independent ReportLab page-role module containing AQA and OCR additional-answer, ruled-continuation, blank, footer, and barcode geometry; family renderers remain responsible for question content but delegate these repeated page shells. Consolidate mark-scheme covers through the existing shared cover module, then rerender all 18 papers and reject any document regression.

**Tech Stack:** Python 3.12, ReportLab, PyMuPDF, Pillow, pytest, Ruff, Graphify.

**Spec:** `docs/superpowers/specs/2026-08-23-contract-first-paper-generation-design.md`

## Global Constraints

- Generated content must remain independently authored and visibly labelled unofficial; do not ship exam-board logos or protected source PDFs.
- Preserve exact marks, AO allocations, page counts, required output roles, and current publication gates.
- A renderer change must not reduce any primary document's fidelity score by more than 0.5 percentage points.
- Each visual change requires a page-specific red/green geometry test and inspection of the regenerated reference/generated/difference contact sheet.
- Run `graphify update .` and commit after every task; remain on `main` and do not push.

---

### Task 1: Page-role-aware fidelity evidence

**Files:**
- Modify: `tools/paper_fidelity_audit.py`
- Modify: `tests/test_paper_fidelity_audit.py`

**Interfaces:**
- Produces: `classify_page_role(text: str, *, document_role: str, page_number: int) -> str`
- Produces: `role_scores: dict[str, dict[str, float | int]]` in each document result
- Consumes: existing registered masked-render and text-layout page measurements

- [x] **Step 1: Write failing classification and aggregation tests**

Add table-driven tests covering `cover`, `question_content`, `mark_scheme_content`, `additional_answer`, `ruled_continuation`, `intentional_blank`, and `end_page`. Add a two-role aggregation test proving variable question prose cannot make the answer-page role disappear.

- [x] **Step 2: Run the focused tests and confirm the new interfaces are absent**

Run: `PYTHONPATH=. .venv/bin/pytest -q tests/test_paper_fidelity_audit.py`

- [x] **Step 3: Implement classification and role summaries**

Classify from normalised extracted text plus document role, keeping the rules board-neutral. Aggregate page count, mean `overall`, `registered_masked_render`, `registered_text_layout`, and `stable_area` by role. Include the role on every page comparison and in JSON/Markdown output.

- [x] **Step 4: Run focused tests and audit the current 18-paper baseline**

Run the focused suite, then run `tools/paper_fidelity_audit.py` against `tmp/pdfs/deterministic-render-qualification-2026-08-23` at 96 DPI. Confirm 36 primary documents are comparable and the aggregate remains within 0.5 points of 67.9%.

- [x] **Step 5: Refresh Graphify and commit**

Commit message: `Measure fidelity by document page role`

### Task 2: Shared board answer-page geometry

**Files:**
- Create: `Backend/Core/exam_pages.py`
- Create: `tests/test_exam_pages.py`
- Modify: `Resources/accounting/aqa/generator/aqaaccountgen/render_pdf.py`
- Modify: `Resources/business/aqa/generator/aqabizgen/render_pdf.py`
- Modify: `Resources/economics/aqa/generator/aqaecongen/render_pdf.py`
- Modify: `Resources/computer-science/aqa/generator/cspapergen/render_pdf.py`
- Modify: corresponding family render tests

**Interfaces:**
- Produces: `ExamPageProfile(board: Literal["aqa", "ocr"], code: str, heading: str, variant: Literal["additional", "continuation", "blank"], legal_notice: bool = False)`
- Produces: `ExamPage(Flowable)` and `draw_exam_page(canvas, profile, *, width, height) -> None`
- Consumes: family font names and the shared deterministic barcode pattern

- [x] **Step 1: Add red geometry tests from measured reference boxes**

Render synthetic AQA additional, continuation, and blank leaves. Assert the question-number gutter, instruction band, ruled-area bounds, line spacing, footer baseline, barcode bounds, and legal-notice exclusion zone against measurements from the AQA reference corpus.

- [x] **Step 2: Implement the shared profile and canvas renderer**

Keep coordinates in the reference PDFs' measured point space, save/restore canvas state, draw only board-shaped generic furniture, and expose the same geometry as a full-page Flowable for Platypus families and a canvas function for AQA Computer Science.

- [x] **Step 3: Migrate the four AQA renderers one family at a time**

Replace duplicated `_additional_answer_page`, `_draw_extra_answer_page`, and final blank-page shells. Preserve page plans and question content. Run each family suite immediately after its migration.

- [x] **Step 4: Rerender all AQA papers and inspect role sheets**

Run the deterministic matrix with `--resume` into a fresh output root, audit it, and inspect every AQA `additional_answer`, `ruled_continuation`, and `intentional_blank` sheet. Require no document regression beyond 0.5 points and improved mean role geometry.

- [x] **Step 5: Refresh Graphify and commit**

Commit message: `Unify measured AQA answer pages`

### Task 3: OCR response and blank-page grammar

**Files:**
- Modify: `Backend/Core/exam_pages.py`
- Modify: `tests/test_exam_pages.py`
- Modify: `Resources/computer-science/ocr/generator/ocrcsgen/render_pdf.py`
- Modify: `Resources/economics/ocr/generator/ocregen/render_pdf.py`
- Modify: corresponding OCR family tests

**Interfaces:**
- Consumes: `ExamPageProfile` and `ExamPage`
- Produces: OCR open ruled response leaves with OCR-specific heading/footer placement and no AQA-style enclosing answer box

- [x] **Step 1: Add failing OCR geometry tests**

Assert reference-matched open rule width, 8 mm line rhythm, left question-number guide, heading baseline, page folio, and restrained footer. Assert blank transition leaves contain only their declared messages and no enclosing answer table.

- [x] **Step 2: Implement OCR variants in the shared primitive**

Use the same profile interface but distinct OCR drawing functions; do not share AQA coordinates. Keep legal copy outside the response region.

- [x] **Step 3: Migrate OCR Computer Science and OCR Economics**

Replace both table-based `_additional_answer_page` implementations and their blank/transition shells. Preserve current bounded page counts and the OCR Economics overflow fix.

- [x] **Step 4: Run OCR suites, rerender five OCR papers, and inspect all response roles**

Require release-PDF validation, unchanged page counts, retained question marks, and improved OCR answer/blank role scores.

- [x] **Step 5: Refresh Graphify and commit**

Commit message: `Match OCR response page geometry`

### Task 4: Shared mark-scheme cover calibration

**Files:**
- Modify: `Backend/Core/exam_cover.py`
- Modify: `Resources/computer-science/aqa/generator/cspapergen/render_pdf.py`
- Modify: shared/family cover tests

**Interfaces:**
- Consumes: existing `CoverProfile` and `MarkSchemeCover`
- Produces: one neutral two-line Paper Creator wordmark with board-specific title baselines, rules, barcode, folio, and footer

- [ ] **Step 1: Add failing cover bbox tests for AQA and OCR**

Measure the shared wordmark envelope, horizontal-rule baseline, qualification/code/title baselines, barcode box, folio, and footer against the local references. Test generic geometry only; do not assert board logo pixels.

- [ ] **Step 2: Calibrate `MarkSchemeCover` and remove the AQA Computer Science duplicate**

Route AQA Computer Science through the shared cover. Retain generated date, unofficial status, metadata, and controlled fonts.

- [ ] **Step 3: Render one scheme per family and inspect cover contact sheets**

Require improved `cover` role geometry for all shared-cover users and no decrease beyond 0.5 points for Edexcel's separate reference-specific cover.

- [ ] **Step 4: Refresh Graphify and commit**

Commit message: `Calibrate shared mark scheme covers`

### Task 5: Full visual qualification and regression gate

**Files:**
- Create: `Resources/fidelity-thresholds.json`
- Modify: `tools/paper_fidelity_audit.py`
- Modify: `tests/test_paper_fidelity_audit.py`
- Modify: `docs/ASSESSMENT_QUALITY.md`
- Modify: `docs/ARCHITECTURE.md`

**Interfaces:**
- Produces: `--thresholds PATH` and non-zero exit on missing documents, excessive per-document regression, or role-score failure
- Consumes: the post-improvement 18-paper report as the versioned minimum baseline

- [ ] **Step 1: Add failing threshold tests**

Cover missing families, a 0.6-point document regression, a failed page-role minimum, and a passing report. Error output must name family, document, role, expected score, and observed score.

- [ ] **Step 2: Implement the fail-closed gate and compact threshold schema**

Store only family/document/role minimum scores and the audit schema version; never commit generated PDFs, raster pages, or official reference content.

- [ ] **Step 3: Generate a fresh deterministic 18-paper matrix**

Run without `--resume`, release-validate all declared roles, run the fidelity gate, and generate all overview, worst-page, and per-document contact sheets.

- [ ] **Step 4: Manually inspect every contact sheet**

Record a checklist covering covers, candidate boxes, typography, margins, page folios, answer rules, mark boxes, tables, diagrams, graph labels, scheme tables, levels, and intentional blanks. Fix every concrete defect and repeat the affected family plus the full gate.

- [ ] **Step 5: Run repository and distribution verification**

Run Ruff, the full Python suite, `make agent-verify`, and `make preflight-app-store`. Update architecture/quality docs with the measured qualification boundary.

- [ ] **Step 6: Refresh Graphify and commit**

Commit message: `Gate releases on measured paper fidelity`
