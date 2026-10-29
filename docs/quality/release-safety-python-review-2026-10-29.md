# PDF safety implementation review

Date: 29 October 2026

This is a scoped semantic review and regression record for PDF transactions,
document measurement, pagination and drawing. It is not a whole-project audit,
exam-paper qualification, accessibility certification or release approval.

The reviewed changes were uncommitted on `main-release-safety-audit`, based on
`4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`, when the hashes below were recorded.
The file hashes identify this snapshot independently of later integration.
Graphify was queried before source inspection. The review read the complete
files listed below; formatting and lint results were not counted as semantic
review. Tests and implementation were written by the same reviewing agent.
Independent review and final release gates remain separate work.

## Findings and changes

1. **Deadline setup and restoration.** Nonfinite timeouts previously passed the
   positive-value check. A timer setup failure after replacing the SIGALRM
   handler could leave signal state changed. Timeouts now require finite,
   positive values before creating output directories or touching signals.
   Failed setup and context exit attempt timer cancellation, handler restoration
   and restoration of the previous timer. Secondary restoration errors become
   notes on an existing primary exception. Without a primary exception, the
   first restoration error is raised after the other steps are attempted.

2. **Truthful temporary-file cleanup.** The PDF transaction and tagging writer
   unconditionally unlinked their temporary path after replacement. An ordinary
   missing path was harmless, but a separate permission or I/O failure could
   falsely report failure after a successful commit, or obscure the original
   renderer/tagging exception. Both now use a shared dependency-leaf cleanup
   helper only during exception handling. Cleanup errors retain the orphan path
   and failure in a diagnostic note. KeyboardInterrupt and SystemExit remain
   the original exceptions. Directory-fsync failures remain real publication
   errors; they are not suppressed or reclassified as success.

3. **Finite dimensions and fragment bounds.** Length now rejects NaN and
   infinity while retaining zero and tiny positive values. Pagination validates
   returned split fragments against both available dimensions, not only their
   progress. A final consuming split no longer creates an extra empty page.
   An explicitly declared empty page is still retained. Built-in instruction
   splitting no longer accepts an oversized first item, and question splitting
   does not force a two-line fragment when fewer than two lines fit.

4. **Measured text and drawing share line breaks.** Instructions previously
   allocated wrapped height but drew each item on one line. Long tokens could
   also be measured over several lines and then drawn as one overflowing word.
   A small text-layout dependency now supplies font-metric line breaks for both
   measurement and drawing. It retains token characters and explicit paragraph
   breaks, and fails explicitly if even one glyph cannot fit. Tables and level
   grids measure against their actual 8pt cell text and 9pt line pitch. Source
   panels use the same available text width in measurement and drawing.

5. **Direct backend publication.** The standalone ReportLab backend previously
   reused a fixed `.tmp` path and replaced the destination before opening and
   validating its PDF. It now allocates a unique sibling temporary, reads and
   validates the staged PDF, captures its content hash/page evidence, and only
   then replaces the destination. Worker-thread use remains supported; it does
   not inherit the signal-based transaction's main-thread restriction. Its
   existing per-page progress timeout now requires finite, positive input.
   Concurrent direct writers retain complete-document, last-writer-wins
   semantics; transactional merging and power-loss durability are not claimed.

6. **Fallback font traits.** Missing bold-italic faces now retain both traits in
   Helvetica, Times and Courier fallbacks. Successfully loaded bundled fonts
   are unchanged.

## Regression evidence

All logs below are retained local evidence under ignored `tmp/`. They are not
bundled resources or guaranteed available from a GitHub checkout.

| Evidence | Result |
| --- | --- |
| `tmp/release-safety-python-red.log` | 14 failed, 14 passed: deadline, cleanup, fragment, final split and fallback regressions |
| `tmp/release-safety-length-red.log` | 6 failed, 4 passed, 19 deselected: both Length constructors reject nonfinite values; zero/tiny positives retained |
| `tmp/release-safety-dsl-red.log` | 7 failed, 37 deselected: actual-PDF instruction/token bounds, staged validation, unique temporaries and built-in fragment fit |
| `tmp/release-safety-python-first-green.log` | Initial 64-test focused pass before additional restoration/concurrency coverage |
| `tmp/release-safety-python-green.log` | Final focused pass: 98 tests, five third-party deprecation warnings, 10.33 seconds |

The final focused command selected these existing test files:

```text
tests/test_render_transaction.py
tests/test_document_dsl.py
tests/test_document_paginator.py
tests/test_fonts.py
tests/test_canvas_furniture.py
tests/test_renderer_contracts.py
tests/test_renderer_sharing.py
tests/test_cover_fonts.py
```

Additional passing cases cover every attempted rollback step when restoration
itself fails, cancellation identity, unsuppressed directory-fsync failure,
overlapping worker-thread publication, complete token preservation, explicit
paragraph breaks and rejection of an unfit glyph. Signal rollback tests use
mocked state and do not change another running application's signal handlers.
Affected-file Ruff checks, formatting and `git diff --check` passed.

## Layout compatibility and intentional differences

The retained short-layout comparison uses six components: InstructionBlock,
QuestionBlock, SourcePanel, Table, LevelTable and AnswerSpace. Its one-page PDF
is byte-identical before and after these backend changes, with identical text
and 100dpi page pixels:

```text
tmp/release-safety-short-layout-parity/summary.json
Previous backend source SHA-256:
f997c298c2a178bf99c08018e92072428a128f05c2d1880d4012400d44593078
Both PDF SHA-256 values:
6055aa97b1a97304b7d76236b1a40d2efaf53c1d2ecf7f37978138fd7117bc17
```

This is a six-component regression sample, not universal raster equivalence.
Long instructions now wrap, long tokens break without losing characters,
explicit paragraph breaks are represented, and table/level-grid heights use
their actual drawn font metrics. These can intentionally change affected long
content's layout and page count. Invalid dimensions, fragments and impossible
glyph widths now fail rather than reaching drawing. Accidental terminal empty
pages disappear; deliberately declared blank pages remain. Missing bold-italic
fallbacks also intentionally change appearance. No historical French catalogue,
provider sampling, AI prompt, question bank, answer or mark policy was edited.

## Exact file snapshot

All files below were read completely, including the new helpers and expanded
tests. “Unchanged” means no additional actionable finding was identified within
this review, not a guarantee that a file has no possible defect.

| Path | Disposition | SHA-256 |
| --- | --- | --- |
| `Backend/Core/render_transaction.py` | Deadline and cleanup fixes | `d78662bf3fb09cfc42fe68827de0f827ac7ea8ead3c1541309def336603259da` |
| `Backend/Core/pdf_text.py` | Reviewed, unchanged | `40e982b1cda2415dc50c7b9c4bcee56a80590af378dcd893917c116637998b55` |
| `Backend/Core/pdf_accessibility.py` | Cleanup fix | `ca21a7bd7e82db9b000f4e5759a2edef8981b834368383b6ea59bd9d6b12625d` |
| `Backend/Core/reportlab_theme.py` | Reviewed, unchanged | `ec1cfb1ae97c7d955c0f9d2cf05634440c256c35adb78ff94ae20b6f10b028ec` |
| `Backend/Core/fonts/__init__.py` | Bold-italic fallback fix | `2fd91353a3fbc75c5d75f59a0ae549af5bb8c9768825195e9fcff563118cb532` |
| `Backend/Core/document_dsl/model.py` | Finite Length boundary | `ff809b146e150916d259823307630d274689ee76b0e0201e3da8c85ccca313ac` |
| `Backend/Core/document_dsl/paginator.py` | Split bounds and final-page fix | `a41c5f620fbcdf47c771cfe890d11d5a0aa258556b3cb426bcadf8b62a27f514` |
| `Backend/Core/document_dsl/reportlab_canvas.py` | Reviewed, unchanged | `3073737332cca2fdadeb54e3db73a9a7f75f52f8b216658abf06ba5024fbda48` |
| `Backend/Core/document_dsl/vector_components.py` | Reviewed, unchanged | `14fb7cb5c438db9198431810aef3299964a7a1da1d2e7a10b623007c80d720bc` |
| `Backend/Core/document_dsl/profiles.py` | Reviewed, unchanged | `e34906a1d87d6640d77b20cc8ead08871cb8dd80eebb00656c3b9e78232dc869` |
| `tools/pdf_process.py` | Reviewed, unchanged | `03e744b9a568541c91ffa7234950754210bdf5e41b1b8319bfa3aefc22790904` |
| `Backend/Core/overlay/layouts.py` | Reviewed, unchanged | `161f58a129acdd74a31255b79c85d46838953e2d8a4d872618155ecfef416943` |
| `Backend/Core/document_dsl/reportlab_flowables.py` | Reviewed, unchanged | `110a0065f9dc8bca72865420a28d54e459cc7003159ee561182d22e16a32cdfa` |
| `Backend/Core/document_dsl/components.py` | Shared measurement and splitter fixes | `3f30e65507166afa66e7c7385fbf5d5e06a66f3b997cc8fd1870b88b38daa7b0` |
| `Backend/Core/document_dsl/reportlab_backend.py` | Shared wrapping and staged validation | `f2fd714c616339b6cb170c2dd8fe94fdddeb59c1f8cadd43d6b29b7789983c35` |
| `tests/test_pdf_process.py` | Reviewed, unchanged | `f3536465138242f449c53530cd1dfc6153fb9ff100a50d1835ddab77b7d057c0` |
| `tests/test_renderer_contracts.py` | Reviewed, unchanged | `483ff9c2a330de63cbffa872d61a4695c5c55b1e6145aeddf090883f974bae0f` |
| `tests/test_canvas_furniture.py` | Reviewed, unchanged | `232c4713510da0f35ccdd988f897c9cfc4eb97ace6354af46d51f9c16f5a5175` |
| `Backend/Core/temporary_cleanup.py` | New shared exception-cleanup helper | `2b5a020106471d1c547b3330dcba0573e8bce2d055adbb009791767b27a92a48` |
| `Backend/Core/document_dsl/text_layout.py` | New shared font-metric wrapping helper | `dd9b835a29746b53973668705693498782dfc9249e20bcbb053898850c1ed9e1` |
| `tests/test_render_transaction.py` | Expanded transaction regressions | `e2a9410b1dd68a7aff97ac3a1dd6b31c6d486c4452df41d7bb3f228fbbdc93e2` |
| `tests/test_document_dsl.py` | Expanded geometry, drawing and publication regressions | `178a0d45d74bd7589d952ce3d5b3f99aa90ff8c409f7ad725d5bb0868298829a` |
| `tests/test_document_paginator.py` | Expanded fragment and blank-page regressions | `e209ded5d13c97c830ffb08e4ea32359ef9c94a8b685d15eab4f2bf35fb1d8a5` |
| `tests/test_fonts.py` | Expanded fallback regressions | `1480ef686bde1cbd4c7320ffaa75a42899f97adab44e5ef19405077ea81266f3` |

## Remaining gates and limits

- The final fixed-source whole Python suite, native tests, signed builds and
  protected CI have not been certified by this focused 98-test result.
- Core-byte identity changes require new current-source and rebuilt-helper
  French acceptance. Retained earlier French runs keep their original
  identities and are not relabelled as acceptance of this snapshot.
- Page-level PDF structure tags do not establish correct semantic reading
  order, image alternatives, PDF/UA compliance or comprehensive accessibility.
- No teacher review, observed learner timing, full-HIG certification or Store
  approval is supplied by this implementation review.
- The separate retained native Qwen numerical review passed 55 independent
  Decimal checks, but concerns the earlier installed helper and is not a test
  of this changed source. Its own scope and limits are in ignored
  `tmp/mlx-final-acceptance-20261029/native-qwen-review/independent-arithmetic.json`.
