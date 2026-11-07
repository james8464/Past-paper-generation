# Edexcel source-booklet padding review

## Scope

Functional commit `981051af` labels deliberately padded source-booklet leaves
without changing the four-page targets for Papers 1 and 2 or the eight-page
target for Paper 3. It is based on `3934be3b`; integration must retain the later
macro-geometry changes and assign a fresh combined Edexcel prompt identity.
This change does not rebind historical checkpoints or rewrite saved packages.

The preceding frozen-CLI Paper 1 preview, seed 270100, had an unlabelled final
leaf containing only twelve crop-mark paths. Its source-booklet SHA256 was
`66afef36683d98e0884c43e295cc00042e7c072047117c558fdbb409ef0619ce`.
This was pre-existing deliberate padding, not a macro-geometry regression.

## Behaviour

The renderer prints `BLANK PAGE` only when `_pad_pdf_pages` creates a leaf.
Full and overflowing booklets receive no additional pages or labels.

The PDF validator classifies exact visible label-only trailing leaves for
Edexcel Economics source booklets, Papers 1–3, after ordinary page checks.
Images or vector content inside the body prevent this classification, including
lines whose bounding rectangles have zero height or width. A classified blank
followed by actual content is refused. Merely mentioning `BLANK PAGE` in source
prose does not classify an assessed page as padding.

This is evidence classification, not an empty-page exception. The explicit
Paper 2 mark-scheme final-page-36 exception and other roles remain unchanged.
There is no new permission to accept visually empty or malformed pages.

## Local evidence

The corrected red run produced four expected failures and five passing controls.
Initial private test runs also exposed an incorrect report-key assumption and
use of a closed PyMuPDF document in the new tests. Those test mistakes were
corrected; their logs were retained and are not production-failure evidence.

The exact reviewed source passed 50 focused tests in 2.02 seconds:

```text
python -m pytest tests/test_edexcel_source_padding.py tests/test_pdf_validation.py Resources/economics/edexcel-a/generator/tests/test_source_booklet.py -q
```

The new test module explicitly binds the imported Edexcel renderer to the
working checkout. Seed 270100 renders retain 4/4/8 pages, with padding on page 4
of Papers 1 and 2 and pages 6–8 of Paper 3. Every original content page has
identical words, positions and native-resolution rasters when compared with an
unpadded rendering. Blueprint objects remain unchanged. Additional controls
cover full and overflowing booklets, interior padding, ordinary prose mentioning
the label, and assessed vector/line content.

Scoped Ruff checks, formatting and whitespace checks passed. The repository's
existing mypy gate passed its four configured source files; that is not a
type-check claim for the edited PDF validator. Exploratory direct type checking
of that module encountered PyMuPDF typing diagnostics; no suppressions or
unrelated typing changes were added.

Private logs are `tmp/nov3-source-padding-red-corrected.log` and
`tmp/nov3-source-padding-focused-reviewed.log`. Owned fixture PDFs and final-page
PNGs are in `tmp/nov3-source-padding-review/`. The Paper 1 final-page raster was
personally inspected: the centred label is readable, crop marks remain, and no
clipping was seen. This is not an every-page visual-review claim; content-page
equivalence is established by the automated comparisons described above.

## Exact bindings and limits

| Maintained file | SHA256 |
| --- | --- |
| `Backend/Core/pdf_validation.py` | `3f363778f246d59997e856d8243dab10e68ed88c2822d6d0f1a10d2071ab6869` |
| `Resources/economics/edexcel-a/generator/pastpapergen/render_pdf.py` | `9a70998702a98091cdb63be15c45778bf04397468e642a916a520603d48009d6` |
| `tests/test_edexcel_source_padding.py` | `99c88918fc037f37bb2668569d38c3b8023383df369a8bac935859fa9129dfcb` |

Review covered this bounded diff and the complete new 121-line test file,
not the entire Edexcel renderer. Root independently reviewed the production
diff and test file. No full suite, app build, GUI journey, model generation,
teacher review or learner study was performed for this change. Integration,
combined versioning and frozen release checks remain separate work.

## 7 November 2026: Paper 3 source-reference binding

A subsequent EOF source audit at `eae9c151` read the complete Edexcel renderer
(4,200 lines), models (154 lines) and paper configurations (294 lines). Scoped
call-path inspection confirmed that the public adapter publishes the auxiliary
Paper 3 source booklet. That booklet selected questions 0, 1, 3 and 4, then
relabeled them A–D in each section. This did not match the actual question
references: Section A owns Extracts A–C and Section B owns Extracts D–F.
The primary question paper already contained the correctly owned sources.

The bounded repair reuses that existing Paper 3 source-page renderer in the
auxiliary booklet: three source pages per section, with the same merged source
prose and Figures 1–3. It does not duplicate source facts or change the primary
question-paper rendering, blueprint, questions, answers, marks or ordering.
The booklet remains eight pages: cover, six source pages and one labeled blank
padding page. Papers 1 and 2 retain their original four-page rendering paths.

The owned-checkout RED run produced 15 failures and one pass for seeds 42, 123
and 26083051 before the renderer repair. Tests bind the imported renderer to
the edited checkout and independently extract section/extract ownership from
the actual published PDFs; explicit controls cover references B, D, E and F,
all six extracts, every question's source prose and all three figure headings.
A public Paper 3 dry-run also compares the entire published blueprint with the
input blueprint and checks each source against both inline and booklet views.
The extractor excludes only the narrow printed line-number column, not source
numbers. Earlier exploratory invocations used an editable checkout or nested
pytest root; those were corrected and are not relied upon as RED/GREEN evidence.

The final owned-checkout focused gate passed 130 tests (four deselected) in
37.82 seconds, with five existing SWIG deprecation warnings. It covered the new
binding tests, existing booklet/render/source-credit tests, source-padding
controls and applicable app-backend previews, using explicit checkout
`PYTHONPATH` and root `pytest.ini`. Scoped Ruff, formatting and whitespace checks
also passed. The renderer SHA256 is
`5f24e4c8d286af15347179b7dcbca7ae05b7e5e4e74409367f79e5d6c3922388`;
the new binding-test SHA256 is
`0e3272896e791e4fb2c35f17954da4356b6426334826997268dae145ebb44318`.

This is source-binding and deterministic rendering evidence, not an every-page
visual review, full-suite, model-generation, GUI, build, teacher-review or
official-equivalence claim. Independent review and final scoped gate results
are recorded separately with the final file pins; integration metadata and
release gates remain the parent task's responsibility.
