# Output integrity and Accounting Paper 2 flow

Internal engineering evidence, 2 November 2026. This records the bounded changes integrated at `449fb335`: French local transport, Accounting Paper 2 scheme presentation and exported UK layout-preview notices. It is not a full-file audit of the partially changed Accounting, rendering or validation files, and does not qualify model-authored papers.

## Accounting Paper 2

The current-source scheme still forced twelve technical verification pages after its answers. It printed internal `source_data` and `verified_answers` fields, including raw intermediate floats, and repeated front-matter boilerplate. Paper 1's existing compact policy did not repair this Paper 2 path.

The public builder now declares `accounting_marking_policy="generated-aqa-accounting-paper2-human-scheme-v1"` on every Paper 2 question. The new policy prints one original general guide, question-owned credit and workings, alternatives, allowances, exclusions, ignored responses, dependencies and one applicable levels grid per item. Its tables use 11-point text with 14-point leading. Private package evidence and precision requirements remain intact. There is no target page count or twelve-entry appendix requirement.

The validator binds the policy to Paper 2's question order, identifiers, tariffs, assessment objectives, section budgets and matching exported items. It checks ordered printed rows and bands, cover and guide presence, and ownership of subsequent pages. Unknown, partial, mixed or misplaced policy declarations refuse. A forged points-mode flag cannot remove a required levels grid.

Independent review found that a positive credit whose text was exactly `Levels-based marking` could be silently suppressed by the shared row helper, then accepted by the same helper in validation. The follow-up refuses a positive award on that reserved heading. It also independently totals actual PDF award-column cells against each authoritative question tariff; a test deliberately breaks both shared rendering and expected-row generation to prove that this independent check catches the lost mark.

Unmarked historical Paper 2 packages retain their legacy rendering and exact 28-page requirement. Paper 1's policy is unchanged. Across seeds 270100 and 270101, all Paper 1 PDFs, Paper 2 question papers and unmarked legacy Paper 2 schemes have exact full-page raster equality with the saved pre-change baselines. Complete blueprints are identical after removing only the new Paper 2 policy field. Original files and raw hashes are retained, not normalised or rewritten.

The adapter identity advances to `ai-assessment-v13-accounting-paper2-human-scheme`. Blind-solver inputs remain exactly unchanged. Writer, reviewer and difficulty payloads gain the private policy version, including an otherwise-empty context wrapper for context-free items; their question facts, answers, marks and instructions do not change. This is not a claim that all prompt bytes are unchanged. Historical checkpoints are not relabelled to the new identity.

The local [June 2025 official Paper 2 scheme](https://cdn.sanity.io/files/p28bar15/green/f8d36453601b3539fcee8721d79accbcd2467c97.pdf), listed on [AQA's assessment-resources page](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/assessment-resources), was used for comparison. Its pages 2–7 contain distinct substantive guidance, and pages 8–28 contain answers, workings, alternatives and evaluation rather than technical-record padding. No official wording or PDF is bundled by this repair. [AQA's assessment specification](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/specification-at-a-glance) remains the component-scope reference; this layout change does not establish equivalent difficulty or coverage.

## Exported layout previews

The `uk-layout-preview-v1` presentation replaces existing cover subtitles with `LAYOUT PREVIEW · Unreviewed sample content · Unofficial`, including source and supporting PDFs. Presentation is scoped around rendering, not model data. Nested and failed contexts reset; a live-render scope explicitly disables an outer preview scope. Live subtitle and font behaviour are unchanged.

Notice checks run inside atomic renderers before replacement, and again after conformance before final hashes, manifest writing and public publication. Missing, duplicate, clipped, too-small, hidden or white notices refuse.

Independent synthetic-PDF review reproduced a false pass when later opaque artwork completely covered searchable notice text. A second reproduction hid only a word or character. The repaired predicate checks non-space glyph bounds within the matched notice, retaining source-header prefixes outside that match. Earlier opaque backgrounds and later transparent controls remain accepted. The shared contrast predicate was factored without changing its existing ordering, opacity or bounds behaviour. This is a bounded later-opaque-vector-fill check, not general visual or accessibility certification.

## French local transport

Default French Ollama inference now uses the same proxy-free, redirect-refusing transport as French metadata admission. Injected transports, UK legacy routing, hosted transports, payloads, timeouts and physical-attempt limits are preserved. Fake-opener tests cover the repaired boundary without network or inference. The separate [provider boundary review](provider-boundary-file-review-2026-11-02.md) records that review's exact scope; no full-file attestation is extended from it to the other changes here.

## Recorded checks and remaining gates

- Accounting author regressions first reproduced the padding and policy gaps, then missing-cover/unowned-page, forged-mode and lost-positive-award cases. The final focused Accounting/layout group passed 309 tests, including the prior 307. Independent preview review passed 32 small draw-order, notice, context-reset and existing-contrast checks.
- The integrated focused group passed 424 tests. Ruff, the 608-file format check and the configured four-file mypy gate passed. The new policy helper also type-checks; separate checks of older Core files retained reproduced baseline errors, not a clean whole-Core type result.
- The combined preview geometry run passed 21 component cases, with 38 tests deselected, in 20.16 seconds. It measured 49 preview PDFs containing 1,061 pages. First-page notice checks passed; default/preview body words, geometry and rasters were compared. Retained pairs: `tmp/nov2-output-integrity-all-preview-fixtures`; raw hashes, page counts and notice results: `tmp/nov2-output-integrity-all-preview-summary.json`. This was not manual inspection of all 1,061 pages.
- An actual source `bridge.py generate --dry-run` Accounting Paper 2 run at seed 270100 published a 36-page question paper and 12-page scheme. The main reviewer personally viewed all 24 scheme pages across that integrated run and the seed-270101 author fixture, finding no clipping or new overlap. Page 10 remains sparse but contains a unique levels-grid continuation. Grids may span pages, and Section C still starts on a fresh page.

These are offline source, publication and visual checks. The separate public CLI run published its first 14 components, then refused OCR Computer Science Paper 2 at seed 270100 for cross-paper duplication at item `9(b)@sections.8.options.0.questions.1`. That refusal is retained, not counted as a successful export; the remaining components and the cause of the duplicate need separate assessment. Family-adapter geometry success does not establish complete public-entrypoint success.

No new-head full-suite, native, release-build or protected-CI pass is claimed here. Fresh model-authored Accounting Paper 2 review, teacher review, observed timing and marking calibration remain separate acceptance work. No model calls, official endorsement, Store approval or zero-defect claim follows from these results.
