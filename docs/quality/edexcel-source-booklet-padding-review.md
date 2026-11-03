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
