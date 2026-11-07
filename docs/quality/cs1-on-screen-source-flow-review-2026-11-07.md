# AQA Computer Science Paper 1: source-owned on-screen flow

## Scope and evidence

This bounded, model-independent repair concerns newly rendered AQA Computer Science
Paper 1 question papers. It is not an official page-count, difficulty, duration or
content-quality equivalence claim. Ten pages in the reviewed seed is an observed
content-driven result, not a new target. No model, network, full-suite, build or
native acceptance was run for this repair.

The original renderer (2,266 lines, SHA-256
`cbcf23e8b35458822dded5f6999812fa94af0a5d7fa2814884d0c7618be1a1eb`)
was read to EOF in the preceding source audit; this review combines that reading
with the complete owned delta and scoped callers, not a fresh whole-file reading.
The new content verifier (374 lines), flow tests (188) and policy tests (267) were
read completely, with independent review of the maintained deltas. Graphify was
used for navigation; source and PDF evidence, not graph inventory, supports this note.

## Repair

The previous fixed 24-page orchestration introduced six blank pages, repeated code
and FSM material, two unrequested trace grids, and a generic timing scaffold that
did not describe the question's five trials. The question paper now flows the
authoritative blueprint in order, with section boundaries and measured overflow.
Only the obsolete Paper 1 private-helper call closure was removed. An on-screen-only
initial-block reservation keeps the question number with its first prompt and
initial declared material. Written Paper 2 follows its existing branch.

The generated-content policy is explicitly
`generated-aqa-cs-paper1-question-content-v1`. Its scope is only AQA Computer Science,
Paper 1, question paper, with a validated on-screen blueprint. The measured reference
remains 24 pages; measured geometry/assets and every other role's policy are unchanged.
The owned registry builder updates only this policy entry. Unknown policy kinds and
incorrect subject/family/paper/role combinations fail closed.

The verifier independently projects declared question/part ownership, prompts,
options, marks, code and material tables from the full matching package. It checks
ordered 12-question/100-mark completeness, duplicate/missing content, A4 geometry,
bounded resources, nonempty body pages and absence of invented padding. It does not
canonically rerender in production. FSM checks establish source text/table and node
circle counts, not exact arrow geometry, state-label binding or graphical equivalence.

No model schema or blueprint layout-version field was introduced. Existing saved
PDF/history opening reads retained artifacts rather than rerendering them; these
files and checkpoint content are not rewritten by this new-generation policy.

## Checks and limitations

Three deterministic seeds (270100, 20, 123) first produced 12 genuine failures and
six passing controls for blanks, invented scaffolds and repeated material. Public
boundary controls also reproduced the missing independent content check. The first
natural-flow visual review then found a stranded Q02 number: a separate three-seed
RED reproduced it; the owner reservation made all 21 flow checks pass.

The final related group passed **213 checks in 42.91 seconds**, including public
package/conformance mutations, existing Paper 1 contracts, renderer contracts,
backend dry-run generation, layout-master tests and the pre-existing Accounting,
Business and OCR content-policy dispatches. Strict typing of the new verifier passed.
No failing test was replaced with a fixed new page count.

Before the owner-reservation delta, all 101 pages of the separate preliminary,
electronic answer document, mark scheme and written Paper 2 controls were identical
at full 100-dpi raster/text/geometry; the answer document's 39 fields and program/data
bytes were unchanged. The final reservation is guarded to on-screen question flow;
the final related tests retain these source/role contracts. This is not a fresh
post-reservation raster review of those other roles.

Root individually viewed all ten final seed-270100 question-paper pages at 85 dpi:
Q02 now shares its first prompt's page, and no remaining scoped clipping, overlap,
invented blank or duplicate scaffold was observed. The PDF SHA-256 is
`3d3e3fc5f0eccc75e248e3a609516f4b9775c8e08f919488197f577bccff3b0d`.
This is source-diagnostic visual acceptance, not frozen/public/live-model acceptance.
Integrated full, packaged, native and protected-release gates remain separate.
