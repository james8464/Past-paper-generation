# Implementation quality audit and improvement plan

## Scope and baseline

The user requested an examiner-style review of implementation practices, followed
by tested changes published to GitHub. This work follows the existing release
acceptance tasks. Release-blocking findings can be fixed sooner in separate,
reviewed changes.

Three read-only reviews examined Python generation code, native application state,
and repository tooling at `70f69c73edc2f773147dde756fe70d71501a4d80`.
The tooling sample covered 24 Python tools, eight macOS scripts and representative
tests from 177 root test modules. These findings are a starting inventory, not
evidence that every line or runtime path has been reviewed.

Before declaring the project-wide audit complete, record coverage for every
tracked file using the repository inventory. Each maintained source, test and
build/configuration file needs a review entry and disposition. Classify generated
metadata, assets and immutable historical implementations separately, with an
explicit reason for retaining or excluding them from refactoring. Formatter or
lint coverage alone does not count as a semantic review.

Review entry points, validation, failure paths, resource cleanup and ownership as
well as names and layout. Check proposed dead-code removals against Graphify,
imports, registry discovery and dynamic CLI entry points before deletion. Preserve
compatibility code that still serves saved packages. Profile suspected hot paths
before making performance claims, and compare outputs after reusable helpers are
extracted.

A read-only Ruff 0.16.4 baseline checked `Backend`, `Resources`, `tools`,
`tests`, `bridge.py` and `conftest.py`: lint passed; formatting would change
234 files, with 263 already formatted. No formatter changes were applied during
the release freeze. Logs are retained under ignored
`tmp/implementation-audit-{format,lint}-baseline.log`.

Keep historical replay implementations, public identifiers, saved data and
qualification evidence intact. Never remove validation to make a refactor pass.
Performance changes need measurements; shorter code alone is not evidence of
better performance.

## Review rules

- Use four-space Python indentation and the chosen formatter. Follow existing
  Swift indentation until a separately reviewed formatter baseline is agreed.
- Use domain names that distinguish requested seeds from selected seeds, public
  evidence from marking keys, and source artifacts from published copies.
  Conventional short loop indices are acceptable in small scopes.
- Keep `break`, `continue`, pattern matching and early returns when they express
  the algorithm clearly. A `break` exits a loop or switch, not an `if` statement.
  Prefer guard clauses over deeply nested conditionals where they help readers.
- Extract a helper when it owns a coherent operation or removes real duplication.
  Do not replace readable subject-specific rules with a generic framework merely
  to reduce line counts.
- Comments should explain constraints, units, invariants and non-obvious choices.
  Avoid comments that restate assignments. Preserve useful contract documentation.
  The user's docstring-to-comment conversion does not justify changing executable
  strings or disguising authorship.
- Keep untrusted input checks at boundaries even when static types are added.
  Catch the errors a layer can handle; report persistence and publication failures.
- Separate mechanical formatting, behaviour-preserving refactors and behaviour
  changes into different commits so each can be reviewed and reversed.

## Ordered work packages

| ID | Finding and source at baseline | Planned change | Required proof |
| --- | --- | --- | --- |
| N1 | Late cancelled-run callbacks can mutate a replacement run. `ApplicationCoordinator.swift:421`, `703`, `754`; `BenchmarkCoordinator.swift:71`. | Give each backend operation a session identity. Ignore stale events and completions. Preserve the MLX setup cancellation lifecycle. Inject the backend at the orchestration boundary for tests. | Deliver old progress, file, error and completion callbacks after cancellation and a new run. The replacement job, documents and status must remain unchanged. Test generation and benchmarks. |
| N2 | `BackendClient.swift:79` decodes arbitrary pipe chunks independently and can drop split UTF-8. | Buffer bytes until a complete newline-delimited event is available; decode the final unterminated line at EOF. | Split accented French and emoji JSON at every byte boundary; test one-byte chunks, several lines and EOF. Keep invalid-event rejection. |
| N3 | UK generation suppresses history-start errors at `ApplicationCoordinator.swift:653`. | Persist a job before committing active state, and refuse helper launch when persistence fails. | Inject a failing history writer. No process launch, phantom active job or successful status. |
| N4 | `RecentDocumentStore.swift:164` treats migration write failures like corrupt JSON. | Separate decoding/schema errors from access and migration-write failures. Quarantine only invalid records. | Valid records survive failed writes; malformed records still enter quarantine. |
| N5 | History removal and retention suppress deletion failures at `RecentDocumentStore.swift:217`, `253` and `JobHistoryView.swift:60`. | Ignore only an already absent file. Keep failed removals visible and report a recoverable error. | Failed deletion, already absent file, retention failure and restart consistency. |
| N6 | `SecretStore.swift:18` ignores Keychain operation results. | Introduce a narrow Security adapter and typed persistence errors. Keep legacy migration and explicit-clear behaviour. | Denied add/update/delete, successful migration, no secret in messages or logs, no resurrection after clear. |
| N7 | UK publication replaces files sequentially at `ApplicationCoordinator.swift:1242`. | Stage the whole output set, commit safely and update document URLs only after success. Reuse the French publisher only where its contract matches. | A second-file failure leaves every existing destination unchanged; successful publication preserves byte equality. |
| N8 | Coordinator state mirrors extracted stores and mixes process, panels, publication and notification work. | After N1-N7, extract small process-session and publication services. Choose one owner for each state field. Share model-option deduplication. | Existing selection, disabled commands, migrations, seed identity and publication tests remain unchanged; add immutable-request snapshot tests. |
| N9 | `ApplicationCoordinator.swift:249` applies delayed Ollama discovery results without operation ownership. | Invalidate a refresh when a newer operation starts. Check ownership after both awaits and in the error path. Keep model-free French generation available during refresh. | Suspend status/models collection, start generation or a benchmark, then return stale events or throw. No new-run error/status/history change, including after that run finishes. |
| P1 | `assessment_checkpoints.py:26` coerces Boolean seed `True` to `1`. | Validate identity inputs strictly before hashing or serialization. | Reject Boolean/coercible malformed seeds; retain valid signed and historical identities. |
| P2 | Checkpoint stores use per-instance locks and one fixed temporary filename at `assessment_checkpoints.py:78`, `130`. | Specify writer ownership, then use an appropriate cross-process lock and unique sibling temporary files if sharing is supported. | Two independent writers and interrupted replacement cannot corrupt a checkpoint or silently lose accepted updates. |
| P3 | `GenerationPolicy` accepts invalid counts and thresholds at `ai_assessment.py:74`. | Validate positive non-Boolean counts and finite similarity thresholds in range at construction. | Zero, negative, Boolean, NaN, infinity and valid boundary tests. |
| P4 | `providers.py:526`, `1033` infers transport schema and seed from English prompt wording. | Introduce typed request metadata with a compatibility wrapper. Preserve current payloads before changing callers. | Reworded prompts do not change schema/seed; signed seed and retry metadata tests. Run pinned live comparisons because this affects generation. |
| P5 | `family_adapter.py:29` erases adapter types and several modules duplicate JSON-client protocols. | Add narrow shared protocols and generic adapter types incrementally. Start static checks at adapter boundaries. | Static checks plus runtime malformed-JSON tests; no validation removed. |
| P6 | `ai_assessment.py` and `independent_solver.py` combine many responsibilities. | Extract pure prompt builders, public candidate projection and subject dispatch behind existing entry points. Leave immutable historical French code alone. | Prompt/output characterisation, source-credit integrity, private-key canaries and replay tests. |
| P7 | `subjects/selected_response.py:94` contains a long operation ladder and repeated choice/rounding code. | Extract named operation handlers with a visible dispatch registry and a small typed result. | Decimal rounding, ambiguous/missing choices, invalid input and operation parity tests. |
| T1 | `build_backend.sh:33` omits installed dependency versions from helper cache identity. | Hash deterministic installed-distribution metadata as well as source, requirements and interpreter identity. | Reuse unchanged dependencies; invalidate after a simulated ReportLab/Pydantic/MLX version change. |
| T2 | `xcbuild.sh:121` ignores the log writer's pipeline exit status. | Treat failed log capture as a failed evidence-producing build, preserving an original Xcode failure where present. | Fake Xcode, filter and log-writer failures singly and together. |
| T3 | `live_generation_matrix.py:147`, `202`, `310` directly overwrites resumable JSON. | Share an atomic JSON writer using unique sibling temporary files. Preserve append-only event logs. | An interrupted replacement leaves the previous valid result readable. Test resume without approval or identity weakening. |
| T4 | Calibration PDF subprocesses have no deadlines in Accounting, Business and OCR Economics tools. | Share bounded PDF process helpers with document/command context. | Timeout, missing executable, invalid page count and normal success. |
| T5 | Ruff CI omits root entry points and does not enforce formatting. | Establish a reviewed formatter baseline, then check it in CI. Include `bridge.py` and `conftest.py` in linting. Review frozen-source exclusions explicitly. | AST/string equivalence for mechanical edits, lint/format checks, complete tests and replay checks. |
| T6 | Some branding tests assert literal Swift spelling instead of behaviour. | Keep resource/identity assertions. Move action routing and migration semantics into native behaviour tests before relaxing spelling assertions. | Equivalent refactors pass while misrouted actions and broken migration still fail. |
| T7 | Generator roots repeat across pytest, CI, conftest and packaging inputs. | Add one explicit inventory or a tested parity check against the registry. Preserve isolated generator working directories. | Deliberately missing family/configuration entry fails the parity check. |
| T8 | Calibration utilities repeat PDF extraction, hashing and band helpers. | Extract only common infrastructure, retaining subject-specific parsing and qualification rules. | Existing report fields/fingerprints and empty-input behaviour remain stable. |
| T9 | `tools/live_process.py` accepts NaN/infinite deadlines, disabling timeout comparisons. | Require a finite positive numeric deadline before opening logs or spawning work. | Invalid input leaves retained logs unchanged and launches no process; valid integer/fractional deadlines retain behavior. |
| T10 | Secure calibration delete/export flags can fall through to import or silently select deletion. | Validate exclusive operation modes and required IDs before accessing keys, data or storage. | Fake-store regressions prove invalid combinations have no access or import side effect; valid modes remain available. |

## Implementation order and release gates

1. Finish the current identity/migration PR and the Accounting live acceptance.
   Freeze each tested source identity. Keep failed attempts and their real results.
2. Address N1, N2 and N9 as release fixes. Run regression tests against the old
   behaviour first, then the native suite and signed direct/Store-mode builds.
3. Address data-loss and persistence risks N3-N7 and T1-T3 in small changes.
   Use injected failures rather than damaging real user files or credentials.
4. Add P1/P3 input checks, then decide the supported checkpoint writer contract
   before P2. Fix T4 and consolidate the calibration helpers in T8.
5. Establish formatting/lint coverage T5 and configuration parity T7. Review the
   mechanical diff separately. Do not claim a speed improvement from formatting.
6. Refactor N8, P5-P7 and behaviour-focused tests T6 one boundary at a time.
   Record why an abstraction exists and avoid duplicate state ownership.
7. Change provider request metadata P4 last, with frozen request snapshots and
   fresh live paper acceptance. A successful solver probe is not a full paper.

Every implementation package needs a scoped plan, failing regression where a
defect is claimed, green targeted tests, Graphify AST update and tracked-file
inventory. Run the full suite when the final source is fixed. Review the diff,
then require both latest-head protected Backend and macOS checks before merge.
After merge, verify the squash tree, update local main and remove only resolved
topic branches. Install only a tested merged build and preserve user data.

## Completion record

The audit covers the stated sampled scope. N1/N2/N9 are implemented in `fd120fd`:
the old behaviour failed 37 assertions in the 121-test native suite; the fixed
suite passed 123 tests. Five further N9 cases reproduced 17 assertion failures
against that source, with the original 123 tests still passing. The final fixed
native suite passes 128 tests. Personal-development-signed Store-mode preflight
and direct Release builds pass; the direct bundle also passes strict signature
verification. See
`docs/quality/native-run-isolation-review-2026-10-28.md`. Scoped native cancellation
checks pass. These native changes were published through protected PR109.

N3/N4/T1/T2 are also implemented locally. The full native suite now passes
138 tests and the build-script suite passes seven cases. Valid history stays out
of quarantine on I/O failure; combined migrations write once; history-start
failure refuses generation; installed dependency versions invalidate the helper
cache; failed log capture fails the build. Personal-development-signed direct
Release and Store-mode preflight builds pass. See
`docs/quality/native-storage-build-integrity-review-2026-10-28.md` for red/green
evidence and limits. PR109 merged at
`df7200bd30f76ad3024e2ac079c9db42cbd100b3` after Backend 16m07s and macOS 8m42s.
The local main was fast-forwarded, squash-tree equality checked and the resolved
topic deleted. The installed app's frontend/helper bytes and strict signatures
match the tested direct Release. Its previous copy remains recoverable in Trash.
The computer-control resolver still caches the former identifier for that
installed path. Temporarily moving the same installed bundle to a fresh path
allowed scoped History, Duplicate Configuration, Documents and Print/Cancel
checks. The closed app was returned to its canonical path and all history hashes
are unchanged. See the merged-native integrity acceptance record for that
workaround and its limits; this is not every-button coverage.

P1, P3, T3 and T4 were implemented in protected PR110:

- P1 requires an actual integer seed at hashing and decoding boundaries. Four
  coercion regressions failed before the fix; 21 checkpoint tests pass, retaining
  valid signed and historical unsigned seeds and hashes.
- P3 validates positive non-Boolean counts and finite similarity limits in the
  existing range. Forty-four invalid inputs failed against the old policy.
- T3 publishes retained matrix JSON with unique sibling temporary files and
  atomic replacement. A real run-manifest interruption regression failed before
  integration; 26 helper/matrix tests pass, including flush failure and overlapping
  writers. This is not cross-writer merging or directory power-loss durability.
- T4 bounds PDF tools at 30 seconds with document-specific errors. Thirty-three
  boundary regressions failed before the fix; 48 helper/report tests pass.

PR110 merged at `29a9e0587b1bdd5feca7f73b40f0e34d25fa4368` after both protected
checks passed. Its fixed-source Python suite passed 4,122 tests with two skips.
Their scoped evidence is recorded in the checkpoint-seed, atomic-matrix and
generation-policy/PDF-tool reviews under `docs/quality/`.

The combined checkpoint has nine unfinished packages: N8 is partial and eight
remain planned. Record implemented commits, tests,
retained evidence and any justified deferrals here. The file-level coverage
inventory must be completed before claiming a whole-project audit.
App Store distribution credentials, third-party rights and observed learner
calibration are separate from this implementation audit and remain unverified.

### Primary storage and configuration package checkpoint

The original primary checkpoint had 17 planned packages before these four
implementations. N5/N6/N7 are committed at `9bb2601` (rebased from `6295278`):
history removal and retention preserve failed records, Keychain errors remain
explicit without exposing credentials, and UK publication commits a complete
output directory before changing document URLs. The final combined native run
passed 178 tests and the personal-development-signed Store preflight passed.
An external-folder Store layout preview published four artifacts with matching
manifest hashes and byte counts; its subject opened and Cmd-P showed 36 pages
before cancellation. This is preview/publication evidence, not live paper
qualification. See `docs/quality/native-storage-transactions-review-2026-10-28.md`.

T7 is committed at `95721af` (rebased from `b74c5b1`). A fake-bootstrap regression
reproduced five missing
advertised projects without modifying the real environment or accessing the
network. Bootstrap installation, backend CI, pytest paths and conftest routing
now agree on the seven advertised generator roots. All four scoped parity tests
pass. See `docs/quality/generator-configuration-parity-review-2026-10-28.md`.

The separate saved-PDF access repair is committed at `a8eb51c` (rebased from
`1c6e109`); it is not counted as completion of another planned package. That
original primary checkpoint had 13 of the 24 packages still planned before its
integration with PR110.

The new file-level coverage ledger records tracked paths as pending or explicitly
excluded, with reasons: 844 tracked files, 640 pending and 204 excluded at this
checkpoint. Its producer detects missing, duplicate, stale and
forged exclusions. It does not infer semantic review from inventory membership
or mark the whole repository reviewed. That remaining file-by-file work is
separate from completing these defect-specific packages.

The combined coverage/parity/hygiene check passes 25 tests (15 coverage, four
parity and six hygiene). Ruff passes. These results do not replace the final
native suite or fixed-source release checks.

### N8 operation ownership follow-up: partial

The native follow-up at `c9e1f78` (rebased from `d488fad`) fixes concrete ownership
defects without completing
the planned coordinator extraction. A benchmark result no longer releases its
process slot before exit. Model-download and MLX confirmations refuse to replace
running work. Model-download completion and cancellation have operation-specific
handling that cannot finish or cancel an unrelated generation history record.

Six new controlled regressions cover these boundaries. The final targeted
isolation run passes 21 tests. No model was downloaded and no user history was
changed by those tests. Read-only review found no additional actionable defect
in the scoped diff. See
`docs/quality/native-operation-ownership-review-2026-10-28.md` for the red/green
logs and exact scope.

N8 remains partial and is still counted among unfinished packages. State-owner
consolidation and architectural extraction remain planned. Keychain operations
remain synchronous; no performance improvement is claimed without measurements.
The earlier 189-test gate and Store PDF-recovery observations certify their
stated prior source only. The new ownership changes still require their final
combined native gate, signed builds and protected publication.

At this follow-up, coverage lists 845 tracked files (640 pending, 205 excluded).
The 25 coverage/parity/hygiene checks and Ruff pass; these do not mark any file's
semantic review complete.

### Rebased native and Accounting integration checkpoint

The native commits were rebased onto PR110's merged main. There were no
executable conflicts. Native source, T7 and coverage-tool source remain identical
to the pre-rebase native head, and all Accounting/Core source remains identical
to merged PR110. Both audit completion records were retained. Conflicting
derived graph/inventory files were restored from main during replay, then
regenerated for the combined tree.

Fifteen of the original 24 packages are implemented at this checkpoint. N8
remains partial; P2, P4, P5, P6, P7, T5, T6 and T8 remain planned. The regenerated
coverage ledger contains 869 tracked files, with 656 pending and 213 explicitly
excluded. No file-level semantic completion or whole-project audit is claimed.
Final combined native and Python gates still need results for this rebased head.

### Selected-response dispatch and bounded native UI follow-up

P7 is implemented in `ab4f6d4a457f56a4eb89ec5384a02711cb71bdda`.
The original selected-response implementation passed 97 characterization tests;
the named-handler extraction passed the same 97 tests. The final registry/helper
version passed 275 numeric and solver tests, plus 86 existing subject tests.
Formulas, half-up rounding, public-input validation, response fields, explanation
strings, raw numeric results and version strings were preserved. See
`docs/quality/selected-response-dispatch-review-2026-10-28.md`. This is a
maintainability change, not evidence of faster generation or a new paper-quality
qualification.

The bounded native UI follow-up fixes the benchmark toolbar's application-boundary
bypass, visible failure/retry handling, semantic verdict text, persistent URL-based
Remove from Recents, and selected-language finite labels and benchmark copy.
The final interface/quality/coordinator/isolation gate passed 70 targeted tests;
the finite benchmark-copy follow-up passed 31 targeted tests. Those source changes
still require their final combined native suite, signed builds, native interaction
checks and protected publication. No PDF or job-history bytes were deleted by
the Recents change. The read-only review provenance and exact source hashes remain
in `docs/quality/implementation-audit-file-review-2026-10-28.md` and
`docs/quality/native-interface-audit-2026-10-28.md`.

Sixteen of the original 24 packages are implemented at this primary checkpoint.
N8 remains PARTIAL: the concrete operation-ownership defects have scoped fixes,
but state-owner consolidation, immutable-request snapshots and further small
architectural extraction are not declared complete. P2, P4, P5, P6, T5, T6 and T8
remain planned here; work in another checkout does not count as integrated work.
The file-level coverage ledger remains an inventory of pending and excluded work,
not a whole-project semantic clearance. No full language, HIG, paper-equivalence
or App Store approval claim follows from these changes.

## Consolidated checkpoint after protected PR112

This section supersedes the earlier branch-local status counts, not their test
results. Main is at `92765b703bda87b87095b608d6e9b08d6a0e7430` after both
protected checks passed for PR112. Its typed operation owner prevents maintenance
from changing unrelated paper history, and the French benchmark labels were
verified through the native interface. The full native gate passed 214 tests;
signed direct and Store-mode builds passed. No Store submission occurred.

The next consolidated branch includes these separately reviewed changes:

- P2: canonical cross-process locks, unique atomic saves, whole-job leases,
  conditional retirement and terminal-event ordering. The later success-cleanup
  regression passed in a 103-test gate. Cancellation coverage is limited to the
  retirement phase, not a universal post-publication guarantee.
- P4: immutable trusted request metadata replaces prompt-wording inference on
  current routes. The current review contract is version 7. Historical French
  routes remain intact. Targeted final gate: 1,118 passed, two skipped.
- P5: a shared minimal JSON-client protocol and typed client factories replace
  duplicated interfaces. Heterogeneous family model hooks still use explicit
  Any; no repository-wide static checker or complete generic migration is claimed.
  The original static-check acceptance criterion remains deferred. Runtime tests
  do not satisfy it, so P5 is only partially accepted.
- P6: prompt builders, known private-key filtering and named deterministic
  dispatch have separate owners. Seven complete prompt/request snapshots remain
  byte-identical. Targeted final gate: 1,305 passed, two skipped.
- T8: shared calibration infrastructure and explicit v2 content metrics replace
  seed-based variety counts. The metric is scoped, not an exhaustive renderer
  identity. Historical v1 reports are retained; no fresh v2 PASS is invented.
- T9/T10: invalid deadlines and conflicting secure dataset operations refuse
  before their side effects. Twenty-seven fake-boundary cases pass.
- T5: the maintained Python formatter/lint gate covers both root entry points.
  Mechanical formatting changed 230 files; all 535 compared Python syntax trees
  and literal sequences are unchanged. Twenty-nine catalogue source files remain
  byte-identical and linted. This is not semantic clearance of all those files.
- The valid internal Keldin naming changes from `31ec4cd` are integrated
  selectively. TipKit identities and existing Edexcel imports/command are kept.
  A new Keldin Edexcel CLI facade uses the same implementation. Unsafe replay
  comment churn and stale generated metadata are excluded.

N8's concrete ownership defects are fixed; broader model-discovery decomposition
remains a separate maintainability decision without a measured performance
claim. T6's existing resource and source-wiring assertions are retained where no
equivalent native behavioral proof justifies removing them. The renamed context
still has readiness/print-choice tests and stable TipKit identity tests.

Next acceptance is finite: refresh graph/inventory, run the frozen combined
Python/native and signed packaging gates, review current source/frozen public
French output against the official comparator, then run the supported live
quality routes without calling previews live generation. Record failures and
repair genuine current-source faults. Complete the remaining file-level review
dispositions without changing frozen source during identity-bearing tests.
Neither inventory, formatting nor this checkpoint establishes whole-project
semantic review, observed learner timing, complete HIG compliance or official
paper equivalence. Distribution credentials and third-party rights stay external.

The ledger can now retain explicit file-review records (`2363e08`). Each record
requires the exact source hash, tracked Markdown evidence path and hash, and a
nonempty review scope/reason. Regeneration preserves valid records, resets a
changed source to pending and refuses malformed or changed evidence. Tests cover
unknown fields, untracked evidence and escaping or looping symlinks. The final
focused gate passed 32 tests after 11 initial and three additional edge-case
regressions failed. No real file was automatically marked reviewed. These
records bind evidence to bytes; they do not authenticate a reviewer or establish
that an attestation is true. Full file-level semantic review remains unfinished.

### 29 October boundary follow-up

Protected PR114 merged at `47cdeb09` after both latest-head checks passed. Its
tested direct Release replaced the installed app with signature and byte-equality
checks; the preceding app remains recoverable in Trash. The control tool still
resolves some installed-path requests to old identifiers or candidate copies, so
mixed-process GUI observations are not canonical-path acceptance.

A further full-file review of ten qualification/process files found four
specific boundary defects. Commits `c7e0b8cb`, `f33c1d13`, `1488eaca`, `68c531a9`
and `beb3763e` preserve atomic publication outcomes and descriptor ownership,
reject contradictory parsed completion events, refuse vacuous qualification
policies, and distinguish observed calibration from inapplicable gates. All 93
focused tests passed. The checked-in qualification matrix and prior evidence
were not promoted or rewritten. See the qualification-boundary audit record.

The current Accounting failure was a mismatch between a canonical printed
answer and a redundant punctuation-sensitive check. Commit `1ff0011a` repairs
that check; strict real-PDF negative cases remain. The related 69 tests pass.
The original live attempt remains failed. Its separately labelled, zero-call
checkpoint reconstruction has a 60-page review and 55 independent arithmetic
checks, documented in the retained-attempt review.

Native cancellation and Settings-owned download fixes are committed at
`d294616c` and `56170a2c`. New typed Main-window routing is at `41f51255`, with a
recovery-only pending-modal guard at `36d048da`. Settings-origin consent/error
handling is committed at `39a96860`. The combined focused native gate passed 129
tests and the scoped Python wiring gate passed seven. Actual window verification
and final release acceptance are pending; this follow-up is not protected-published
yet.

The separate six-file review/build-boundary record covers the ledger producer,
its tests, Ruff, dependency lists and CI. It records remaining limits such as
version-tagged Actions and direct writes of regenerable ledger metadata. These
reviews can support exact-byte ledger entries; they do not clear unreviewed files.

The separate bookmark follow-up at `7fc9f427` reports failure to save output-folder
access in the initiating scene. Its injected failure regression failed before
the fix; the focused native gate passed 76 tests. Successful saved bytes, selected
path and security-scope options are unchanged. This fixes the silent failure
recorded as outside the earlier scene-routing package.

Actual signed-app testing caught a provider-control highlight that did not reset
after cancelling disclosure. The actual provider and consent were unchanged.
Commit `916738ab` observes the typed pending request and derives the control's
selection; its focused regression gate passed 53 native tests. The full Python
run also identified one obsolete direct-call spelling assertion after typed menu
routing (4,554 passed, one failed, two skipped). That wiring assertion now follows
the route covered by native ordering/recovery tests. A real-repository ledger
check additionally rejects stale reviewed source; its red case caught the changed
Settings service before its explicit re-review. Final gates must use the refreshed
ledger and rebuilt interface, not the preceding frontend's results.

### 29 October PDF, tooling and native safety follow-up

Protected PR116 merged at `4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`.
Its installed Apple MLX Qwen3 8B Accounting Paper 1 run completed a real paper,
with all 60 pages visually reviewed and 55 independent numerical checks. The
smaller default model failed the quality process and published nothing. The
separate installed-MLX acceptance report records both attempts, exact bytes,
repairs and remaining editorial/calibration limits. Neither attempt certifies
the newer source changes described here.

The next bounded implementation package fixes PDF deadline restoration,
exception cleanup, finite dimensions, split-fragment bounds, actual-font text
wrapping and validation before standalone PDF replacement. Six short-component
layouts retain byte and raster equality; long instructions and tokens now wrap
to their measured bounds. Focused Python tests pass 98 cases. The scoped PDF
safety report records the full-file review hashes and intentional differences.

The tooling package constrains build cleanup to its own validated targets and
uses separate path arguments in its Finder fallback. Its tests use fake tools;
no retained build or user file was deleted. The AQA CS console now prepares the
shared runtime from a complete checkout when launched from another directory.
Strict mypy checks cover three dependency leaves and typed-client fixtures.
P5 remains partial: this does not check every family adapter or remove its Any
boundaries. The tooling report records 18 focused and 26 related passing tests.

Native follow-up addresses finite benchmark/ETA values, recovery from a failed
explicit credential clear, and truthful MLX setup copy. Actual long-history
testing also found the segmented document selector overflowing with 30 PDFs.
A bounded contextual menu replaces it; immediate selection-to-action consistency
needs its own regression proof before release. Final combined native tests,
source/frozen French comparison, signed builds and protected CI remain required.

These scoped reviews add file-level evidence; they do not finish the remaining
repository-wide semantic audit. Keep the ledger's pending files visible. No
performance gain, teacher validation, learner timing, whole-HIG compliance or
Store approval follows from this checkpoint.
