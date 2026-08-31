# Difficulty Calibration v2 Qualification Report

Initial report: 30 August 2026. Continued qualification: 31 August 2026.

## Outcome

The Difficulty Calibration v2 framework is implemented across all advertised assessment routes. It replaces tariff-only calibration with copyright-safe reference features and an item-level, independently solved difficulty gate. Continued live and manual qualification has exposed unresolved subject-policy and closed-answer validation defects, recorded below; implementation coverage is not evidence that every route is yet correctly calibrated.

## Implemented evidence

- Reference profiles are schema version 2 and cover all 21 advertised assessments.
- Each profile includes paired tariff/command aggregates, mark-weighted demand, response mode, cognitive operation, extraction coverage and per-metric tolerances.
- Every item target declares a lower and upper reasoning-step bound, required cognitive operations, context/data requirements, timing range, scaffolding ceiling and shortcut-resistance rule.
- Shared generators pass their canonical independent solution to a distinct difficulty reviewer and persist the result on the accepted item.
- AQA Computer Science and Pearson Edexcel Economics use the same solver-grounded review and persisted evidence contract.
- Live assessment packages fail closed if any item lacks passing difficulty evidence. Preview packages expose evidence coverage without implying that an AI review occurred.
- The macOS Quality inspector reports item-review coverage, reasoning-range fit, context fit, shortcut resistance, extraction coverage and maximum form drift.
- Saved evidence is strictly revalidated against the current profile, reasoning bounds, operations and timing. Missing fields, contradictory approvals and stale profiles fail; shared-generator resume regenerates invalid items individually.
- Accounting has six independent deterministic solvers for closed source-constrained calculations. They do not consult draft answers and do not replace the subsequent content and difficulty reviews.
- Accounting schemes now include the complete exact answers and working. Depreciation no longer silently rounds to hundreds; company adjustments state their rounding policy; partnership allocations conserve the supplied amounts exactly.
- The data-structures bank retains its 30-mark total but now includes a sustained four-mark, context-dependent comparison, instead of consisting entirely of short-tariff parts.
- Matrix qualification distinguishes successful PDF generation from a passing reference-demand audit and requires both, including in preview runs.
- Live model responses must explicitly contain every difficulty check; omitted checks cannot be filled with affirmative defaults.
- Specialist solver inputs include candidate-visible options, table headers, chart values and diagram structure. Classification blanks remain blank, answer-key fields are excluded recursively, and canonical answers are reconciled before difficulty review.
- Specialist generation and package export share assessment-objective interpretation and preserve inherited question styles. Empty context no longer creates an application requirement; selected-response items no longer incorrectly require explanation.
- Supported decisions (`Advise`, `Recommend`, `Justify`) require analysis and judgement rather than falling through to generic explanation. Corpus extraction now recognises `Advise`, matching [AQA's Accounting command-word guidance](https://www.aqa.org.uk/resources/accounting/as-and-a-level/accounting/teach/command-words).
- Accounting indicative-content tables preserve explicitly declared assessment objectives. Unassigned points show an em dash instead of receiving an invented label based on row position.

## Initial 30 August verification

- Python: 851 passed, 2 skipped, 5 third-party deprecation warnings. The skips are pre-existing environment-dependent checks.
- macOS: 48 tests passed, zero failures, with warnings treated as errors and complete strict-concurrency checking.
- App Store preflight: passed on the final code, including the Release build, property-list checks, strict signature verification, app/helper sandbox entitlements and helper hardened runtime. This is not a guarantee of App Store review approval.
- Advertised preview matrix: 21 of 21 packages generated and passed the schema-v2 reference-demand audit for each of three base seeds (42, 20260830, 26083031): 63 passing packages in total.
- After the final Accounting label correction, both Accounting papers were rerendered and passed again for all three seeds: six additional passing preview packages.
- For base seed 26083031, maximum gated distribution distance was 0.771384 (data-structures cognitive-operation distribution; its focused-bank tolerance is 1.0). Its mark-weighted demand distance improved from 0.819232, which failed, to 0.552566, below the unchanged 0.8 tolerance.
- Minimum official-corpus extraction coverage across the advertised matrix: 0.8.
- Recognising `Advise` raised official Accounting Paper 1 extraction coverage from 0.934211 to 0.973684 without relaxing any tolerance.
- Repository hygiene: 436 tracked files, with no forbidden or unclassified paths. Graphify's code map was refreshed; its existing warning about 37 non-code resources yielding no AST nodes remains visible.
- The corpus profile freshness check passed and retained no official question prose or corpus paths.
- A read-only follow-up review confirmed target equality for 468 specialist items across eight routes and three seeds, explicit rejection of missing checks, complete candidate inputs, answer-key exclusion and reconciliation wiring. It identified no further concrete blocker in that bounded review.
- A second focused review confirmed supported-decision classification for `Advise`, `Recommend` and `Justify`, including consistency at 2, 8 and 25 marks. Four regression cases failed before the correction and passed afterwards.
- Focused live Ollama `gemma4:12b` checks passed the company-statement and both partnership calculation contracts, with no reported issues. Reviewed demand/steps/minutes: company high/8/21; retirement standard/5/9; appropriation standard/8/12.
- Full live AQA Accounting Paper 1, seed 26083031, passed generation and release validation with 21 of 21 independently solved, content-reviewed and difficulty-reviewed parts. The first attempt stopped safely at question 17 because of the `Advise` classification bug; the corrected run resumed the 20 accepted parts and completed in 314.76 seconds. This is one live paper, not a full live matrix.
- The exported assessment was reconstructed from its saved blueprint and revalidated under the final checks. After the label correction, the same accepted blueprint was rendered again through package finalisation, assessment validation, basic PDF validation and manifest creation. Its 36-page question paper and 26-page scheme passed those checks with zero detected text overlaps. This replay reused the accepted AI content; it was not another AI generation run. A subsequent print audit found that this QA replay had bypassed the production render transaction and therefore omitted accessibility tags. The original live exports contain those tags. The replay's basic validation pass must not be interpreted as print/accessibility qualification.
- Manually inspected the generated company source page beside the official AQA 2025 Paper 1 page 12, and the revised data-structures comparison page. Both changed generated pages fit without clipping. The accounting page still differs from the official table placement and spacing; pixel-identical layout is not claimed.
- Manually inspected the live question 17 source, answer page and indicative scheme. Corrected the misplaced AO labels, then inspected the final rendered scheme again. A focused read-only review also verified all three affected table builders and seven prefix-handling cases.

### Reproduction and local evidence

Run the full backend suite with `.venv/bin/pytest -q`. Run strict app tests and
distribution preflight from `macOS/` with `make test AGENT_NAME=codex-difficulty`
and `make preflight-app-store AGENT_NAME=codex-difficulty`.

For each of the three seeds, run `tools/live_generation_matrix.py --dry-run`
with `PYTHONPATH=.`, the project virtual environment, an output directory and
the corresponding `--seed`. The retained local reports are under
`tmp/pdfs/difficulty-v13-preview-26083031/`,
`tmp/pdfs/difficulty-v13-preview-42/`, and
`tmp/pdfs/difficulty-v13-preview-20260830/`. These generated artifacts are
deliberately excluded from Git.

The completed live run and its events are retained under
`tmp/pdfs/difficulty-v8-accounting-p1-26083031/`. The final renderer replay,
including both PDFs, the assessment record, package manifest and inspected
scheme image, is under `tmp/pdfs/difficulty-v14-live-final/`.
The failed 300-DPI print audit of that replay is preserved in
`tmp/fidelity/excellence-accounting-live-300.json`. A corrected saved-content
replay using `render_pdf_atomically` is under
`tmp/pdfs/excellence-accounting-replay-tagged-26083031/`. Its scoped 300-DPI and
600-DPI audits passed the unchanged Accounting Paper 1 document/page-role floors
and print checks with zero failures (aggregate scores 0.685 and 0.684).
Reports: `tmp/fidelity/excellence-accounting-tagged-300.json` and
`tmp/fidelity/excellence-accounting-tagged-600.json`. These are single-family,
saved-content checks, not fresh model runs or full-matrix qualification.
Fresh assessment-revalidation evidence is in
`tmp/difficulty-v13-live-revalidation.json`; final replay evidence is in
`tmp/difficulty-v14-live-replay.json`. The preserved first-attempt failure is
`tmp/difficulty-v13-first-live-result.json`, with its corresponding events file.

Final verification logs: `tmp/difficulty-v14-final-pytest.log`,
`tmp/difficulty-v13-macos-test.log`, `tmp/difficulty-v14-app-store.log`, and
`tmp/difficulty-v13-profile-freshness.log`. The final Accounting-only preview
reports are under `tmp/pdfs/difficulty-v14-accounting-preview-<seed>/`.

## Interpretation

The result supports a claim that generated items and forms are shaped to the observable demand of relevant official papers. It does not establish psychometric equivalence. That remains dependent on independent examiner review, student response data and marker agreement under the empirical-calibration policy.

The same chosen model can perform authorship, content review and difficulty
review in separate contexts. This reduces shared prompt contamination but does
not make their judgements statistically independent. Reference profiles are
aggregate heuristics with explicitly reported extraction coverage, not measured
item-response parameters. The 63-package preview matrix verifies every supported
route and its structural demand envelope; it does not constitute 63 live AI runs
or examiner approval of every generated question.

## 31 August continued qualification findings

Fresh live AQA Computer Science Paper 2 (base seed 26083031) authored and
content-reviewed 14 question groups, then stopped at the first final independent
solution reconciliation after 648 seconds. No paper was released. The saved
groups do not yet constitute passing difficulty evidence. Its report and events
are under `tmp/pdfs/excellence-phase7-live-26083031/`.

A captured follow-up solver check exposed an additional false-pass mechanism:
closed classification labels were treated as a non-exhaustive open response,
allowing duplicated partial points to conceal an incorrect final answer. The
figure also lacked the maintenance examples referenced by its scheme. The
reproduction is retained in `tmp/excellence-cs-solver-probe.json`; these defects
must be fixed before claiming the route is qualified.

Manual Accounting contact-sheet review covered all 36 question-paper pages and
26 scheme pages at overview scale. No clipping was apparent, but the shareholder
source was not the same data reviewed by the model, introductory guidance was
repeated, and some objective labels were incorrect. AQA Accounting has only
AO1–AO3; analysis and evaluation belong to AO3. These are substantive content
and calibration defects, not cosmetic exceptions to waive. [Official scheme of
assessment](https://www.aqa.org.uk/subjects/accounting/a-level/accounting-7127/specification/scheme-of-assessment).

The cross-route objective audit also found unsupported AO4 allocations in both
OCR Computer Science papers. AQA Computer Science Paper 2's saved preview
allocation is 81/7/12 marks for AO1/AO2/AO3, versus the specification's approximate
55/40/5 raw-paper split. Its published component shares must be divided by the
component's 40% qualification weight before comparing them with a 100-mark
paper. Correcting both task demand and objective allocation remains open;
metadata relabelling alone is not sufficient. [AQA Computer Science assessment
scheme](https://www.aqa.org.uk/subjects/computer-science/a-level/computer-science-7517/specification/scheme-of-assessment),
[OCR Computer Science specification](https://www.ocr.org.uk/images/170844-specification-accredited-a-level-gce-computer-science-h446.pdf).

The OCR trace audit found a related answerability defect in the saved normal
preview (base seed 26083031, route seed 26083044). Paper 1 question 1 supplies a
loop over indices 0–8 but has only six data values; the rendered source page
omits those values. Its trace subpart asks for five iterations and output even
though output occurs after the loop. The response table also derives its row
count from a two-case text match rather than the actual requested iterations.
The source, exact trace answers and response rows need one coherent contract
before their difficulty can be judged. This correction is included in the CS
task-demand work; existing preview distribution passes do not establish that
the trace is answerable. The source PDF page was manually checked.

### Shareholder source correction verified

Commits `c538e93`, `65123ce` and `a92f2c5` replace Accounting's renderer-only
investor data with one typed candidate-source contract. Nominal share value,
equity movements, explicit units and numerical comparison evidence now agree
between generation, solving and the printed source. The scheme prints all eight
case-specific worked/analytical points; solver-only derived equity data and
separately paraphrased source facts were removed. Actual PDF regressions check
source parity, scheme completeness, table containment and each header word's
padded cell bounds.

Final verification: 857 backend tests passed, 2 skipped, 5 third-party warnings;
34 Accounting tests passed. Both papers passed preview checks across three seeds
after the source repair, and Paper 1 passed all three again after the final
header wrap. All three final source pages were manually inspected. Scoped
300/600-DPI audits passed unchanged thresholds and print checks with zero
failures (0.681/0.680). Reports are
`tmp/fidelity/excellence-shareholder-round2-{300,600}.json`; previews are under
`tmp/pdfs/excellence-shareholder-round2-<seed>/`. The independent scoped review
approved the correction. Fresh macOS tests passed 48/48; Release/App Store
preflight passed before the final header-only change. This is not App Store
approval or fresh live qualification of the revised source.

The new Economics Paper 1 live attempt failed on a provider timeout during a
recorded low-battery hibernation, before accepting its first item; no PDFs were
released. Preserve `tmp/pdfs/excellence-economics-live-26083031/` as failed
runtime evidence, not a content-review verdict.

The powered-on retry (`tmp/pdfs/excellence-economics-live-awake-26083031/`)
reached content review and failed after 47 seconds. Its first four-mark
contestability part had irrelevant topic-wide revision notes and conflicting
AO guidance: the declared breakdown was Knowledge2/Application2, whereas the
scheme claimed AO1/AO2/AO3=1/1/2. The official 2024 Paper 1 contextual
explain-one-reason examples use Knowledge2/Application1/Analysis1; allocation
must therefore follow the actual task, not a generic four-mark formula. No
paper was released. Item-specific Economics marking remains an open correction.

### Closed-response integrity correction

Commits `afece43`, `bdbc7da` and `9999285` add exhaustive, candidate-slot-based
checking for finite Computer Science answers, preserve private answer keys
through AI authoring, and prevent missing or contradictory fields from passing.
The independent solver receives visible source data and blank/output locations,
not expected answers or computed output lengths. Correct answers can omit a unit
already printed on the answer line; wrong values and incompatible units fail.
Source/solver parity now includes the software-classification examples and
explicit parent/child relationships. Symbolic and program equivalence still
require semantic review; these literal checks do not solve that wider problem.

The independent first review exposed a dropped-key integration bug and two
answer-length hints. Their corrections include four failing-then-passing
regressions, a prompt-version increment to invalidate old reviews, and a final
backend run of 960 passed / 2 skipped / 5 existing third-party warnings. All five
affected normal-backend preview routes passed again under
`tmp/pdfs/task7c-app-preview-matrix-review1/`. Independent scoped re-review
approved the corrections and passed six focused checks. Whole-paper live and
empirical qualification remain open.

A fresh three-item production-provider probe through the repaired authoring
merge passed sound-size and truth-table answers; classification again produced
a wrong duplicated category and was correctly rejected. Evidence:
`tmp/excellence-closed-solver-live-probe-review1.json`. A separate prompt-only
experiment requiring working for every slot, without expected-answer hints,
corrected that classification response. Its integration and regression checks
are queued with the CS demand-policy changes. This single-item result is not
a full live paper or a general model-quality claim.

The preceding final previews passed unchanged 300-DPI print/fidelity checks for
AQA CS Paper 1 (0.704) and Paper 2 (0.692), with no threshold or print failures;
the review correction changes neither rendered source nor geometry. Reports:
`tmp/fidelity/task7c-cs1-300.json` and `tmp/fidelity/task7c-cs2-300.json`.
Manual comparison against official 2025 Paper 2 page 2 still shows a simpler
classification diagram with fewer distinctions, smaller diagram text and
different connectors. Different tariffs prevent a direct difficulty equivalence
claim. This feeds the outstanding CS task-demand audit, not a visual-gate waiver.

A separate shared content-review probe found that a response containing only
`{"approved":true}` passes because omitted issue categories default to empty.
Requiring explicit checks is queued with the Economics content-contract repair;
the existing strict difficulty-review checks do not close this distinct gap.

### Accounting objective and credit calibration verified

Commits `dbea456` and `3dcb5c5` replace Accounting's generic four-objective
policy with its published three-objective meanings. Both 120-mark papers now
allocate AO1/AO2/AO3 as 30/42/48, matching the inspected June 2025 pattern.
Allocation follows actual calculations, case analysis and judgements; mixed
best-fit tasks retain their non-additive indicative content. Shared review and
checkpoint identities now include the subject policy and actual objective
budget, so obsolete approvals cannot silently survive. Other subjects' valid
AO4 support is retained; Computer Science's separate correction remains open.

The independent review found misleading zero-award cells beside valid
indicative content and nonzero level descriptors. A rendered-cell regression
failed before the display fix and passes afterward: these cells now show a
dash, while genuine Level 0 and positive awards retain their numbers. Scoped
re-review approved the fix. Final controller verification: 990 backend tests
passed, 2 skipped, 5 existing third-party warnings. Six normal Accounting
previews passed across three seeds, plus a fresh Paper 2 display preview;
assessment JSON is unchanged by that display correction. These are not live
AI-authorship or external-examiner qualifications.

The controller's two-item production-provider probe passed the current gates
for fixed, reviewed Paper 2 tasks 14.4 and 15.1. It did not author new questions.
For 15.1 the rounded final answer was correct, but an unused extra model field
contained incorrect intermediate arithmetic. The published scheme was correct;
this evidence does not establish that all model working was independently
verified. Probe: `tmp/excellence-accounting-policy-live-probe.json`.

### Shared numeric reconciliation remains a release blocker

A new adversarial reproduction on `3dcb5c5` calls the real shared independent
validation path for Accounting Paper 2, seed 26083122, question 14.2. The task
requires three variances: £22,600 adverse, £9,700 adverse and £2,000 adverse.
An intentionally wrong solver response containing only the input rate £97
passes. Its canonical mark points are then populated from the correct draft
scheme, masking the failure. Presence of a number anywhere in the draft is not
proof that a requested result was independently solved.

Task 7.G now precedes further live qualification: separate expected credit from
solver-derived results, verify closed numeric outputs exhaustively by role and
unit, extend candidate-source deterministic Accounting coverage, invalidate old
approvals, and regression-test the actual shared path. Earlier universal claims
about deterministic or independent verification have been reopened in the plan.
The existing specialist finite-response fixes remain valid but do not cover
this distinct generic numeric path.
