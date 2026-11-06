# Computer Science answer document continuation review

The Electronic Answer Document previously drew every prompt on one page, then placed a response field with a minimum height of 280 points. A structurally valid owned long prompt extended into that field. Its white appearance covered prompt text and the mark label. This was a renderer admission fault, not evidence that a default paper or live model output had produced the same problem.

The renderer now plans every part before opening the canvas. It measures text at the existing 9.5-point font and 480-point width while retaining the previous 88-character word-wrap ceiling. A word that cannot fit physically is refused; ordinary long prose continues onto numbered pages without truncation, smaller type or changed marks. A long narrow word that fits is still accepted.

Prompt-only pages stay above the footer. The last page reserves the original response area and a clear gap below the mark label. If the last prompt chunk cannot share that space, one response-only continuation page is added. Each part retains one mark label, one canonical multiline field and a question heading on every continuation. Short parts keep their existing draw order and field geometry.

## Evidence

Three initial regression cases failed: the 35-line and 85-line prompts overlapped their fields, and an unrenderable word reached the canvas before admission. The final focused suite passed 21 tests, including existing Paper 1 checks. New controls verify complete source order, widget clearance from printed text, continuation labels, capacity boundaries, unique field/tree references, nonempty appearances, multiline flags, unchanged source data and successful or refused atomic replacement. The receipt is `tmp/nov6-ead-flow-focused.xml`.

Four built-in contexts, MatchRecord, LoanRecord, Observation and SiteReading, were rendered with the exact old source and the repaired source. All 160 full-page rasters and extracted page texts matched, with 40 pages per context. Owned stress documents have 41 and 42 pages respectively. All five new first-part pages were freshly viewed after Poppler rendering; the prompt, footer, continuation label, mark and response field remain separate. Both stress documents also passed the root's current generic PDF release validator, loaded as an explicitly identified source snapshot rather than a packaged-build claim.

Hashes, baseline comparisons and stress outputs are retained in `tmp/pdfs/ead-flow-fixed-6j3z4m6p/report.json`. The repair does not change other supporting files, authoring prompts, answer keys or tariffs.

| File | SHA-256 |
| --- | --- |
| `Resources/computer-science/aqa/generator/cspapergen/paper1_assets.py` | `c3fa0c867fd848b1bd2c97585a525ebabb638bfae1322c7aae6151024f498dc6` |
| `tests/test_cs1_answer_response_flow.py` | `ec3fef237a89e1dfd02252255959329a4da16f41b56ea59342159e650284c3d9` |

Ruff checking and formatting passed for both changed Python files. The configured type gate passed its four existing infrastructure files, not a new static-type certification of this renderer. These are owned source-fidelity and form-layout checks, not live question quality, learner calibration, official-paper equivalence or a release-build qualification.
