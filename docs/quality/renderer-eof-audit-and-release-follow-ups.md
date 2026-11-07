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
