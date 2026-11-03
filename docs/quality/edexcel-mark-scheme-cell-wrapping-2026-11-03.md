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

## Extended offline preview check

At source commit `ba21442ce2cae33d1b541db9e5053b47000e5d74`, the actual family
adapter rendered normal offline previews for Edexcel Papers 1, 2 and 3, seed
270100 and display date 3 November 2026. Module location was asserted. The
comparison used the pre-fix renderer with the same seeded source objects and
preview context; it did not replay a model package under a new identity.

All original marking points and allocation counts remained present. Across the
75 mark-scheme pages, 65 measured answer rows had no text crossing their cell or
bottom boundary. Every one of the 65 changed pages was inspected in page grids;
Paper 2 pages 4 and 24 and Paper 3 page 12 were also viewed at 1100 pixels. No
overflow, clipping, footer collision or broken continuation was found. Mark
schemes had 25, 27 and 23 pages, versus 25, 27 and 26 before the repair. All 120
question-paper/source-booklet pages had identical words, boxes and 1100-pixel
rasters. These checks establish retained preview content and layout only.

Artifacts remain in `tmp/nov3-edexcel-ms-preview-acceptance/`. Its `report.json`
SHA256 is `6c13dc38c344f6dcd00c07786a30d8f6b2ae8a23662cef86f27c4556e405f972`.

## Bounded Gemma Accounting evidence notice

A retained live Accounting Paper 2 test accepted Q06 with a favourable material
usage key, although its stem described purchases rather than actual consumption
and explicitly stated a price above standard. Purchases do not determine usage;
the stated price supports an adverse price variance. Automated acceptance of
that ambiguous question is not a qualification pass.

The native advice now describes this observed false acceptance only for Ollama
`gemma4:12b`, retaining existing name normalization. It does not assert that all
outputs fail, change the memory-fit suggestion, modify generation or claim a
provider-wide defect. The supplied English/French title and detail were added
as two catalogue keys; every old entry, including the previous incomplete-review
translations, remains unchanged. The unused, non-persisted `reviewIncomplete`
enum case and branches were removed after checking for consumers.

Two new Python checks failed before implementation; the quality-guidance and
contrast group then passed all 11 tests. Native assertions cover both languages,
the exact provider/model boundary and existing normalization. They were read but
not executed locally: no native test host was launched. Protected macOS CI and
the later rebased full run remain required, not completed claims.

The following files were read completely through EOF after the change:

| File | Lines | SHA256 |
| --- | ---: | --- |
| `macOS/Keldin/Domain/PaperQualityGuidance.swift` | 129 | `4e40ab2f800785a400b0319f32e013cf42d6e1cf802132e327b89f1932988225` |
| `macOS/Tests/ModelQualityGuidanceTests.swift` | 90 | `5f4b90fccdf45fbf80b72a1cfb9436694415c2fb9841919f68d1db2ecf400cc0` |
| `tests/test_native_model_quality_guidance.py` | 174 | `3d2b2cf4fdde6dfa00f988d10fe4e243838c33bd0815e8e068d9f47251d188e9` |

The catalogue review was scoped to the additions and unchanged-entry comparison,
not a full-file language audit; its ledger status remains pending. The renderer
and its earlier PDF evidence remain bound to the unchanged hashes above.
