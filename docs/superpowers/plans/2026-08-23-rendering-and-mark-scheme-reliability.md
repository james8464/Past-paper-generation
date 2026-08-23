# Rendering and Mark-Scheme Reliability Implementation Plan

**Goal:** Make every supported document render bounded and atomic, reject malformed page content before publication, and require mark schemes to contain examiner-usable depth rather than renderer-added filler.

**Architecture:** Generator CLIs will call one shared render transaction that writes to a same-directory temporary file, enforces a per-role deadline, validates that a readable non-empty PDF was produced, and atomically promotes it. Release validation will add conservative text-collision and density evidence without rejecting intentionally sparse covers or answer pages. Mark-scheme validation will operate on the renderer-independent assessment package and use question type, marks, and AO allocation to enforce specific minimum content.

**Tech stack:** Python 3.12, Pydantic, ReportLab, PyMuPDF, pytest, Ruff, Graphify.

---

## Task 1: Bounded atomic render transactions

- Add `Backend/Core/render_transaction.py` with typed timeout/output failures.
- Use a Unix main-thread deadline, preserve any outer timer, clean temporary files on every failure, and promote with `os.replace` only after PyMuPDF opens the artifact.
- Add red/green unit tests for success, timeout, invalid output, renderer exceptions, and replacement of an existing destination.
- Commit with an updated Graphify map.

## Task 2: Route every generator family through the transaction

- Update all seven package CLIs so question papers, mark schemes, and source booklets use stable role labels and the shared 30-second gate.
- Keep renderer functions directly testable; bound the production orchestration boundary.
- Extend CLI tests to prove partial artifacts are never returned or published.
- Commit with an updated Graphify map.

## Task 3: Artifact containment, collision, and density evidence

- Extend `Backend/Core/pdf_validation.py` to record per-page text, drawing, image, occupied-area, and line-collision metrics.
- Reject text outside safe boxes, exact/near-exact overlapping text spans, unreadable fonts, empty pages, and unexplained content-free pages.
- Treat covers and answer-space pages by role/profile rather than applying one global density threshold.
- Store the metrics in the qualification manifest and cover them with synthetic-PDF tests.
- Commit with an updated Graphify map.

## Task 4: Mark-scheme depth contracts

- Add deterministic validation for accepted points, working, alternatives, common errors, evidence binding, level descriptors, AO coverage, and subpart correspondence.
- Replace generic enrichment that merely repeats syllabus prose with question-specific guidance derived from the structured item.
- Add regressions for short calculations, data response, extended response, accounting follow-through, and computer-science pseudocode.
- Commit with an updated Graphify map.

## Task 5: OCR Economics pagination regression

- Build an adversarial long-content fixture reproducing the previous non-terminating mark-scheme case.
- Ensure tables split or compact deterministically and complete within the render budget without clipping or losing marking points.
- Verify expected page roles and measured content density.
- Commit with an updated Graphify map.

## Task 6: Phase qualification

- Run repository-wide Ruff, the complete Python suite, strict Swift build/tests, and App Store preflight.
- Rerender deterministic samples for all 18 supported papers and run release PDF validation.
- Update architecture/quality documentation, refresh Graphify, commit, and leave `main` clean and unpushed.

