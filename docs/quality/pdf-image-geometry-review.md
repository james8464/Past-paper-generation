# PDF image geometry review

## Reproduced admission gap

An owned 200-by-200-point PDF contained a 600-by-600-pixel image placed at
`(-20, 50, 80, 150)`. The release validator accepted its 432 DPI resolution,
although the visible page cropped the left side of the figure. The first red
test reproduced this acceptance. The broader pre-repair matrix produced
27 failures and 20 passing controls. These fixtures identify a validator gap;
they do not establish that a current generated paper contains a cropped chart.

The repaired validator rejects nonfinite or nonpositive image geometry and
pixel dimensions before computing DPI. Non-background images must fit the
visible page, with a 0.01-point tolerance for numeric extraction noise.
Existing minimum image resolution, overlap, content and metadata checks remain.

## Coordinates and deliberate backgrounds

PyMuPDF returns extraction coordinates relative to the unrotated visible page.
`page.rect` alone reflects rotation. The repair uses
`page.rect * page.derotation_matrix` for image and text containment, occupancy
and print-evidence geometry. This also removes false refusals of valid text on
rotated rectangular pages. Offset CropBoxes are already reflected in extraction
coordinates; their offset must not be subtracted again.
[PyMuPDF Page documentation](https://pymupdf.readthedocs.io/en/latest/page.html).

The existing full-bleed exception remains: an image touching every page edge
and covering at least 90 percent of the page is treated as background artwork.
This heuristic does not prove that the image is decorative or that its contents
are complete. Full-page and deliberately oversized backgrounds remain accepted,
including on rotated pages with offset CropBoxes. They still undergo DPI checks.

## Evidence and compatibility

Print-evidence schema 2 still describes the same fields. For rotated pages,
`page_box`, mark positions and safe-print bounds now use the same unrotated
basis as extracted content. Normal portrait evidence is unchanged, including
offset-CropBox controls compared with the previous `page.rect` basis.

The fidelity auditor extracts both generated and reference print evidence
afresh on each run. Current publication calls the release validator before
writing its manifest. No cache of extracted print geometry was found in these
scoped callers. The existing `Backend.Core.pdf_validation:v2` manifest label
and old schema-2 reports are historical evidence, not proof that an earlier
PDF passed this stronger check. Revalidation is required for that claim.
No historical report or approval is relabelled by this repair.

The focused suite passed 119 tests. Controls include all right-angle rotations,
nonzero CropBoxes, image-only pages, boundary noise, outside edges, invalid
geometry, preserved backgrounds, portrait evidence equality and rotated
reference comparisons through the existing print-profile consumer. Validation
leaves fixture PDF bytes unchanged. Ruff and the repository's scoped type gate
passed; standalone typing of the broader PDF module remains outside that gate
and reports PyMuPDF stub/annotation limitations.

The author read the original 975-line file through EOF and reviewed the repair
delta. This is a bounded geometry review, not a whole-project audit, paper-quality
qualification or complete print-safety guarantee. Root reviewed four retained
Poppler PNGs. Their private validation JSON binds the exact source and unchanged
PDF hashes under `tmp/pdfs/pdf-image-geometry-review-sQ1vGr`.

A separate reviewer checked the complete repair delta, all new geometry tests
and the relevant extraction, containment, decorative-background and print-metric
helpers. No issue was found at the exact hashes below. That review did not read
every unchanged dependency through EOF or replace the final combined release
tests and packaged-runtime checks.

| File | SHA-256 |
| --- | --- |
| `Backend/Core/pdf_validation.py` | `806e89959831557ff5768120bd54ee8fc134db6204c0ebaf6527c7bcad925e0a` |
| `tests/test_pdf_image_geometry.py` | `eeb9d595f5f112800fbb2023f7b781410dce2207d646a43a9f692831aae2ada3` |
