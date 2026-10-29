# Accounting V11 retained-attempt review

## Original live result

The pinned Accounting AQA Paper 1 attempt used seed 270100 and `gemma4:12b`,
digest `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c`.
It failed after 3,758.18 seconds with exit code 1 and the terminal error
`Accounting scheme omits choice credit for 05`. All 21 accepted items remain in
the checkpoint. The transaction did not publish its final PDFs or package.
That attempt remains failed; reconstructed files must not be attributed to it
as surviving original outputs.

Retained root: `tmp/final-v11-accounting-live-20261028`.
Original checkpoint SHA-256:
`69622502978442ad6480e6f98e97c8f9ac2f8f2cf753c68b05d8decd43469c85`.

## Reproduction and repair

A separately labelled offline replay copied the checkpoint and resumed all 21
accepted items with a client that refuses model calls. It made zero requests.
The question paper has 36 pages and its scheme has 24. The reviewer rendered
and inspected all 60 pages in fifteen four-page grids, alongside extracted text
and printed tables. No clipping, missing glyph, missing row, overlap or answer
border overflow was found in this reconstruction. Some scheme pages are sparse.

The exact ten-row answer-table check passed. A later containment check required
the raw Q05 answer's terminal full stop, although the canonical printed answer
policy intentionally removes that stop. The printed row was present:
`5 | Option B: It increases the gearing of the business | 1`.

Commit `1ff0011a` uses the same canonical printed-choice function in that later
check. It preserves the exact table validation and keyed option letter. The
real-PDF regression failed before the fix. Punctuated and unpunctuated valid
choices pass; changed letter, missing row, changed text and wrong award still
fail. The related 69 tests passed. The retained scheme then passed validation
for all 21 parts and 89 credit statements without another model call.

## Content and official comparison

The reviewer inspected the official June 2025 AQA Paper 1 question paper
(36 pages) and scheme (26 pages), as well as the reconstruction. Independent
Decimal calculations supplied 55 checks from public inputs. All ten multiple
choice questions have distinct choices and correct keys. Credit totals remain
120, split 30/40/50 across the sections.

The reconstructed partnership, sole-trader and plc tasks use the printed cases.
The previous generic-case, duplicated-choice, repeated-guidance and credit-budget
findings did not reproduce. Extended answers use the given figures and preserve
supported alternative conclusions. V11's supplied tax expense differs from the
official paper's movement-based derivation, so equal task demand is not claimed.
One template and seed do not establish syllabus coverage or timed difficulty.

Official question-paper SHA-256:
`7482ff23f5406f37e54d49bf76f8d2a1cd5bdd823a4face1f55ee7ece2c1cfa6`.
Official scheme SHA-256:
`75bb31088224c2e3e305e3dbd3d6c6efd9891e4f262314d855a4fd1aa1907dd3`.

## Evidence and acceptance limit

The detailed checklist, all arithmetic, renders and initial failed diagnostic
wrapper remain under
`tmp/accounting-v11-final-review-20261028/offline-replay-review`.
The initial wrapper omitted a required `reference_count` argument; the corrected
three-argument reproduction is separately recorded. It did not replace or lose
the artifacts.

| Artifact | SHA-256 |
| --- | --- |
| Detailed conclusion | `90844af45f8310e8dec46376992d67c9eb187eb240625102b3cbe4c9653f54c2` |
| Reconstructed question paper | `2ae5dcc07551aab53f55addf7f1d643840d3b1d8db7996a00f69c9040333068c` |
| Reconstructed scheme | `909fcda48096c0bcfb1c3ca110b31555e620adb031d5040b713c3787a14eda8c` |
| Reconstructed package | `cf710a9e3ba8ddc62a2a0c489d08251308015682892f327b8441f32db69cc748` |

This is offline review of retained accepted content, not a new live AI pass.
The Core repair changes implementation identities and needs final rebuilt
source/helper acceptance. The complete supported-paper matrix and MLX paper
acceptance remain separate. Teacher review and observed learner calibration are
`not_run`. No official PDF is bundled and no Store approval is claimed.
