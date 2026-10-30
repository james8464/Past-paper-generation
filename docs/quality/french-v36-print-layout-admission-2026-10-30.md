# French V36 code-layout admission

Internal engineering review, 30 October 2026. No new live paper qualification is claimed.

## Reproduced failure

The retained Pro10 DeepSeek V4 Pro trial completed all nine authoring, blind-solve and review calls on unchanged source. PDF publication then refused an overwide code line. The atomic output path published no partial paper. Independent textual review found no definite concrete calculation, SQL or Python-answer error, but recorded precision, depth and whole-paper variety limitations.

At the existing readable 12-point monospace size, the first subject failure was exercise 3, question 3, code line 20: 468.076 points against 429.276 available. Two correction lines also exceeded their 459.276-point limit. Enlarged print uses 16-point code and had ten overflowing lines across the three exercises. The original responses remain unchanged under `tmp/french-v36-live-20261030/deepseek-pro-run-10-typed-advisories`.

## Repair boundary

The shared layout helper owns the existing A4 margins, frame offsets, monospace font and normal/enlarged sizes. Rendering still refuses the same overwide source; it does not rewrite code, shrink type or widen the page. The extracted fence pattern and line measurement are shared with prospective author admission.

New V36 author requests describe the actual requested print mode and conservative character targets. Exact font measurement is authoritative. Admission checks context, question and answer listings before blind solving or review. An overwide listing uses the existing single recorded whole-exercise structural regeneration. The app does not edit the answer or silently retry a semantic failure.

New packages bind `fr-nsi-v36-code-layout-v1` and a strict Boolean `large_print` to their identity. Stored revalidation checks the bound mode. Legacy packages without either field retain their original reading rules, with no inferred enlarged-print compatibility. New runtime publication requires both fields and a match with the captured request.

ReportLab retains literal tabs, while the existing PDF content validator expects eight-space tab expansion. Historical rendering is unchanged. New mode-bound author admission refuses tabs and requests spaces rather than rewriting indentation.

## Review and tests

The parent read the complete new 64-line helper and all source/test changes. The pipeline/runtime baseline full-file reviews and subsequent diffs are recorded in `hosted-and-french-full-file-review-2026-10-30.md` and `french-question-advisory-review-2026-10-30.md`. This follow-up reviews their complete layout diffs. The rendering diff was reviewed, but this record does not attest a complete-file rendering audit.

| Source | Reviewed SHA-256 |
| --- | --- |
| `Backend/Core/france/code_layout.py` | `7d7136e22014f189ab448be76e3eb642dfb23d7d8179154fd87ebb51079b12dd` |
| `Backend/Core/france/llm_pipeline.py` | `a9b43141df5d61cebc603db015bff7f6595ebc3ebfc9286d9e3cb97fd503d210` |
| `Backend/Core/france/llm_runtime.py` | `da544b85b6f52573a834e54109a2ae3ae28516e106b7f1df03b1eded811c5793` |
| Rendering diff only | `ca35a6d5ad51f71ce678028ffc1b16c11f4f7ffff2f5bee7e66aaf3f4c8ad3e1` |

The agent's scoped suite passed 271 tests, including historical pipelines, real normal/enlarged PDF publication, strict mode metadata, security-priority failures and the single-regeneration limit. Root integration passed 124 targeted tests. Full integrated regression, protected CI and a fresh live paper remain separate gates.

Retained-response admission accepts the first two exercises in normal mode and refuses their enlarged variants; exercise 3 refuses both modes. Four admitted single-exercise normal diagnostic PDFs were inspected across all 21 pages with A4 and exact code/indentation checks. Their shared three-exercise cover does not match their diagnostic-only contents, so they are not distributable papers or full-paper acceptance evidence. Earlier failed diagnostic attempts are retained separately. None is described as a fresh model generation.
