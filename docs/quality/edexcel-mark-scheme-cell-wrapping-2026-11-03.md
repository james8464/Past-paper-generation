# Edexcel mark-scheme answer-cell wrapping

The answer-cell renderer could print across the Answer/Mark divider. With the
registered bold face at 11 points, the old 54-character wrapper placed the first
line of “The only correct answer is B: Exports may become more expensive to
overseas buyers” beyond the available width. Character counts did not account
for the selected font or the different bullet inset.

The scoped repair reuses `Backend/Core/document_dsl/text_layout.py:wrap_text`.
One answer-cell layout helper selects the existing face and inset and computes
the available width, leaving six points before the divider. Row measurement and
drawing consume the same wrapped lines. Centred headings remain centred on each
wrapped line. Long tokens split without dropping characters; a cell too narrow
for a glyph refuses instead of overflowing. Question wording, marking content,
font sizes, table geometry, diagrams and unrelated character-based wrappers are
unchanged. Line breaks, row heights and resulting pagination may change.

## Local evidence

The initial boundary subset produced nine failures and four passing controls on
the old renderer. It covered the reported bold sentence, regular and italic
text, bullets, centred headings and long tokens, with normal and narrower cells.
An additional test checks refusal when a glyph cannot fit. A drawing check
verifies that measured row height contains the rendered lines.

The first unpinned invocation imported the editable primary checkout. Its
renderer bytes were verified identical to this branch's base
`3d12c0f5c8c8440255f4bcbe748024dbc5057bbe` (SHA256
`d2c85f5ce72d83b0b25dd8988f6c662699bc4b07a94d5ada45525c2c8cf19778`).
Positive checks explicitly put this worktree's resource package on `PYTHONPATH`;
the boundary test and standalone fixture assert their imported module location.
An unpinned pass is not evidence for the changed worktree.

Using the primary virtual-environment interpreter with that explicit binding,
`test_mark_scheme_layout.py`, `test_renderer_contracts.py` and
`test_document_dsl.py` passed: **86 tests**. Ruff and `git diff --check` passed.
No full suite, application build, model request or installed-helper replacement
was performed for this local check.

The owned two-page fixture is retained under
`tmp/nov3-edexcel-ms-metric-wrap/`, with its driver, geometry report and both
1100-pixel Poppler page images. Both pages were visually inspected. Rightmost
answer ink was 496.491 points before the normal divider at 506, and 350.525
before the narrowed divider at 360. Extracted text retained every non-whitespace
source character. The PDF SHA256 is
`faa251a15f18943b7d224d50832438ea81ea0c7382ad7bdadca3d77104bdea1a`.
These are synthetic layout checks, not educational qualification of a paper.

## Review boundary

The renderer review covers the changed row measurement/drawing helpers,
style predicates, their pagination callers and the reused shared wrapper. It is
**not** a complete-file audit of `pastpapergen/render_pdf.py`; that file remains
pending in the implementation-review ledger.

The complete 562-line `tests/test_mark_scheme_layout.py` was read through EOF,
including the new regressions and existing full-content, typography and
pagination checks. Its SHA256 is
`ce6abcea2ec3a3163f8e46daac5ce9c0ee932dbc21bbd2e28e4201afc8e1d2aa`.
The changed renderer SHA256 is
`ccba221a5c5c46dc1eefd39f440d4f098822c69a1a42f87bdc9a2269e0791bdd`;
the unchanged shared wrapper SHA256 is
`dd9b835a29746b53973668705693498782dfc9249e20bcbb053898850c1ed9e1`.
These hashes describe the local reviewed bytes, not a completed release gate or
a whole-project audit.
