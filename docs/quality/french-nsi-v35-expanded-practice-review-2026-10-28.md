# French NSI V35 expanded practice review

## Decision and scope

V35 adds one original whole-paper family to the four retained V34 families.
The public candidate uses five families, rejects repeats and states that
difficulty and duration are uncalibrated. It uses application-owned exercises,
not an AI model. Explicit Ollama diagnostic calls retain V32. Historical package
replay and the four existing families are preserved.

The new family has three independent written exercises, each worth six points,
with twelve questions each. The paper has 36 questions and 18 technical points,
plus the separate two indicative language points. Its normal subject has nine
pages and correction nineteen; enlarged versions have sixteen and thirty.
The other families still have 34 questions. This is a finite practice catalogue,
not comprehensive syllabus coverage or a claim of official-paper equivalence.

Teacher review and empirical calibration remain `not_run`. The user requested
internal review because teacher review is unavailable. No teacher record or
observed learner timing was created.

## Comparison with official material

The local 2026 Métropole day-one subject was reread and its sixteen rendered
pages inspected. SHA-256:
`275b050d7577142794bb579b66ffc08fe7742a70c943a632eebd32701994310b`.
The current 2019 programme and 2027 written definition informed the review.
The older subject's 6/6/8 technical allocation is not copied into the 2027
18-technical-plus-2-language structure.

The comparison focused on connected reasoning, changing representations,
constructing reusable helpers, tracing state and explaining counterexamples.
Official sparse pages do not justify padding a generated paper to sixteen pages.
No official exercise wording, context or dataset was reused for the new family.

The directory exercise requires an adjacency representation and object links,
then recursive exploration, a shared-name counterexample, shortest-path code,
mutation reasoning and a class-attribute sharing defect. The graph has a cycle,
shared child and isolated node. All 36 source-target distances were checked
against independent relaxation, not just the printed examples.

The allocation exercise connects SQL keys and joins to a candidate relation,
a greedy failure, recursive search, branch-local lists, an invariant and an
impossibility argument after an eligibility change. SQLite checks enforce the
foreign key and composite-key constraints. Independent permutation search
checks the solver across all 512 three-by-three eligibility patterns.

The communication exercise defines an explicit atomic single-slot model.
Candidates trace blocking and retry without advancing the blocked instruction,
distinguish readiness from execution, complete a receive helper, diagnose lost
data and preserve unread data after closure. The security questions distinguish
key roles, compromised endpoints and visible traffic metadata, each with
explicit indicative credit. This is a supplied model, not an assertion that a
particular operating-system channel has exactly these semantics.

These sequences increase sustained construction and explanation compared with
isolated short tasks. They do not establish equal difficulty, actual completion
time or success rates. The source review found two wording problems: an
ambiguous zero-based visit position and a defensive performance disclaimer.
Both were corrected with red/green regression tests before the final source
acceptance run.

## Source and PDF acceptance

Final source commit at acceptance: `1aa4953`. Implementation SHA-256:
`6264f6ffb5dab61c9f055e15e3a3214d5150037e5a8c6e3d7e68c7f8a32ceda6`.
Retained evidence root: `tmp/pdfs/french-v35-expanded-20261028/`.

`run-3/summary.json` records every package, checkpoint and artifact hash from
five normal and five enlarged public source generations using the actual local
French reference index. Every package and PDF passed complete ordered-content,
A4, footer, nonempty-body and source-integrity checks. Repeated preferred seed
270100 selected 270100 through 270104. A sixth request in each output folder
failed with every existing file unchanged. No history was cleared.

All 74 new-family run-1 pages were visually inspected in twenty contact grids.
The other 267 full pages were pixel-identical at 100 dpi to fully reviewed V34
run 9. After the wording fixes, six changed pages were individually reinspected
at full-page size; the other 335 run-2 pages are pixel-identical to reviewed
run 1. Page counts did not change. Exact inheritance and observations are in
`run-1/visual-review.json`, `run-2/wording-page-comparison.json` and
`run-2/visual-review.json`.

The cross-folder follow-up changed selection and bookkeeping, not printed
exercises. All 341 run-3 pages are full-page pixel-identical at 100 dpi to the
reviewed run-2 pages. `run-3/full-page-inheritance.json` records this comparison.

No clipping, overlap, missing table, code, answer or body-empty page was found.
Sparse tails remain, particularly where an enlarged code/question group is kept
together. No padding or font reduction was added. Enlarged graph labels use the
16-point body size. Vector checks verify actual edge direction, endpoints and
arrow geometry; negative tests reject reversed or missing arrows that text-only
checks had accepted.

`frozen-run-2/summary.json` records five signed frozen-backend normal generations
in five separate output roots, using cumulative saved-family exclusions. A sixth
request in another fresh root refuses without changing any existing file. Every
PDF is full-page pixel-identical at 100 dpi to
the corresponding reviewed source output. Frozen execution hashes the helper
executable; source execution hashes Python sources. Both identities were kept
unchanged. Cross-runtime checks independently rebuild content and compare all
fields except the implementation identity and its dependent evidence digest.
Production package validation was not weakened.

App-owned checkpoints now include version, full implementation digest and
selected seed. A regression test covers an old V34 checkpoint in the same output
root. Old checkpoints remain intact rather than being misused or deleted.

## Native acceptance

Computer control generated all five families using the candidate Debug app.
Normal and enlarged print and toolbar/Command-Return entry points were exercised.
The selected seeds were 331507253, 1237439021, 1990623397, 195329049 and
563119145. Each completed `app-owned-v35` history entry matches its manifest.
The five outputs contain 158 pages. Of these, 134 full pages are pixel-identical
at 100 dpi to reviewed run 2; all 24 changed pages were visually inspected in
six additional contact grids. No clipping, missing content or answer inconsistency
was found. Exact page accounting and hashes are in
`tmp/final-validation-20261028/native-v35-page-comparison.json` and
`native-v35-output-review.json`.

French workspace and completion text were checked. A sixth native request
displayed the French five-family refusal, with every output file unchanged.
The test exposed an English status label after dismissal; a regression test
failed on that label and passes after resolving it in the selected language.
The original System language and Downloads output preferences were restored;
the candidate was closed. No history, documents or teacher records were erased.

A final Release check found that folder-local screening alone allowed a saved
family to repeat after changing the destination. The native app now derives
family exclusions from completed or missing-artifact V34/V35 records, persists
stable family identifiers separately from the configurable history limit, and
passes exclusions into backend selection. Failed jobs, previews and unrelated
assessments are not counted. Unknown saved identifiers or missing seeds fail
closed. Existing local text screening remains an independent additional gate.

Red/green tests cover new output folders, V34/V35 modulo mapping, missing files,
corrupt saved usage and usage retained after removing isolated test history rows.
No user history was removed. Native computer control then confirmed English and
French refusal with Downloads selected after all five families had been created
elsewhere. The corrected French status reads « Erreur ». All 67 checked history
and paper files stayed unchanged. System language and Downloads were restored.

The restricted Store build also generated a remaining family, seed 1781703662,
without repeating its prior family at seed 1473858048. Both exported packages,
all artifact hashes and complete PDF contents passed checks. Their 55 pages are
covered by 52 full-page raster matches and three freshly inspected changed pages.
The earlier Store subject opened a nine-page native print preview, cancelled
without printing. Original Store preferences were left unchanged and both
candidate apps were closed. Evidence is in `v35-store-export-review.json` and
`cross-folder-native-files-unchanged.json` under the validation log directory.

## Verification status

Final fixed-source local suite: 3,847 passed, two skipped in 514.20 seconds.
Final native unit suite: 101 passed. Focused tests
after those changes: 93 passed. Logs are under `tmp/final-validation-20261028/`.
Candidate Debug compilation passed. Packaged and native acceptance is scoped
to the recorded tests, not a full interaction-coverage or HIG certification.

Personal-development-signed Store Release preflight passed, with strict bundle
signature checks. Protected checks and merge are separate release gates. This
review alone does not certify them. No Store upload
occurred. The personal Distribution identity, third-party rights clearance and
applicant-owned competition fields remain external requirements. No official
PDF is bundled with the app.
