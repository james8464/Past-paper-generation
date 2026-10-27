# Keldin user acceptance — 27 October 2026

## Accounting print follow-up — retained-content replay

Two regressions reproduced the visible choice/box contact and repeated marking
instructions. The choice column now reserves a 4 mm gap before the selection
box. General instructions print once, and repeated identical indicative rows
are suppressed without changing the stored question, answer or credit limits.
All **41 Accounting tests** passed, including PDF-coordinate checks around the
selection boxes and checks for a single occurrence of each affected instruction.
The frozen-source full suite passed **3,581 tests with two skipped**; the
development-signed direct Release build also passed.

The saved MLX assessment was replayed through the changed renderer, with measured
page-box conformance and release PDF checks. This is **not another live run**.
The original assessment and original published PDFs were retained unchanged.
The replay remains 36 QP / 26 MS pages. Normalised QP text is unchanged on every
page; only MS pages 3–7 and 22 have changed text, removing repetition. Updated
choice pages and every changed scheme page were visually checked: the choices
now wrap clear of the boxes, and no new clipping was found. Some scheme pages
are now sparse; they were not filled with replacement boilerplate. Question
variety, full marking calibration and the other manual HOLD findings below are
not resolved by these presentation fixes.

Retained replay: `tmp/final-validation-20261027/accounting-print-retained-replay`.
SHA-256 QP `aeb8b755a7131eba04242040616318bf13911000cd0947f492ddeb2316c79615`;
MS `823e42ca5bf1c404c6c3a5a2a42462e968452d3f1b83b1d7d9ba563ed85d679d`.

## Full native MLX attempt and export source scope

The sandboxed, development-signed app completed all 13 item batches using
`mlx-community/Qwen3-8B-4bit` with previews disabled. It then rejected the whole
Accounting Paper 1 at `item_difficulty_review`; no new paper was published.
The activity log included item refinement, so this is not a zero-repair success.

A deterministic reproduction found that review and export constructed different
demand targets for the first ten self-contained Accounting MCQs: review required
retrieval, while export added contextualisation from unrelated option material.
Both Accounting components reproduced the mismatch before the fix. Source-scope
predicates are now shared by generation and export. Full parent content remains
identity-bearing, and no review flags, fingerprints or difficulty thresholds
are overridden. Existing source-conflict and independent-solver tests still pass.

New packages record source-scope version 1. Packages without that marker retain
their original extraction rules, without rewriting stored files or granting new
qualification. Unknown versions are rejected. The focused suite passed **123
tests**, including complete item target/evidence round trips for both Accounting
components, shared-route target comparisons and read-only legacy replay.
This engineering fix does not itself qualify an MLX paper or change the French
fidelity HOLD.

The frozen-source suite subsequently passed **3,579 tests with two skipped**.
The rebuilt sandboxed app resumed the failed configuration through History →
Duplicate Configuration, with previews off, model `mlx-community/Qwen3-8B-4bit`
and seed **1288688945**. It published and opened both documents. This is a
retained-checkpoint recovery, not a new first-attempt/zero-repair trial. The
published provenance records 11 AI-authored items, three reviewed seeded
fallbacks and seven verified-contract-reviewed items. All 21 exported items
passed the package checks. The native print dialog showed all 36 question-paper
pages; it was cancelled without submitting a print job.

All pages of both generated PDFs and both official June 2025 comparators were
rendered with Poppler and visually inspected. Both pairs have 36 question-paper
pages and 26 mark-scheme pages, but equal page counts do not establish equal
demand or quality. The independent-practice labels are present. Key calculations
were recomputed from the printed source: non-current assets £135,300; receivables
£74,600; income-statement profit £1,169,955; partnership residual profits £57,954
and £29,445. These agree with the printed scheme. The manual verdict is **HOLD**:

| Generated pages | Findings against the official role/flow |
| --- | --- |
| QP 1–5 | Readable cover and MCQ sequence; question 5 option A touches its selection box. Question 2 omits the percentage multiplier and adds an unnecessary parenthetical. Questions 7 and 9 repeat a simple gross-profit operation, unlike the comparator's distinct multistep roles. |
| QP 6–11 | Response lines and ledger grids fit. Question 11 does not separate the two reasons. Source tables on pages 8 and 10 are noticeably more compact. |
| QP 12–21 | Source/question/working-space sequence is intact; adjustment arithmetic reconciles. The generated tax charge and interest-on-drawings information are supplied directly, reducing derivation compared with the comparator. |
| QP 22–32 | Both extended cases and their working space fit. The shareholder case is materially different; its personal investment and bonus-issue reasoning is less developed than the comparator. |
| QP 33–36 | Blank/additional pages and independent publisher label are visible; no new clipping found. |
| MS 1–8 | Readable, but pages 2–7 repeat the same general paragraphs. |
| MS 9–20 | Tables fit; numerical checks above reconcile. The sales-account presentation nets returns, unlike the comparator's separate gross-sales transfer; classroom treatment still needs review. |
| MS 21–26 | Question 16 repeats five indicative points and contains generic filler; the final guidance page is sparse. Level descriptors are shorter than the comparator's and are not independently calibrated. |

Retained outputs and all page renders are under the ignored
`tmp/final-validation-20261027/store-ui` and `mlx-accounting-review` directories.
SHA-256:

- Question paper: `2ce6f494defdb2f7d2e5e4a747eab990066eec6e4e15a7a4050e7783c0dd47d7`
- Mark scheme: `5728096ffbc5097d4e601a8a1b2b82c1c833479952b83169e5e171cd4a617d1d`
- Assessment: `e2baa12d68b3c030b480e2342bf4823f9dd60cfb4eaf8f07bc356c06e6b83131`
- Manifest: `d55d647ae513f88ee959938d88be396664b541a9fd9fe9f4cf6192681d647865`
- Official QP: `7482ff23f5406f37e54d49bf76f8d2a1cd5bdd823a4face1f55ee7ece2c1cfa6`
- Official MS: `75bb31088224c2e3e305e3dbd3d6c6efd9891e4f262314d855a4fd1aa1907dd3`

## Teacher-review score controls

The installed form's score steppers were visible, but its accessibility tree
exposed the eight criterion labels without editable score controls or values.
The four-value inputs now use native menu pickers with stable accessibility
identifiers. They retain the same independent bindings and 1–4 range.

Computer-control testing found all eight named controls and exercised all four
choices in each: **32 score selections**. Every change updated only its own
criterion. Recording stayed disabled with no reviewer or notes. Cancel dismissed
the form; reopening restored all default scores, so the unsaved choices were
not retained. No teacher review or attestation was recorded. The form was also
visually checked; the native values and labels fit without new clipping.
All **91 native tests** and the direct Release build passed. This is an
accessibility-API and interaction check, not independent VoiceOver approval.

The same interaction test exposed a second bug: cancelling the manifest chooser
also dismissed the review form and lost its unsaved input. The coordinator now
returns an explicit submission outcome; cancellation keeps the form open, while
submission and validation errors preserve the existing dismissal/alert path.
A new regression failed before the fix. In the rebuilt app, cancelling the
chooser retained the synthetic reviewer name, notes and a changed score. Explicitly
cancelling the form then cleared the draft; reopening restored eight default
scores and disabled recording. No bundle was selected and no review was written.

The short native menus follow the platform guidance for a small, ordered set of
choices: [Apple picker guidance](https://developer.apple.com/design/human-interface-guidelines/pickers).
French paper content, teacher/learner calibration and rights status are unchanged.

## Fit-flag semantics: retained-case comparison

The one-item Qwen2.5 trace independently solved the purchases-journal MCQ and
approved its factual review. Its demand response nevertheless said `approved=true`
with `context_fit=false`, `scaffolding_fit=false` and no stated issues. The target
required no context and allowed up to explicit scaffolding. The application
correctly rejected the conflicting flags; it did not publish a paper.

Review instructions now define fit as appropriateness, not feature presence, and
make clear that maximum scaffolding is a ceiling rather than a required minimum.
All Boolean gates remain enforced. Regressions verify that either a false context
or false scaffolding result still fails, even when context is not required.
Review version V6 invalidates earlier review reuse.

The exact retained review payload has SHA-256
`45d3bf39d023c8508eff81a2cb55812bbabf29fa331b2dcd3f4160ed92eec5e1`.
Using the same cached Qwen3 8B snapshot, the original prompt returned
`approved=true` but `context_fit=false`; the clarified prompt returned approval
with every fit check true. Qwen2.5 still rejected context after clarification.
These bounded observations show a model-dependent interface improvement, not a
complete paper or general model qualification. No task, answer, target or result
was edited to obtain acceptance. Logs remain in the ignored
`tmp/final-validation-20261027/fit-semantics-*` files.

The final frozen-source backend suite passed **3,571 tests with two skipped**;
the combined targeted suite passed **246 tests**. Development-signed sandbox
preflight and strict signature verification passed. A separate complete native
attempt is not counted as qualified by this retained-case comparison. French
content and its fidelity HOLD are unchanged.

## JSON framing, context demand and language follow-up

The cached Qwen3 tokenizer reproduced a protocol mismatch: its default chat
template leaves thinking enabled, while this workflow constrains the response
to JSON. The model's documented non-thinking template closes that channel before
the answer. MLX JSON requests now explicitly select that template once. The
pinned Outlines adapter's automatic template is disabled to prevent a second
wrapper; the underlying tokenizer is not modified. Base models without a chat
template still receive their original prompt. Five regressions failed before
the change; all 51 provider tests passed after it.

The first native trial with corrected framing still failed question 01's context
demand check and published no paper. Framing correctness alone does not qualify
the model. Difficulty review now states the immutable target's actual context
requirement outside the untrusted candidate payload. A self-contained knowledge
task need not invent an external extract; an application target must still use
its context. Two prompt regressions failed before this clarification. Separate
tests confirm that a rejected context check still fails for either target: no
review flag is overridden. Review version V5 prevents silent reuse of older
reviews. The combined targeted suite passed **243 tests** and the frozen-source
full suite passed **3,568 tests with two skipped**.

Native testing found that translated status strings did not honor the app's
explicit French language choice. The corrected resource lookup passed the new
red/green regression; all **90 native tests** passed. History now displays
“Baccalauréat · NSI / Épreuve écrite” instead of internal French identifiers.
The quality inspector no longer substitutes route readiness for missing package
engineering evidence: without a saved package it says “At creation”. These two
presentation fixes were checked through the signed sandbox app. Direct Release,
development-signed App Store preflight and strict signatures passed.

All previous failures and checkpoints remain. MLX full-paper qualification,
French manual fidelity and external release gates remain open. Sources:
[Qwen3's chat-mode contract](https://huggingface.co/Qwen/Qwen3-8B),
[Apple localized string resources](https://developer.apple.com/documentation/Foundation/LocalizedStringResource).

## Generation feedback and preview history

History now labels layout-only jobs “Layout preview” instead of displaying the
selected model as if inference had run. The stored configuration and provenance
are unchanged. Computer-control inspection of the Release build confirmed the
label on completed and failed preview jobs; live failures still show their model.
The new labels fit the table without clipping.

The workspace shortens the known refinement message to the question being
rechecked. A known model-quality failure explains that no paper was published,
suggests another model and points to Tools for diagnostics. Other errors retain
their original wording. Activity keeps the original backend messages, and Copy
Diagnostic Summary now includes the six most recent activity entries. The new
messages and preview label have French translations. Two regressions failed
before the change, then all **89 native tests** passed. Release build, repository
inventory checks and static release compliance passed.

After the source-scope fix below, a fresh Qwen3 8B native attempt and a duplicate
of the earlier failed configuration both stopped on question 01's context-demand
review. Both remained failed jobs without a new paper. These observations do not
establish a completed MLX paper or justify changing the recommended model.

## Review source scope

A real sandboxed Qwen3 8B attempt accepted four Accounting items, then rejected
question 05 using facts from an unrelated extract. The original question asked
about a “source of finance”; the source selector treated that domain phrase as
an instruction to use the option's case study. This was an application defect,
not evidence that the paper passed or that the model alone caused the failure.

Source selection now distinguishes material references such as “Extract 1” and
“the data above” from topic terms such as “source of finance”, “source document”,
“source code” and “data structures”. Demand-target construction uses the same
scoped material as the reviewers. Explicit evidence and owned question contexts
are retained. Full parent content remains part of the saved-review identity, and
the review version changed so earlier reviews cannot be reused silently.

Ten regression cases failed before the fix. The 106-test targeted assessment and
reference-demand suite then passed; the full suite passed **3,562 tests with two
skipped**. The real Accounting blueprint's ten standalone MCQs no longer inherit
the later case, while question 11 and the owned cases retain their evidence.
Development-signed App Store preflight and strict signature verification passed.
A fresh native Qwen3 attempt is separate from these engineering checks; no full
MLX paper is qualified by them. Logs remain under
`tmp/final-validation-20261027/source-scope-*`.

## Current PDF branding and cover totals

Current UK covers, notices and PDF author metadata use Keldin. Shared wordmark
constants keep the cover variants consistent. Storage paths, signing identifiers,
the notes cache and historical French identities are unchanged. The Edexcel
colophon reader still accepts retained papers carrying the earlier publisher name.

Visual inspection found a separate AQA Economics Paper 3 defect: its cover counted
only the first compulsory MCQ, printing A = 1 and B = 50 beside a total of 80.
The cover now uses the declared candidate marks: A = 30, B = 50, total = 80.
Shared cover validation rejects non-positive or non-integer marks, duplicate
section labels and subtotals that do not sum to the paper total. Regression tests
failed on the original error before the fix, then passed against both the profile
and printed PDF.

All 21 advertised UK layout previews passed on the corrected source, producing
49 PDFs including inserts. Every PDF was checked for the old publisher text and
all authors are Keldin. All 49 covers were rendered and their contact sheets
inspected; the changed AQA, OCR and Edexcel cover styles and corrected Economics
subtotal were also inspected at full size. No new clipping or overlap was found
in those changed elements. These are layout previews, not live model or content
qualification. Earlier incorrect covers and renders were retained.

The final local suite passed **3,554 tests with two skipped**. Ruff, repository
hygiene and the direct Release build passed. Evidence remains under
`tmp/final-validation-20261027/keldin-branding-final-corrected` and
`branding-review-corrected`. The corrected Economics Paper 3 question paper has
SHA-256 `df866d97bc2a271fd20eebe0e920f0983a844b51068eef4bf78b3ae64b19a2aa`.
French question content, its manual fidelity HOLD and the external release
reviews remain unchanged.

## Structured MLX follow-up

MLX now uses pinned Outlines 1.3.3 and llguidance 1.9.1 to constrain structured
responses. Full JSON-schema validation follows decoding. Array uniqueness stays
in that validation because llguidance does not implement `uniqueItems`; other
unsupported grammar rules fail before inference. Truncated JSON, duplicate fields
and commentary outside the object are rejected. Batch identifiers remain exact.

Independent multiple-choice solving is limited to the public options, without
the private key. A one-mark choice cannot invent alternative correct options.
MLX can now use the same reviewed seeded-stem recovery as Ollama after bounded
wording failures. It restores the original question and repeats the required
answer, marking, difficulty and originality checks. Provenance records
`reviewed-seeded-fallback:apple` when this happens.

The retained isolated Qwen2.5 7B MCQ diagnostics returned the correct purchases
journal answer and a consistent mark point. Total observed times were 83.57
seconds with the default Outlines backend and 9.66 seconds with llguidance.
These single observations do not establish a performance guarantee or qualify a
paper. The corrected full-paper run, seed 270127, accepted questions 01 and 02,
then stopped at question 03 because the difficulty reviewer rejected scaffolding
fit. No completed paper was published. Earlier batch, numeric-drift and
alternative-answer failures remain under `tmp/final-validation-20261027/`.

Computer-control testing of the development-signed sandbox build reached real
Llama 3.2 3B inference and accepted its first accounting item, seed 1288688945.
The test then used Cancel. History recorded Cancelled and creation controls
became available again; this bounded smoke test did not complete a paper.
A newer Qwen3 8B trial is separate and is not counted as qualification here.

Model setup now downloads data files without repository Python files. Loading
explicitly disables remote tokenizer code and tokenizer network access. All
decoder code is packaged with the helper. Frozen apps still cannot install a
runtime. This addresses a download-policy risk identified against Apple's
rules; distribution signing, upload and Apple review remain open.

The final local suite passed **3,546 tests with two skipped**; all **87 native
tests** passed. Development-signed App Store preflight and strict bundle signature
verification passed. An earlier suite ran while source files were being edited
and correctly rejected an implementation-identity change during V33 replay. The
43-test V33 suite and subsequent frozen-source full runs passed. No replay check
was relaxed.

Sources: [Outlines MLX integration](https://github.com/dottxt-ai/outlines/blob/main/docs/features/models/mlxlm.md),
[llguidance schema support](https://github.com/guidance-ai/llguidance/blob/main/docs/json_schema.md),
[Apple review rules](https://developer.apple.com/app-store/review/guidelines/).
French source and layout were unchanged; their recorded manual fidelity HOLD,
rights gap and external teacher/learner reviews remain open.

## Result

Computer-control testing reproduced failures that the source-tree tests had missed. This update fixes MLX setup, instruct-model formatting, packaged UK marking policies, document selection, replaced-file previews, multi-page printing and safe PDF export. It does **not** qualify every model or establish that the app is ready for public educational use.

The installed direct build is `/Users/james/Applications/Keldin.app`. Test outputs remain under the isolated checkout's ignored `tmp/user-acceptance-20261027/`. Previous builds were moved to Trash, not permanently deleted. User history, downloaded references and earlier paper evidence were retained.

## Failures and fixes

- MLX setup loaded a model, then rejected its cache because the Hub client expected repository files that mlx-lm intentionally does not download, including README.md and .gitattributes. Local resolution now uses mlx-lm 0.30.2's inference-file filter. Generation still forbids network downloads outside approved setup; missing inference files still require setup.
- MLX instruct models received raw prompts. The provider now applies the tokenizer's chat template when available; base-model behavior is unchanged.
- The packaged UK preview failed because `level-of-response-policies.json` was absent. It is now included in the helper and build fingerprint. The bundled health check parses it and fails on missing or invalid policies.
- Successful generation selected the oldest question paper. It now selects the newest. A replaced filename receives a fresh document identity, the PDF view reloads that revision, and externally requested selections propagate into the preview. Restoring the document library removes duplicate paths without deleting job records.
- Separate current-generation artifacts from the document library. Completion records and sandbox exports now use only files emitted by that operation; older library PDFs cannot be attached to a new job's provenance. The final native Accounting preview stored exactly its four artifacts. Ambiguous historical artifact identities and reused paths no longer enable Copy Provenance; the original records remain unchanged. Teacher review records already written beside a selected manifest are not exported as new paper bundles.
- Printing used a zero-sized PDFView and offered one page for a multi-page document. PDFKit now creates the whole-document print operation. The corrected native dialog showed page 1 of 18 for the French correction. No physical print job was sent.
- Export removed an existing destination before reading the source. Selecting the source itself could therefore delete it. Same-path export is now a no-op; other exports read first and write atomically. Tests also verify that a missing source leaves an existing export intact.
- The first clean-sandbox Economics preview exposed an axis-label/MCQ-mark collision. An independent packaged scan of seeds 0–23 reproduced it at Edexcel paper 1, seed 22. Diagram layout now reserves the axis caption and its descent before the following prompt. All 24 seeds pass packaged validation after the fix; seed 22's rendered page 6 was visually checked. The native sandbox job that originally failed was duplicated with its original seed and completed successfully with the corrected helper.

Each regression was observed failing before its fix. Native regression tests cover newest/replaced documents, restored-library deduplication, all-page printing, same-path export and failed-source export. Python tests cover filtered offline snapshots, chat templates and missing bundled marking policies.

## Checks performed

| Workflow | Evidence |
|---|---|
| Installed MLX runtime | Bundled `mlx-status` reported available |
| Guided MLX setup | Original failure reproduced; corrected setup continued into live drafting |
| Real local MLX inference | Cached Llama-3.2-3B-Instruct-4bit returned the requested JSON object through the corrected provider |
| Full live MLX Accounting paper | **Failed validation**: question identifiers did not match the blueprint; no live paper published |
| Cancel generation | Running MLX attempt stopped; History retained its cancelled state |
| Duplicate configuration | Restored Accounting paper 1 and Apple MLX from the cancelled job |
| UK packaged layout previews | All 21 advertised paper/practice routes passed through the installed helper, with expected output events and no errors; these are placeholder previews, not live model qualification |
| Native Accounting preview | Created both PDFs and packages; corrected app opened the new Accounting paper rather than the older French PDF |
| Native French generation | Created a V32 draft without AI setup; opened the new French PDF |
| Documents | Paper/correction selection, Quick Look, print dialog and export exercised; exported correction hash matched its source |
| Navigation | Subject search, OCR selection, unavailable Chemistry state and return to the full list exercised; unavailable subject exposed no Create action |
| Settings | AI, Output and Privacy panes opened; temporary output folder selected through the native chooser |
| Benchmark | Built-in 30-second test completed and displayed results; this is hardware evidence, not paper-quality qualification |
| Automated suite | 3,518 backend tests passed, two skipped; 85 native tests passed |
| Distribution build | Static App Store-mode Release preflight passed. The original ad-hoc identity failed library validation; personal-development signing of that identity stalled in OS sandbox initialization. A separate development-signed test identity launched, replayed its failed preview successfully after the diagram fix, then generated and externally exported paper 2. Production identity/migration and distribution upload remain unqualified |

The tests did not send physical print jobs, create teacher attestations, delete the user's reference corpus, change API keys or purchase model/API credits. Fresh live OpenAI/Anthropic generation, every Ollama model, independent VoiceOver testing and distribution-signed App Store upload were not performed. The acceptance inventory is not a claim that every possible state or button combination has been tested.

### Sandboxed launch failure

An actual App Store-mode launch exposed a limitation that static signature checks do not detect. The ad-hoc hardened helper could not load its nested Python dylib because library validation requires a matching signing team. No library-validation exception or sandbox bypass was added. A copy signed locally with an existing personal Apple development identity passed strict signature verification, but then stalled in `_libsecinit_appsandbox` before app initialization; its one-second process sample is retained in `/tmp/keldin-store-startup-sample.txt`. Xcode's separate attempt to use that identity also failed certificate/team selection. Neither result qualifies a distribution build. The stalled test process was stopped, existing containers were not removed or reassigned, and the working direct build was restored. A correctly provisioned distribution-signing configuration and a fresh sandboxed runtime test remain required.

A diagnostic copy used a separate `SandboxQA` identity, the same personal development signing team, and a new app container. It launched and completed onboarding without disabling any protections. Its first Economics preview was correctly rejected for the diagram collision described above. Updating only that copy's packaged helper to the corrected build, preserving its failed history entry, allowed Duplicate Configuration to replay the original seed successfully. A second preview, paper 2, exported through a security-scoped folder chosen in the native dialog. The external test folder contains exactly paper 2's question paper, source booklet, mark scheme, assessment package and manifest; no earlier paper 1 artifacts leaked into the export. This is clean-container development evidence, not validation of the production bundle identity or an App Store-signed archive. Existing production containers remain untouched.

## French output retained

UI-created package: `nsi-2027-1535248359-8dde7ff64a15`, seed 1535248359, public application-owned V32. The manifest remains `unreviewed_draft`, with exactly 18 technical and a distinct 2 indicative language points. No live-model qualification is inferred.

- Subject SHA-256: `d1804d7fd610b22a8b184955b703c39928251d255c2ea944477966d853bb3bf6`.
- Correction and exported-copy SHA-256: `7944f1b76eadf32c2eaff015f45b8cc8f85692445bebf4136ebdf9e4026b7eec`.
- Assessment SHA-256: `4930fd5c873aee4a220ee5fa8305a38a3f0eec11b01b0281c831fa3a734e5260`.

There were no French authoring or layout changes in this update. The [26 October page-by-page comparison](keldin-engineering-and-french-audit-2026-10-26.md) and its manual fidelity **HOLD** remain in force: three finite families, compact/table-led response flow, no teacher/learner timing and mark calibration. No new final expensive live UK/French matrix was run.

## Remaining release gates

The default MLX 3B model has not passed full-paper validation. A successful setup or small JSON request must not be presented as evidence that it can author a valid complete assessment. Do not weaken identifier, answer, marking or second-pass review checks to make it pass.

Current UK outputs use Keldin. Existing PDFs and historical French render contracts keep their recorded identities. Per-document reference rights, independent accessibility review, teacher/learner evidence, distribution signing and store review remain open. No Apple, examiner, school, regional or prize approval is claimed.

## Same-day follow-up: signed runtime and MLX contracts

The earlier production-identity launch failure above is retained as historical
evidence. A subsequent Xcode build successfully used the existing personal
development identity with the original `com.jamesdurup.PaperCreator` bundle ID.
The build wrapper's isolated home hid Xcode's signing configuration. Selecting
the normal signing home through `HOME_PATH`, together with `SIGNING_IDENTITY`
and `SIGNING_TEAM`, resolved certificate selection. The Makefile now forwards
optional identity, team and signing-style settings to build and test. No
credentials were copied into the repository. No container was deleted or
reassigned, and no library-validation exception or sandbox bypass was added.

The signed Release passed strict bundle verification and App Store preflight.
Computer-control testing launched that original-identity build, generated an
Economics layout preview through its bundled helper, reopened its saved documents
after relaunch, and opened a print dialog offering all eight subject pages. The
app was missing `com.apple.security.print`; it is now declared and required by
the compliance check. No physical print job was sent. This is development-signed
runtime evidence, not a distribution-signed archive, upload or Apple approval.

Within the sandboxed app, the French reference preparation completed after the
download confirmation. A fresh V32 draft, seed **1876489898**, completed and
automatically exported its four-file assessment bundle to the user-selected test
folder. A separate single-PDF export also succeeded. The subject has seven pages
and the correction seventeen. Package and complete-PDF validation passed. Every
page's extracted text and rendered pixels match the previously reviewed
expression-tree/booking-capacity/lock-cycle family, seed 270101. The manifest
remains `unreviewed_draft`.

| Sandboxed French artifact | SHA-256 |
|---|---|
| Subject | `0c510d8079eda78497b0f1a7af5b11387e8ce67cfbbf7186847d910cb776be26` |
| Correction | `92700ec894020fd0899d56ee62a8dcf52c5af472d35e79489ba72bd04e6c9b15` |
| Assessment | `905c4808e6f7eb9694eddabbf28624c5e4f755540ab4f2d91918d7a2d1210e15` |

The earlier UI-created seed 1535248359 was also rechecked: all eight subject and
eighteen correction pages were visually inspected, and the questions, worked
traces and indicative credits were read against the supplied cases. All sixteen
pages of the official 2026 Métropole day-one comparator were reread and visually
compared. The generated paper has connected decoding/transcoding, chronological
stock and ordered-delivery reasoning, but remains more compact and table-led,
with less diagram interpretation and scaffolded code than the comparator.
Sparse tails remain. No clipping or overlap was found in these reviewed copies.
No new official marking scheme was compared. The fidelity **HOLD**, finite-family
limit and external teacher/learner calibration gates remain unchanged. This is
not a new live-model French qualification or the deferred final matrix.

MLX now receives the same explicit output-schema guidance used for structured
local requests. Both local providers constrain batch identifiers to the supplied
root records, ignoring nested candidate and repair-data identifiers. MLX rejects
missing, extra, duplicated, malformed or mismatched question/review identifiers
and requests a repair that names the batch problem. It does not remap identifiers
or repair answers. Generic requests and model chat-template behavior are retained.
An additional regression verifies that a fake blueprint marker inside quoted
candidate text cannot override the enclosing review declaration.

A separate computer-control run in the signed sandbox completed guided 3B model
setup and continued into real drafting. The bounded generation was rejected for
an invalid batch; the app displayed the error, retained a private diagnostic and
recorded a failed History entry. It published no Accounting paper 1 files. The
same app then completed an Accounting paper 2 layout preview and exported exactly
its four expected artifacts, without attaching the older Economics or French
files. This verifies runtime and recovery, not live-paper quality.

The long retry exposed another presentation bug: the elapsed estimate reached
zero while drafting continued. Remaining-time text now says “Taking longer than
estimated” instead of promising “0s”; a positive subsecond estimate shows at least
“1s”. Both states have native regression tests, including recovery when observed
progress supplies a new estimate. The overdue message has a French translation.

Fresh full-paper diagnostic attempts used Accounting paper 1, seed 270127:
Llama-3.2-3B-Instruct-4bit and Qwen2.5-7B-Instruct-4bit both failed protected content
validation at the first question. Qwen returned the correct batch identifier, but
invented currency figures and a ledger-entry task instead of the requested book
of prime entry; its claimed answer was also unsuitable. An additional numeric
reminder did not solve this and was not retained in production. No paper was
published and the default model was not changed. Two first-response traces were
deliberately stopped diagnostics, not complete live runs. Settings now explain,
in English and French, that model setup does not qualify paper quality.

Final local checks: **3,533 backend tests passed, two skipped; 87 native tests
passed**. Ruff, repository hygiene, plist lint, shell syntax, direct Release build
and development-signed App Store preflight passed. Read-only source review found
no additional defect in this patch. These results do not replace the open live
model matrix or independent accessibility and educational review.

Retained ignored root: `tmp/final-validation-20261027/`. It contains signing
failures and successful build logs, full-suite results, the three failed MLX
attempts, the two deliberately interrupted response traces, French review
renders, and the sandbox exports. Earlier attempts and historical packages were
not removed.
