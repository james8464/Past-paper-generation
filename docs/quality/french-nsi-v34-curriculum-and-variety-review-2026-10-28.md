# French NSI V34 curriculum and variety review

## Current decision

V34 is experimental. The public app remains on V32 and its three paper families.
The new edition adds a fourth family and corrects the SQL required by the three
retained families. It creates original practice papers on this Mac without an AI
model. Four families are a finite catalogue, not unlimited variety or full
curriculum coverage.

The user has requested internal evaluation instead of unavailable teacher
reviews. This review therefore checks the papers against official sources and
independently tested algorithms. It does not create a teacher-review record or
claim observed learner timing. Papers remain non-official drafts with indicative
marking guidance.

## Official sources and curriculum correction

The [current Eduscol programme page](https://eduscol.education.gouv.fr/5823/programmes-et-ressources-en-numerique-et-sciences-informatiques-voie-g)
still identifies the 2019 Terminale programme as current. Its SQL requirements
cover core selection, joins and mutations; the programme permits aggregation
without requiring grouping clauses. The accompanying resource guidance also
places outer joins beyond expected Terminale SQL knowledge.

The retained V32 database exercises ask for grouped outer-join reports. V34
replaces those questions with core SQL extraction followed by a Python report.
Every question and answer in all four V34 families is checked against requiring
`GROUP BY`, `HAVING`, `LEFT JOIN` or `COALESCE`. Private SQL used as a separate
test oracle is not presented as candidate knowledge. V32 and earlier source
catalogues are unchanged for historical replay.

The [2027 examination definition](https://www.education.gouv.fr/bo/2026/Special4/MENE2622643N)
requires three independent written exercises, 3 hours 30 minutes, and two of
twenty points for French-language proficiency. V34 keeps exactly 18 technical
points and a separate indicative two-point language rubric. It does not produce
the practical component.

The local comparator is the [2026 Metropole day 1 paper](https://eduscol.education.gouv.fr/sites/default/files/document/26-nsij1me1-128190.pdf),
SHA-256 `275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`.
Its 16 pages contain 36 questions. Its connected tasks move from interpreting a
representation to building helpers, composing them, diagnosing errors and
explaining a result. Its diagrams and scaffolded code do substantial explanatory
work. Matching its page count would not establish equal difficulty.

## The fourth family

The first exercise uses the existing experimental postfix compiler and stack
machine. Candidates trace execution, diagnose invalid prefixes, construct a
recursive compiler, complete an evaluator and justify stack validity and cost.
The program and tree must agree; changing a number alone is not counted as a new
family.

The second exercise distinguishes physical book copies from titles. Candidates
reconstruct active loans using half-open intervals, reject an incorrect query
that confuses a historical return with present availability, and combine core
SQL with a Python dictionary. A proposed overlapping loan is refused. Correcting
the previous return time then permits a new loan at the same boundary. Later
questions require all conflicting pairs, expose a nested-interval counterexample
and distinguish referential integrity from preserving history.

The third exercise uses a stated round-robin scheduling model. Arrivals during
a slice join the ready queue before the unfinished process returns to it. The
questions reuse a trace to calculate waiting times, investigate an incorrect
boundary order, complete a slice helper, construct waiting-time calculations,
and compare a changed quantum. A later arrival introduces a genuine idle gap.
Termination and resource deadlock are treated separately. Switching overhead and
I/O are explicitly excluded rather than silently assumed away.

The retained families remain ordered-tree/sensor/routing,
expression/booking/locks and prefix-code/stock/message-delivery cases. Their
originality screening is unchanged. V34 gives each exercise six technical points;
the earlier editions retain their original allocations.

## Automated checks

The 99 new targeted checks pass, including all 16 normal/enlarged subject and
correction render combinations. Complete printed content is checked in order,
including answers and marking criteria, with A4 geometry, footer and page-count
checks. Prompt, answer, marking or verification tampering is rejected even after
an attacker recomputes the exposed content hashes. False approval fields and
malformed saved failures are refused.

The full repository suite passes 3,685 tests, with two skips. Ruff, repository
classification and release metadata checks pass. The App Store-mode Release
build passes strict signature checks using the personal Apple Development
identity. No Apple Distribution identity is installed, so this is a development
preflight rather than a distribution archive or upload.

The scheduler agrees with a separate one-tick simulator on 2,187 small schedules.
Boundary arrivals, partial final slices and idle periods have explicit tests.
Loan availability agrees between set-based Python and a fixed SQL query across
all 24 source orders and nine snapshot times. Additional tests cover nested
intervals, touching boundaries and the corrected loan state. The printed core
SQL for each retained family agrees with independently assembled row joins.

Four families pass sequentially in one history. A fifth paper repeating a family
is refused; the failed checkpoint is retained. No history was cleared and no
similarity threshold was relaxed. These are application-owned trials, not live
model qualification.

## Review still in progress

### Enlarged-print corrections

Run 3 exposed a correction page containing only the end of question 1h and its
rubric. The database introduction also appeared without either source table.
V34 corrections now refer readers to blank code scaffolds in the subject and
print the complete filled solution once. Incorrect example programs remain in
the correction because they are part of the question's evidence. Candidate
papers retain every scaffold. The ordered-content check follows this explicit
V34 print policy; older editions retain their existing policy.

The new database and scheduling source tables paginate independently from the
first worked answer, so an oversized combined group cannot strand an
introduction. Regression tests require a source table on each introduction
page at 16 points. The font size, questions and credit allocations are unchanged.
No blank pages were added. Run 4 confirmed the database fix and exposed the same
problem in scheduling; run 5 includes both fixes. Earlier runs remain retained.

The installed main-branch app also opened the native Print panel for the selected
26-page Accounting correction. Cancel returned to Documents without sending a
print job. This checks that interaction, not all document actions or paper quality.
Export also saved the selected correction through the native Save panel. The
saved file matched its source byte for byte (SHA-256
`aaed8b943970d7e8a17511395aa909ed9df1db751625235111fc5f735357aa05`).
The uniquely named test export was moved into the ignored UI evidence folder.

The final targeted print/replay suite passes 101 tests, including all four
families in normal and enlarged subject/correction form. All 16 run-5 PDFs pass
the full ordered-content check. The fourth family's enlarged correction remains
34 pages; shorter output alone is not the acceptance criterion.

Every-page visual review and question-level reference comparison of the revised
edition are in progress. The original three families remain more compact and
more table-led than the official comparator. Allocated minutes and difficulty
labels are author estimates, not measurements from learners. No equivalence or
classroom approval follows from the unit tests.

The public route must not change until its complete-package, print, originality,
packaged-runtime and native-app checks pass. No official PDF is bundled; the
document-specific third-party rights gap remains open.

Ignored evidence is retained under `tmp/pdfs/v34-reference-review-20261028` and
`tmp/final-validation-20261028`. Runs 1 and 2 preceded the SQL curriculum
correction and are not final-release evidence. Earlier V13-V33 packages,
checkpoints and failure records have not been removed.
