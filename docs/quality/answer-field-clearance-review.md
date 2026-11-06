# Answer-field clearance review

## Reproduced fault

An owned Computer Science Paper 1 blueprint passed structural validation after
an ordinary question was extended to 35 wrapped lines (2,872 characters).
Its electronic answer document still had 40 pages, but the first answer field
covered seven question-text spans and the mark label. The existing release
validator accepted it. This was a constructed stress case, not a claim about
the default blueprint or a live model's output. Root inspected the rendered
page, including the field appearance.

The retained reproduction is `tmp/pdfs/ead-response-flow-dqazeoam`, with PDF
SHA-256 `1c48665925fe1138af36cd75b4dbd1f14eb8904d81debd6a61c41a3a4188d089`.

## Release check

The release validator now checks form-widget geometry and its clearance from
printed page text. Widgets are not included in the existing annotation or
page-drawing checks. Printed text is extracted from a display list without
annotations, so a candidate's entered answer is not mistaken for question
text. Display-list coordinates are derotated before comparison with the
widget and visible page bounds. Validation does not fill, flatten or rewrite
the document.

Fields must have finite, positive geometry inside the visible page, allowing
0.01 point for extraction noise. An intersection exceeding half a point in
both dimensions refuses publication. The allowance avoids treating a font
bounding box touching a field border as covered content. This geometric test
does not establish the educational quality or completeness of the question.

The first focused run reproduced eleven failures against the previous code.
Passing controls covered empty and filled fields. The final focused matrix
adds crop-offset and right-angle rotation cases, including covered text under
a filled field, all four outside edges, and boundary-touching controls. The
35 new tests and 97 existing PDF validation/image-geometry tests passed.
Every fixture comparison checks that validation leaves its bytes unchanged.
The retained 35-line reproduction is now rejected for covered question text.

A separate reviewer read the complete repair delta, its call site and all new
tests, and requested the additional cropped-and-rotated overlap controls.
Those controls passed. This extends the earlier full-file baseline review;
it is not a new claim that every unchanged dependency was reviewed through EOF.
Combined renderer, frozen-runtime, full-suite and protected release acceptance
are separate gates, not implied by these focused results.
