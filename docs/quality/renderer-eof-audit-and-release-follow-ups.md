# Renderer audit and release follow-ups

This audit covered selected active rendering and source files. It is not a
claim that every repository file, generated paper or model has been qualified.
The implementation coverage register retains the remaining work.

## Files read

The Accounting audit read the complete renderer (2,779 lines), case-data module
(1,354), configuration (276) and syllabus loader (38). It found no new high- or
medium-priority release defect in that scope. Dependency inspection was scoped;
it was not a second whole-file audit of every caller.

The Computer Science audit read the complete AQA renderer (2,266 lines) and the
prior OCR renderer (1,261). The OCR repair then received complete-delta review
and independent review of its new tests. The current OCR file has 1,267 lines.

The Edexcel audit read the complete prior renderer (4,200 lines), models (154)
and paper configuration (294). The source-booklet repair received complete-delta
review and independent review of its new tests. The current renderer has 4,212
lines. Review of the Business cover fix combines its previously recorded
renderer baseline and repairs with the complete new cover-selection delta;
it is not a fresh full read of the 1,665-line current Business renderer.

A further complete AQA Economics read covered its generator, renderer,
configuration, level policy, written tasks, syllabus loader and CLI: 4,043
baseline lines. The OCR Economics read covered its generator, renderer,
configuration, syllabus loader and CLI: 3,766 baseline lines. AQA Computer
Science generation, question-bank and model files added 4,989 complete lines;
no demonstrated current-path release defect was found in that latter scope.
The Economics repairs below received complete-delta and independent review.
Those reviews do not claim a second whole-file read after each repair.

## Findings and repairs

### Keep rendering separate from reviewed source data

OCR Computer Science Paper 2 changed the first option's title while rendering.
The title belongs to the parent-source projection used by difficulty evidence.
The family adapter renders before exporting the public assessment package, so
the display-only change could invalidate the evidence created during review.
Layout previews do not require that evidence and did not expose the problem.

The renderer now passes a local display-title override to the page-group helper.
It does not modify the question model. An owned reproduction produced two
failures and one passing heading control before repair. The final scoped group
passed 169 tests. All 32 pages retained their full extracted text and 100 dpi
RGB rasters. Existing display and continuation headings are unchanged.

### Share the source projection used by the question paper

The published Edexcel Paper 3 companion booklet selected a generic subset of
questions and restarted extract letters in each section. That disagreed with
the primary paper's B, D, E and F references and omitted or misattributed source
material and figures. The primary paper's inline sources were already correct.

Paper 3 now reuses the existing canonical inline-source renderer. It includes
all six extract owners and Figures 1 to 3 without a second mapping of their
content. Paper 1 and Paper 2 retain their existing paths. The owned source tests
produced 15 failures and one passing control before repair. The final targeted
group passed 130 tests, with four unrelated tests deselected. Public dry-run
publication and unchanged blueprint data are part of that scope.

### Derive instructions from the selection rules

Business Paper 2 and Paper 3 require every question, but their covers used
generic instructions about Sections A and B and optional sections. The cover
now says “Answer all questions.” when every section requires all its options.
Paper 1 retains its existing compulsory and optional-section instructions.

The owned reproduction produced five failures and two passing controls. The
final targeted group passed 135 tests. Tests preserve the complete blueprint,
all non-instruction profile fields, every post-cover page's word coordinates
and raster, and the entire Paper 1 cover. This is a presentation repair, not a
change to selection, marks, source material or difficulty.

## Implementation guidance

### Use source facts in numeric answers, diagrams and marking tables

The Economics reads found further renderer and source discrepancies:

- AQA seed 72 Paper 1 printed 26.2% for public endpoints 88 and 111.1, where
  the existing half-up contract requires 26.3%. OCR seed 15 Paper 1 printed
  -1.2% for 88.0 and 86.9, where that contract requires -1.3%. Both generators
  now calculate from decimal representations of the public endpoints and use
  the existing numeric-output display policy. Acceptance tolerances and source
  series are unchanged. The OCR witness came from a bounded scan of 384 owned
  papers, not a model run.
- AQA negative-production-externality quantity guides missed the intersections
  of the actual drawn curves. The guides now derive their positions from those
  line segments rather than separate hand-tuned coordinates.
- OCR appended a generic grading scale to already-authored levels, including
  a second scale that stopped at 12 on a 15-mark question. The renderer now
  retains the question's authoritative statements without adding another scale.
- OCR's printed AO grid guessed allocations from tariffs. It now uses each
  question's validated assessment-objective allocation, including the sum of
  actual allocations in grouped multiple-choice rows. Missing or invalid
  allocations are refused, not replaced with guesses.
- OCR Paper 3 cover instructions implied optional answers and a nonexistent
  Section C. They now follow the actual all-required selection topology.
- OCR's Paper 3 figure claimed “2019 = 100” despite raw initial readings that
  were not 100. The unsupported base-year claim was removed; source readings,
  questions and answers were not renormalized.

Removing the duplicate OCR bands exposed a spacer-only physical page before
the appendix. Only that final spacer is removed before the forced break. No
assessed table is dropped and no finished PDF page is deleted or padded.

The AQA repair's focused group passed 390 tests. OCR's final public/source group
passed 97. Both had genuine failing owned reproductions before their repairs
and independent source/test review afterward. These results are distinct from
the final combined release suite. A preliminary combined renderer run was
stopped after 3,924 passing tests to include these completed audit findings;
its interrupted result is not acceptance evidence.

### Maintenance rules

These repairs follow three rules that apply beyond the affected papers:

1. Rendering may project display text, but must not mutate identity-bearing
   source data or invalidate completed review evidence.
2. Companion documents should reuse the canonical source projection rather
   than maintain a second extract-to-question map.
3. Candidate instructions should follow the paper's selection metadata rather
   than a generic cover string copied between paper types.

Large rendering modules remain candidates for a later, separately tested split
by document role. That refactor should preserve source identities and pixel
baselines. Renaming variables or rewriting comments across those modules is not
a substitute for these checks and is not required for this release repair.

## Limits

All reproductions and targeted tests used owned deterministic material. No
model, paid service, learner timing or new teacher review was used. Static
call-path evidence is distinguished from executed tests. Source/raster parity
does not establish official-paper equivalence or the quality of an arbitrary
model's answers. French and provider live-paper qualification remain separate.
Final combined regression, signed builds, actual frozen previews, native
acceptance and protected checks are separate release gates.
