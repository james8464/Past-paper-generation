# Computer Science table source fidelity

The table renderer and the candidate-visible review projection both shortened
table values to 34 characters. A developer-owned long finite-state-machine
header lost its final qualifier in both representations, so comparing the two
could miss the loss. A fresh built-in support table also contained a 44-character
validation instruction that was cropped. This does not show that a model can
inject arbitrary table headers through the current authoring route.

The projection now retains the complete source. The renderer measures each cell
at its existing 8-point font, wraps ordinary prose between words and reserves
the complete row and table height before drawing. Existing single-line cells
keep their 20-point row geometry. Unsupported spacing, oversized words, missing
headers, extra cells and tables that cannot fit safely are refused, not shortened.
Finite-state-machine placement also reserves its diagram space.

The AQA Computer Science review digest includes a visible-source policy, and its
adapter moves to version 16. Reviews made against the cropped projection cannot
silently count as reviews of the complete source. Historical records are not
rewritten. No question, answer, mark allocation or model prompt was repaired.
OCR uses a separate renderer and is outside this change.

Before the repair, 12 owned regression cases failed and the original-geometry
control passed. The author's final focused run passed 435 tests with two skips.
Across four scenario contexts, 168 of 172 question/correction pages were
pixel-identical at 72 dpi. Only question page 17 changed in each context,
restoring the complete support-table instruction; page counts were unchanged.
The long-header control pages and one restored support page were rendered and
viewed. The other three changed support pages received raster/text comparison,
not a fresh visual-review claim.

Independent review covered the exact four-file change, all table callers and
review/checkpoint identity. The 289-line authoring file and 181-line new test
file received complete source review. The large renderer received a bounded
delta/caller review against its previously reviewed baseline, not a new whole-file
audit. These are offline source-fidelity controls, not live-model qualification,
calibrated difficulty, student timing or official-paper equivalence.
