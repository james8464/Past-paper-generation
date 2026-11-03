# Visually empty PDF page review

The release validator counted extracted text and graphics even when later opaque artwork hid the entire page. An owned temporary fixture contained 46 extractable characters but rendered completely white. Validation accepted it. This demonstrates a validation gap; no actual generated-paper corruption was observed.

Non-intentional pages now receive a bounded RGB render. A page whose rendered pixels are all identical is refused. Native 72 dpi is retained on ordinary A4 pages; larger pages are scaled to a longest side of 1024 pixels. RGB preserves meaningful colour variation that a grayscale comparison could discard. Any sampled pixel variation counts, without a contrast threshold. The existing intentional-blank contract now also requires its contracted page to be the actual final leaf, as its original comment specifies.

## Evidence

Five owned negatives failed against the unchanged validator: covered text, invisible text, off-white solid paths, solid-colour paths and a uniform white image. Six controls passed. A separate 37-page fixture reproduced the incorrect exemption of blank page 36 when page 37 contained visible work. That test failed while the exact 36-page final-blank positive passed. Logs are `tmp/nov3-pdf-visible-empty-red.log` and `tmp/nov3-pdf-interior-blank-red.log` in the INTEGRITY checkout.

After both repairs, 32 focused tests passed with one existing reading-order/tagging test deselected, in 1.20 seconds. Ruff and diff checks passed. The existing image-only positive had used a uniformly white image; it now has a visible black graphic, with a separate uniform-image negative. Other controls preserve faint lines, vector-only pages, meaningful colour images and superseded template text hidden beneath visible replacement content. No new accessibility testing was performed. Final focused evidence is `tmp/nov3-pdf-visible-empty-boundary-green.log`.

The output sample budget is at most 1025 by 1025 RGB pixels, or 3,151,875 bytes per page, processed sequentially. This does not bound decoder allocations or rendering time. One measured pass opened and checked the existing 67-page frozen Edexcel preview in 1.1898 seconds, with no uniform pages. Original PDFs and identities were unchanged. The six owned negative PDFs, hashes and private handoff remain under `tmp/nov3-pdf-visible-empty-fixtures/` and `tmp/nov3-pdf-visible-empty-qa.md`.

## File review and limits

The author read the entire 922-line baseline validator and 352-line baseline test file through EOF, then reviewed every final source and test change. The 74-line print-profile and 107-line cover-font tests were also read completely; selectively traced callers are not attested as complete-file reviews. Root and another internal agent independently reviewed the repair. Full-suite, native and latest-head protected checks remain required before release.

| File | Final lines | SHA-256 |
| --- | ---: | --- |
| `Backend/Core/pdf_validation.py` | 937 | `b5c5a0f445b75a8a461ff5f00b9af04b9f99b4b5e847cb201683051ecb01313a` |
| `tests/test_pdf_validation.py` | 482 | `d3d57ba2f016ddbb3a2e8b697c7cbbbc59691054bcb78ef1adc3d3d7e97664a6` |

PyMuPDF documents [`Pixmap.is_unicolor`](https://pymupdf.readthedocs.io/en/latest/pixmap.html#Pixmap.is_unicolor) as checking whether all pixels are identical in any colour space. The guard detects uniform rendered pages, not every hidden paragraph, missing answer, irrelevant graphic or semantic error. A page with only furniture or noise may still be nonuniform. Tiny details lost at the capped resolution are outside this check's guarantee. This review does not qualify generated papers or complete the repository audit.
