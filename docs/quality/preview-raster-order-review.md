# Preview notice raster order review

UK offline layout previews must disclose that their content is unreviewed. The earlier check could certify a notice that remained extractable as text but had been covered by a later image. The new check adds a conservative paint-order requirement before a preview can be published.

## Reproduction and repair

Two owned PDFs contained the same notice and body text, with a white raster painted either before or after the notice. Poppler rendering showed the notice in the first PDF. In the second, the notice crop was uniformly near-white while the body remained visible. Both PDFs passed the previous validator. The retained reproduction, render crops and paint-sequence evidence are under `tmp/pdfs/nov6-preview-raster-repro` in the release checkout. This was a constructed counterexample, not evidence that a delivered paper had this defect.

The repair uses [PyMuPDF's documented `get_bboxlog()` paint sequence and text-trace sequence numbers](https://pymupdf.readthedocs.io/en/latest/functions.html). If a later raster bounding box overlaps any nonspace notice glyph, the validator refuses certification because visibility cannot be verified. Existing text-size, colour, opacity, clipping and opaque-vector checks remain in place.

A transparent or masked image painted later is also refused. This is deliberately an ordering certificate, not an assertion that every overlapping image is opaque or hides the notice. Images painted before the notice and images outside its glyphs remain accepted. Relevant malformed or nonfinite geometry cannot receive a certificate. The 10,000-event limit bounds the validator's own analysis; it does not establish that PyMuPDF avoids allocating the display list before the limit is checked. No image decoding, OCR or whole-page rendering was added to production validation.

The certificate is now `uk-layout-preview-v2-raster-order`. Existing records bearing the earlier certificate are not rewritten or silently upgraded. This identifier is recorded with PDF presentation validation; no prompt, model or checkpoint policy changed.

## Checks

The initial run of the new ordering-policy tests had five failures and ten passing controls. The earlier validator accepted all five later overlaps: white, black, patterned, transparent and translucent images. The opaque white-cover reproduction establishes the existing visibility defect. Refusing transparent later overlaps is a deliberate conservative policy change, not evidence that their notice was hidden. The ten before-notice and outside-notice cases passed.

The final focused run passed 113 tests in 31.48 seconds across `test_preview_raster_order.py`, `test_uk_preview_presentation.py`, `test_ocr_preview_uniqueness.py` and `test_configured_family.py`. It includes the real image and mask fixtures, invalid relevant geometry, unknown sequence metadata, malformed events, the event limit and the new certificate. Existing public offline previews still pass, with their body geometry unchanged. Fixture checks also confirm that validation does not alter PDF bytes.

Ruff checking and formatting passed for the three changed source/test files. The configured type gate passed its four configured infrastructure files; it is not a type-check claim for the whole preview module. These were offline fixtures, not live model qualification or proof of paper difficulty.

## Reviewed source

`preview_presentation.py` was read through its final line 145 and the new raster-order test file through line 121. The existing UK preview test file was reviewed only for its changed two certificate literals and relevant caller context, not certified through EOF.

A subsequent independent review read all 145 source lines, all 121 new test lines and all 361 lines of the existing UK preview tests at the hashes below. It found no actionable issue within that scope. Caller inspection remained selective; this does not certify complete dependencies or a runtime release.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/preview_presentation.py` | `09ff7bdb901422ebf897b077f10084532bf8eb2cf44a46104d1362881eb24dd8` |
| `tests/test_preview_raster_order.py` | `15ead3648db05236926f92102754190c7f616e0ce284b0e2df520a9051602110` |
| `tests/test_uk_preview_presentation.py` | `d7a5efcd941992dfcf45389701e81d437dcdbaedcd94883d5c6c34fef5e08462` |

The preceding bounded audit also read unchanged `Backend/Core/paths.py` through line 27 and `Backend/Core/legacy_migration.py` through line 83. No concrete defect was found in those two files. Their hashes are respectively `5935a31d7cd1de7abce064ec8aadd806063111a055e4b1a535cecf244329685b` and `17e87141bcef2ce6c41adb1718394061a16fced53c14f984d404de7cf0440068`. Dependency and caller inspection was scoped to these checks, not a complete dependency or project audit.
