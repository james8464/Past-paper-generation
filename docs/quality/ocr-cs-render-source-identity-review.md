# OCR question rendering preserves source identity

## Failure

The OCR Paper 2 question renderer changed its caller's first option title from
`Question 1` to `Section A · Question 1`. That title is part of the parent source
used to bind difficulty-review evidence. The shared adapter renders the PDFs
before exporting the same assessment object, so rendering could invalidate an
otherwise unchanged saved review at the publication boundary.

An owned offline Paper 2 fixture reproduced both effects. The complete blueprint
changed after rendering, and genuine pre-render evidence from a fake reviewer
was refused against the exported post-render candidate identity. Two tests
failed; a third confirmed that the intended printed heading was present. An
earlier test setup failure caused by a missing temporary parent directory was
retained separately and is not counted as defect evidence.

## Repair

The heading is now a local display value passed to the page-group renderer.
Continuation and answer-continuation headings use that value too. The option,
questions, public source data and saved review objects are not changed. Direct
page-group callers retain their previous default title behavior.

This does not change difficulty validation or accept stale evidence. It removes
the renderer's mutation of the evidence-bearing source. No model prompt,
question, answer, mark allocation, source fingerprint algorithm or checkpoint
version was changed.

## Checks and scope

The new tests and existing OCR renderer, Computer Science objectives and shared
source-projection groups passed 169 tests in 5.64 seconds, with five existing
Swig deprecation warnings. The final test-only formatting change wrapped one
set literal; Ruff, formatting and diff checks passed afterward.

All 32 pages of the owned before/after question papers have identical complete
text and identical full-page RGB rasters at 100 dpi. The corrected heading page
was also rendered with Poppler and visually inspected. Its heading, source,
question text, marks and response space were unchanged. This is preservation
evidence for this owned fixture, not a new full visual-quality qualification.

The preceding independent audit read both maintained Computer Science renderers
through EOF: the 2,266-line AQA renderer and 1,261-line OCR renderer. This repair
received complete-delta review plus the relevant shared adapter, candidate
identity, export and saved-evidence paths. Dependencies were not all reviewed
through EOF. The AQA renderer was not changed.

All work used generated temporary files and fake review responses. There was no
live model, network request, GUI interaction, native build or complete-suite run.
No historical user document was modified or retrospectively qualified. The final
combined release gates remain separate.
