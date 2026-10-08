# French NSI database depth — design

## Purpose and boundary

Make the original Terminale NSI written database exercise a sustained, independently solvable reasoning sequence. The current six short questions occupy roughly two subject pages in the [pinned v17 diagnostic](../../quality/french-nsi-v17-live-diagnostic-2026-10-08.md); the [official 2026 Métropole comparator](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf) develops its middle exercise through eleven linked questions across five pages. Its topic differs from our database case. The comparison motivates depth and pacing, not copied content or a mandatory page count. The product remains a non-official training draft pending teacher and learner review.

This increment affects Exercise 2 only. Exercises 1 and 3, the 18 technical + 2 distinct indicative language point split, 210-minute paper, French-only retrieval and non-official PDF labels remain unchanged. The practical component is not supported.

## New version and compatibility

Add a new `fr-nsi-written-2027-v16` authoring route. Leave v13–v15 database contracts, catalogues, checkpoint identities, package replay and PDFs readable. V16 uses a separately versioned application-owned database contract and finite French prose catalogue; model output chooses only registered scene/question/rubric IDs. No arbitrary model SQL or Python is executed. V16 identity binds contract, catalogue, blueprint, model and reference hashes. Unknown versions fail closed.

## Case and question sequence

Use one original incident-management scenario with three related tables, six seeded-but-validated incident rows, an intentionally wrong join and an intentionally wrong Python count. Keep table names, key structure, status vocabulary and fault type stable while varying safe names/labels by seed. The fixed incident facts are `(101,1,2,ouvert)`, `(102,1,3,clos)`, `(103,2,1,clos)`, `(104,3,2,ouvert)`, `(105,2,2,ouvert)`, `(106,3,1,ouvert)` in `(id_incident,id_agent,id_cat,statut)` order. Category frequencies are 2, 3 and 1; there are two initially closed incidents and four open incidents. The targeted update closes incident 101, leaving three closed. The wrong join uses `incident.id_agent = categorie.id_cat` instead of `incident.id_cat = categorie.id_cat`; the wrong Python count tests `statut == 'ouvert'` instead of `'clos'`. Both faults must produce observably different results. Compute SQL results with a private in-memory SQLite database; do not evaluate model-authored code.

Ten numbered questions, `2a`–`2j`, progress through: identify key relationships; reject an invalid foreign-key insertion; follow an incident-to-category join; diagnose an incorrect join; write and interpret the corrected join; aggregate category counts; perform a bounded update and recompute the closed count; construct an assertion exposing the Python bug; correct its condition; and test the corrected function on an empty/no-closed boundary case. Each answer has a deterministic expected result or narrowly defined explanation and an explicit indicative rubric. The question sequence is self-contained and never relies on Exercises 1 or 3.

Three seed-dependent technical allocation profiles total 5.5, 6 or 6.5 points for Exercise 2. Ten per-question times total 70 minutes. Credits use exact decimal arithmetic, with no negative or double credit. The independent two-point language component is unchanged. All prompts, answers, feedback and rubric prose are native French.

## Rendering and evidence

Render the richer case with tables/code and stable question-to-answer/rubric order in normal and large print. Keep headings and individual questions legible across pages; avoid orphaned prompts and answer leakage. Runtime PDF verification binds printed facts, question labels, expected answers and rubric credit to the versioned contract. Preserve every failed attempt and accepted checkpoint. Benchmark fixtures and a single pinned live diagnostic may test V16 after source stabilizes, but fixture success is not live fidelity or educational approval.

## Verification and gates

Use tests-first for contract validity, SQLite facts, ten-part blueprint/scoring, finite selection, prompt/answer/rubric binding, replay identity, UK and older-French compatibility, and PDF layout/large-print bounds. Inspect every new PDF page against the official comparator with the PDF skill. Retain the v17 live manual HOLD until a new pinned paper is evaluated; do not run the expensive final UK/French model matrix while shared source changes. Teacher marking review, learner timing calibration, rights and accessibility evaluation remain external gates.
