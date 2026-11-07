# Source-bound overlay market geometry

## Bounded review and defects

The read-only main192 review read all four remaining non-French Backend modules:
overlay `graphs.py` (894 lines), `humanities.py` (134), `science.py` (253), and
`solver_prompts.py` (120). Five directly related tests were read through EOF;
additional caller/test reads were scoped, not complete dependency audits.
The source-pinned receipt is retained under the audit owner's ignored
`tmp/nov7-overlay-solver-eof-review.json`.

The active Edexcel economics PDF dispatcher calls the affected graph helpers.
Two model-independent inconsistencies were established:

- Positive externality rendering labelled the private-cost curve as MSB and
  omitted the actual MSB curve. Its generic public `externality` kind silently
  selected the positive branch. Negative-externality welfare shading omitted
  the private-output benefit vertex, producing a near-degenerate polygon.
- Consumer/producer surplus shading treated a quantity as an array index. Its
  default equilibrium marker was not on the drawn curves, and the helper did
  not consume the public `eq_price`/`eq_quantity` parameter names.

No new active release defect was established in humanities or solver prompts.
The unadvertised science ray helper retains a fixed-image-height limitation;
no production caller was found in the scoped repository search. It is unchanged.

## Narrow repair

Only the two affected drawing functions change. Externality curves, exact affine
intersections, equilibrium markers, and nondegenerate welfare triangles now use
the same coefficients. Generic externality aliases preserve the negative default;
explicit positive/negative variants remain supported; unknown kinds refuse.

Surplus curves intersect at the declared positive finite price and quantity.
The exact quantity is included in the sampling grid and bounds both welfare
fills. Existing shared scale checks reject invalid or unrepresentable inputs
before axes are created. Direct `price`/`quantity` keywords and historical
dictionary aliases remain supported; equal public/legacy aliases agree and
conflicting aliases refuse. Other graph parsers are unchanged.

Both legends use the normal figure margin rather than crossing plotted curves.
Surplus equilibrium annotations use plain ASCII Pe/Qe with point offsets.
No prompt, model answer, mark allocation, source prose, or solver policy changes.
These are illustrative market geometries, not calibration or official equivalence.

## Evidence and limits

Before production edits, the two new test files produced **30 failures / 1 pass**
in 0.68 seconds. An earlier externality-only RED was 7 failures / 1 pass; the
combined RED corrected a nested assertion's diagnostic representation without
changing its geometric requirement. Draw captures exercise the actual public
dispatcher, both externality signs, generic aliases, both surplus kinds, default
and non-default parameters, bounds, source-input immutability, areas, and refusal
controls. Compatibility and annotation checks were added during refinement.

The first six-page model-free PDF preview exposed inherited legend/curve overlap;
it was retained, not accepted. Three focused legend regressions then failed.
The revised export was rendered with Poppler and all six pages inspected:
negative, positive, generic externality; default surplus; P80/Q120; P20/Q300.
No overlap, missing labels, or clipping was found in that bounded preview.
This is the real public drawing route in a synthetic canvas, not a whole paper.

Final focused gate: **162 passed in 1.60 seconds**, with five inherited SWIG
deprecation warnings. Scope: the two new geometry files, existing macro and
labour geometry files, and Edexcel stimulus-diagram tests. No full suite, build,
model calls, network requests, GUI, native interaction, or live-paper qualification
was performed. Ignored logs and PDFs remain under the implementation worktree's
`tmp/nov7-overlay-*` and `tmp/pdfs/nov7-overlay-geometry/` paths.
