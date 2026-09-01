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

The remaining whole-form audit also counts all printed options, which
overweights optional sections: Business Paper 1 contains 150 printed marks but
a candidate answers 100; AQA Economics Papers 1–2 contain 200 but a candidate
answers 80. Reference and generated distributions need matching candidate-path
weighting, with every allowed choice checked rather than averaged away.

The Economics Paper 3 objective audit found another substantive demand gap:
AQA's baseline allocates 40/10/15/15 marks and OCR's 47/11/10/12. Both treat
all 30 MCQs as AO1, including numerical application, and some stems add
irrelevant scenario numbers to recall questions. Task 7.H covers actual
task-demand and candidate-path corrections across the remaining routes.
Verified component ranges and the reconciled OCR 2024 item-format evidence are
recorded in `assessment-objective-reference.md`. Deeper cross-checks against
individual items found inconsistencies in both OCR 2022 and 2023 summary grids;
neither is accepted as exact calibration ground truth. Published but conflicting
totals remain distinct from verified totals and inferred task operations.

The fresh two-item Accounting probe on `d1dac13` passed both the three-variance
question (14.2) and activity-based costing question (15.1), with
`verified-contract-reviewed` provenance. Answers are recomputed from declared
candidate inputs; the two model calls review content and difficulty. These are
fixed-contract transactions, not new AI-authored questions or full-paper
qualification. Final Paper 2 preview print checks passed at 300 DPI (0.706;
zero threshold/print failures). Independent review nevertheless found numeric
suffix/range and accepted-alternative bypasses; Task 7.G remains open while
those regressions are fixed.

Task 7.G closed after fix `7ea51fa` and a clean scoped independent re-review.
Complete quantity endings, role-bound numeric alternatives and explicit
supported output units now reject the reproduced bypasses. Integrity version
`closed-numeric-v2` invalidates weaker saved evidence. Final tests: 1,112 passed,
2 skipped, 5 existing SWIG warnings; all 21 preview routes passed. The first
fix-round full suite caught a stale repository inventory (442 versus 444 tracked
files); the snapshot was corrected and the complete suite rerun successfully.

Fresh post-fix production checks of Accounting 14.2 and 15.1 also passed,
including explicit content and difficulty responses, using `gemma4:12b`.
Their provenance remains `verified-contract-reviewed`; this does not turn
fixed numerical questions into new AI authorship or qualify a whole paper.
Current deterministic coverage remains the enumerated contracts: outstanding
OCR CS and Edexcel closed calculations are assigned to Tasks 7.E and 7.F.

### Computer Science implementation — corrective review still open

Commit `2e344f7` introduces explicit AQA/OCR CS objectives, source-derived OCR
numeric/trace contracts, more appropriate actual tasks and complete SQL credit.
AQA's component budgets now match the inspected 2025 allocations: 20/30/50 and
56/40/4. OCR uses explicitly inferred allocations consistent with its rounded
specification shares. Its unadvertised Cambridge placeholder remains unqualified;
these AQA/OCR policies are not presented as Cambridge rules.

The final core run passed 1,198 backend tests and 48 strict macOS tests. All
63 previews generated and passed package-contract checks; 57 passed aggregate
reference checks. The six failures are banks 4.2 and 4.10 across three seeds.
All full-paper components passed those aggregate checks. Every bank still uses
a whole-paper proxy at this point, so bank 4.12's passing score does not establish
topic-matched difficulty. Reviewed topic-specific source metadata is prepared
for Task 7.H; no tolerance or evidence gate was waived.

Manual PDF checks corrected a constant-output trace, omitted final trace values,
an SQL primary-key conflict and missing Boolean symbols. AQA CS2's fresh scoped
300-DPI comparison passed (0.696, no print failures). OCR CS1's scheme document
score remains below its unchanged 0.650 floor (0.641, then 0.643 after typography
work); a complete-credit/layout correction remains open. OCR CS2's typography
snapshot passes at 0.706 but still omits some non-numeric credit criteria and
must not be accepted on its visual score alone.

Independent review also reproduced incorrect encoded-answer alternatives passing
validation and an undefined initial state in an AQA recursive trace. A focused
live SQL run exposed futile self-paraphrase retries caused by restoring the
source-coupled stem after asking the model to rewrite it; the run stopped before
solution/difficulty review. These are open corrective findings, not successful
live qualification. Evidence is retained under `tmp/pdfs/task7e-*`,
`tmp/fidelity/task7e-*` and `tmp/task7e-aqa-sql-live-probe.json`.

### Computer Science reviewed fix — separate live and layout limits

Fix `31cc94c` passed scoped independent re-review: encoded alternatives are
checked, OCR schemes retain all specific credit, and the AQA recursive trace
defines and correctly displays its starting state. Source-coupled AQA questions
now receive actual content review without futile rewriting. Their saved status
is `reviewed-fixed`, not AI-authored; source/content hashes protect reuse and
export. Editable source-free scenarios retain authoring and actual content review.

Final backend run: **1,229 passed, 2 known optional-note skips, 5 existing SWIG
warnings**. Strict macOS build passed; no Swift source changed after the recorded
48-test run. Graphify: 5,505 nodes, 15,316 edges, 261 communities. Fresh CS previews
generated all 21 route/seed combinations; the same six pooled-bank proxy failures
remain assigned to the topic-reference correction. Root manually inspected the
complete OCR criteria and final AQA trace table; earlier artifacts remain intact.

The complete-credit OCR schemes have no print failures but still miss their
unchanged layout floors: Paper 1 document 0.617 versus 0.650, Paper 2 0.647 versus
0.659. These cannot be called visually qualified or fixed by removing credit.

A fresh actual SQL transaction on `31cc94c` passed the complete content review
and its first subpart's solution/difficulty checks. The second subpart used
`COUNT(Booking)` in the answer and `COUNT(*)` in its marking points. The initial
description of the first expression as universally invalid was too strong:
[PostgreSQL permits table-name row expressions](https://www.postgresql.org/docs/current/rowtypes.html#ROWTYPES-USAGE).
The app had not validated the dialect, identifiers or query intent. A bounded
replay confirmed the underlying defect independently: even a non-SQL answer
passed generic open-response reconciliation. The live difficulty gate rejected
a missing required programming operation. The transaction failed and did not
reach later parts. Evidence: `tmp/task7e-review-round1-aqa-sql-live-probe.json`;
the separate follow-up records the unambiguous negative replay.
Candidate-grounded SQL validation is an explicit open follow-up. Neither the
scoped code-review approval nor the first successful subpart is full-paper or
empirical difficulty qualification.

### Further calibration corrections in progress

Manual Edexcel prototype review found incorrect eight-mark levels, duplicated
assessment-objective credit, missing substituted calculation working and
unsupported attribution of fictional extracts. These are being corrected using
the relevant point-based or levels-based official marking style; prototype
rendering is not a live-quality pass.

Normal preview runs then exposed an exact-reference page-count rule that had
previously been satisfied using empty mark-scheme padding (Paper 2: 26 content
pages versus 36 required; Paper 3: 22 versus 31). The scoped correction permits
explicit content-driven Edexcel mark-scheme pagination only with printed-part
and credit-completeness checks. Reference counts remain comparison metadata;
question-paper rules, other-family policies and fidelity thresholds are unchanged.
The failed previews are retained, and this is an intentional structural-policy
change rather than evidence of unchanged visual qualification.

Read-only preparation and a baseline Business PDF inspection also found a
break-even graph whose cost/revenue labels, intersections and keyed movement
disagree. Some other Business tables are printed without supplying their values
to the independent solver. Economics checks found retrieval-only targets for
calculation MCQs, possible duplicate numerical options and a derived diagram
answer leaking into the solver input. These are explicit H1 corrections, not
problems solved by assigning higher objective labels alone.

H2 will bind saved approval to actual candidate/source/credit content and report
the saved package's mode, rather than current UI controls. H3 will complete
candidate-path weighting and topic-bank reference evidence. Their implementation
and final qualification remain open. Local long-running probes now support
verified committed-source archives with before/after integrity checks, preventing
concurrent development from silently changing the version under test.

Edexcel implementation `7216ce4` now has nine passing three-seed previews and a
successful strict packaged build. Checks: 842 root tests, 260 Edexcel tests and
225 affected shared tests (the last group overlaps the root suite). Graphify and
the 456-file inventory were refreshed. Eleven incomplete latent calculation
contracts remain explicitly unsupported; no currently reached live numeric route
was downgraded. Preview evidence is not a live-content or difficulty approval.

The controller's final PDF inspection still found cross-section source citations
in Paper 3 marking, including references to Extract E where the actual evidence
is in Extract A. Other variants retained stale figure labels and case values.
Source-page headings also cross the top frame. These are under independent
review and require correction before this slice is accepted. All failed and
superseded artifacts remain available; the programme is not yet qualified.

Scoped 300-DPI Paper 3 comparison also misses the unchanged mark-scheme layout
floor: 0.628 versus 0.680, with no detected print failures (overall 0.680).
Content-complete pagination therefore does not establish visual similarity.
Further presentation corrections must retain all specific credit and the failed
comparison, rather than lowering the threshold.

An additional committed-source prompt capture found that Edexcel's new private
assessment contract exposed all four expected marking statements to the blind
solver on the tested contestability item. The corrective round now removes that
private payload while retaining candidate inputs and full contracts for later
marking comparison. Actual prompt-capture negatives pass; final regression,
packaging and independent re-review are still required before live qualification.

Corrective commit `b7ec042` rebuilds contextual credit from selected source roles,
selects the actual three largest firm shares, clears source-page headings and
protects the blind-solver input. Final checks: 285 Edexcel tests, 225 affected
shared tests, nine fresh normal previews and a successful strict packaged build.
The earlier 842-test root run preceded the last blind-projection change; its
affected tests were rerun, rather than claiming the old run covered new code.
Graphify and the 458-file inventory are current for the implementation. Scoped
independent re-review is underway; live and visual qualification remain open.

That re-review subsequently passed all four corrections. The first fresh live
transaction, Paper 1 question 1, nevertheless exposed a source-registration
mismatch: the independent solver cited the actual supplied table ID, which the
adapter had not registered in its evidence list. The app rejected the response
before difficulty scoring. Content review passed, but the transaction did not.
The evidence was recorded from an immutable `b7ec042` archive with successful
source/import checks; this is a real integration follow-up, not a passing paper.

Two Paper 2 live items then returned the correct selected answers (Quarter 6
and a 16.1% terms-of-trade increase), but reconciliation rejected both because
the specialist supplied a labelled key where the shared check requires its
integer index. Paper 3's five-mark source explanation also reproduced the
source-registration mismatch. F2 now covers these adapter corrections after J;
H1 additionally covers the observed contestability MCQ whose table is not
needed to choose its answer despite its application allocation. No failed
response has been edited or promoted to a passing difficulty check.

The completed Paper 3 probe reproduced the same source-registration rejection
on all four selected 5/8/12/25-mark questions. Source/import identity verified at
the end. All seven selected transactions across Papers 1–3 failed before their
difficulty judge; these were not seven full-paper runs. Three Paper 3 questions
used reviewed deterministic fallback after unsuccessful wording attempts, while
one retained an AI-authored stem. Reporting must preserve that provenance and
cannot infer newly AI-authored questions from live mode alone. Further Edexcel
model runs wait for the source/key correction rather than repeating this gate.

Task7.J now separates declared open-credit obligations from model-created advice,
keeps concrete closed/numeric alternatives strict, and gives the stored-program
task two source-supported one-mark criteria. A CPU-only semantic comparison runs
after blind solving; private criteria appear only in that comparison, not in the
blind-solver or general difficulty prompts. The default suite passed1403tests
with2existing skips/5dependency warnings, three previews and the strict build
passed, and the privacy fix added352+79 focused passes. Independent review found
one private-difficulty-prompt leak; fix`180bccc` addressed it with clean scoped
re-review. This is engineering/review evidence, not a live semantic pass or
empirical learner-difficulty equivalence.

The first committed-source J CPU transaction from verified archive`0af3f70`
failed safely in the new semantic stage before general difficulty review. The
model supplied both expected supported decisions, exact answer/scheme quotes,
point indices and one-mark allocations, but placed them under top-level criterion
IDs rather than the required `criteria` list; strict validation rejected the
missing field. Source/import identity verified at the end. Artifact:
`tmp/task7j-cpu-live-probe-0901.json`, SHA-256
`f5a0bb7b51f4b8193612eabc992179da26ee64e755330142d4ead442f422e5b4`.
The response is retained as a failed live case, not normalized after the fact or
called a semantic/difficulty pass. A bounded prompt-schema correction must make
the required array shape explicit, retain strict unknown/missing/duplicate
rejection and pass independent review before a fresh transaction.

Task7.F2 commit `d4fa73a` now constructs one atomic Edexcel solver projection
from the selected candidate-public stimulus, registers an `EvidenceRecord` with
the exact same item-specific ID and serialized content, and resolves labelled
multiple-choice keys to their current ordered integer index. The blind prompt
continues to remove marking contracts and keys while retaining ordinary public
source fields. Captured P1, both P2 and P3 solver responses cross the real
solve-and-reconcile boundary in tests with only the later difficulty call
stubbed; mutated, stale, foreign, duplicate and private evidence, invented
citations and wrong keys still fail. Reported checks were 305 Edexcel tests,
276 affected shared/inventory tests, nine passing dry-run previews, Ruff,
inventory, strict packaged build and Graphify. Independent source review found
no Critical, Important or Minor defects. These results close the adapter defect,
not the pending frozen-source model transactions, visual floors, whole-paper
quality or external qualification.

J round-2 commit `1110dd4` passed scoped independent review without findings.
A fresh seed-26083134 Q7 transaction from a verified 252-file archive then
completed every production gate and recorded `passed: true`, with source and
import identity verified at the end. Manual content review nevertheless rejects
it as qualification evidence. The independent answer said only that the CPU can
“fetch and execute instructions as needed”; the semantic judge quoted that text
and awarded the distinct point requiring instructions to be executed serially
or in sequence. Fetching/executing “as needed” does not state ordered execution.
Artifact `tmp/task7j2-cpu-live-probe-0901.json`, SHA-256
`510e9e6d1d8cdb3bbd6df7511b728db324ba11bdfc2de7144da41aa17fcef0c9`,
is preserved unchanged as a technically passing but manually unqualified
semantic false positive. Round 3 must add bounded deterministic evidence for
the two fixed CPU meanings without imposing one exact wording or adding another
model call.

Frozen-source F2 follow-up used that same `1110dd4` archive. Paper 1 question 1
now passed exact source registration, independent solving, MCQ key reconciliation
and difficulty review (`tmp/task7f2-p1-live-probe-0901.json`, SHA-256
`167708c0c171dc2f4c7a33ae24bf29071560965e4722cf1f033ec1dd8f2b80d4`).
Its table-dependent explanation is coherent, but its MCQ can be answered from
the generic “lower sunk costs” option without using the table value despite an
AO2 allocation; H1 retains that source-dependence defect.

Paper 2 confirmed that the formerly rejected Quarter 6 and 16.1% answers now
cross the F2 boundary. The wider selected questions still fail later: Q1(c)'s
coherent precautionary-saving explanation was labelled with retrieve,
contextualise and analyse but omitted the required `explain` operation, while
Q2(b)'s solver response made incorrect terms-of-trade claims and did not match
the source-bound scheme. Artifact `tmp/task7f2-p2-live-probe-0901.json`, SHA-256
`a99f7453b86040cf9cbbb391607d5c02341a55cc2ed0ff0ae48d2e3e521e54e4`,
failed overall with source identity intact. The first result is a reviewer
classification inconsistency; the second is a valid fail-closed content result.

Paper 3 likewise crossed source registration on all four selected transactions.
The 12- and 25-mark items passed their complete live chains. The 5-mark answer
was rejected because the difficulty judge reported five reasoning steps against
a maximum of four, which requires calibration review because verbose solver
working is not automatically candidate demand. The 8-mark solver omitted the
requested response fields and failed answer-scheme reconciliation; its prose
contained several relevant source-linked points, so H1 must make the independent
solver's exact response envelope explicit before deciding substantive mismatch.
Artifact `tmp/task7f2-p3-live-probe-0901.json`, SHA-256
`16dc4a4c2bae6efc2f26d21d333359ef93563bc98bd41b38a16c570773366f2b`,
failed overall with source/import identity intact. These results validate F2's
adapter boundary, not the downstream question/difficulty quality or visual and
external qualification.
