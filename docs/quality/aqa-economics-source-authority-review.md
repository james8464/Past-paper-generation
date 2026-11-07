# AQA Economics source-authority repair

## Scope and retained evidence

The November 7 read-only audit covered all 4,043 lines through EOF in the seven
requested AQA Economics generator/renderer/configuration modules at
`eae9c151a633d159d985fc35faacd4ce7100c1d3`. Exact original hashes, read chunks,
dependency-span limits and the two findings are retained in ignored
`tmp/nov7-aqa-economics-eof-audit.json`. This is a bounded source audit, not a
whole-application or official-paper quality qualification.

A bounded offline search over Paper 1 seeds 0–72 found a real generated witness:
seed 72, context A1, activity values `[88, 99.4, 112.3, 113.4, 111.1]`. The exact
endpoint percentage is 26.25%. The original binary-float prose displayed 26.2%,
while the existing deterministic numeric contract correctly returned 26.3% using
Decimal and ROUND_HALF_UP. Reconciliation rejected the original scheme; this
was a generated-source defect, not a reason to relax numeric checks. A separate
four-legal-draw arithmetic witness `[80, 84, 79.8, 81.4, 80.6]` confirmed the same
0.7% versus 0.8% discrepancy without a model or renderer.

The expected negative-production-externality diagram independently hardcoded
quantity guides at relative x=145/183. The drawn MSB/MSC and MSB/MPC segments
intersect at x≈132.037/169.753, respectively. Thus Q* and Qm did not project the
diagram's own equilibria, although their ordering was correct.

## Small implementation

- Percentage prose now uses Decimal representations of the same public endpoints
  and the existing `NumericOutput`/`display` policy. Both calculation answers and
  Paper 3 indicative percentages share this projection. Source series, working,
  question prompts, tariffs, AO allocations and validation tolerances are unchanged.
  Negative displays use the numeric contract's canonical minus glyph.
- Externality guides and their quantity labels use intersections calculated from
  the same line-segment endpoint arrays used to draw MSB, MPC and MSC. A small
  local helper refuses parallel or non-intersecting segments; no extra dependency
  or hand-tuned coordinate offset is introduced. Other diagram branches are untouched.

This changes generated answer displays at rounding boundaries and the expected
diagram geometry, not examiner-credit rules or model-answer selection. Existing
saved PDFs/history are neither migrated nor deleted. No schema or prompt-version
change is needed: checkpoint identity already hashes the complete blueprint
(`assessment_checkpoints.identity_for_blueprint`), so changed answer text changes
the blueprint identity. The renderer fix is pure and does not alter that identity.

## Focused verification and limits

Genuine pre-fix RED: 4 failures, 8 passing controls in 0.23 seconds, covering the
seed-72 reconciliation mismatch, positive/negative half-boundaries and guide
geometry. An earlier missing-import collection error from nested pytest config
was setup failure, not RED evidence; the valid run explicitly selected root
`pytest.ini`. Initial post-fix GREEN: 12 passed in 0.23 seconds.

Final tests additionally cover the public exported seed-72 scheme, continued
rejection of stale 26.2% prose, positive/negative/zero/non-half display controls,
Paper 3 indicative content, the real generated expected-diagram path, source
immutability, parallel/disjoint refusal, and six unaffected diagram kinds.
The scoped existing AQA Economics and shared numeric tests passed 291 cases in
3.58 seconds; new tests plus selected-response dispatch passed 114 in 0.43 seconds.
Final combined gate is recorded separately in the implementation receipt.

All checks are offline, with no live model/provider call, network, GUI, native
build or full-suite run. Existing focused tests render their own temporary PDFs;
no additional manual PDF or raster review is claimed. Five existing SWIG
deprecation warnings were observed. Ruff check/format and diff whitespace checks
are required before freezing. Root owns final integration, Graphify and ledger.
