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

P1, P3, T3 and T4 are implemented on the next integration branch:

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

These four packages still need final integration and protected publication.
Their scoped evidence is recorded in the checkpoint-seed, atomic-matrix and
generation-policy/PDF-tool reviews under `docs/quality/`.

The remaining 13 work packages are planned. Record implemented commits, tests,
retained evidence and any justified deferrals here. The file-level coverage
inventory must be completed before claiming a whole-project audit.
App Store distribution credentials, third-party rights and observed learner
calibration are separate from this implementation audit and remain unverified.

### Primary storage and configuration package checkpoint

The preceding count of 17 planned packages predates these four completed
implementations on the primary branch. N5/N6/N7 are committed at `6295278`:
history removal and retention preserve failed records, Keychain errors remain
explicit without exposing credentials, and UK publication commits a complete
output directory before changing document URLs. The final combined native run
passed 178 tests and the personal-development-signed Store preflight passed.
An external-folder Store layout preview published four artifacts with matching
manifest hashes and byte counts; its subject opened and Cmd-P showed 36 pages
before cancellation. This is preview/publication evidence, not live paper
qualification. See `docs/quality/native-storage-transactions-review-2026-10-28.md`.

T7 is committed at `b74c5b1`. A fake-bootstrap regression reproduced five missing
advertised projects without modifying the real environment or accessing the
network. Bootstrap installation, backend CI, pytest paths and conftest routing
now agree on the seven advertised generator roots. All four scoped parity tests
pass. See `docs/quality/generator-configuration-parity-review-2026-10-28.md`.

The separate saved-PDF access repair is committed at `1c6e109`; it is not counted
as completion of another planned package. On this primary checkpoint, 13 of the
original 24 packages remain planned. Parallel Accounting/Python changes require
their own fixed-source acceptance and protected merge before this primary
completion record is reconciled with them.

The new file-level coverage ledger records tracked paths as pending or explicitly
excluded, with reasons: 844 tracked files, 640 pending and 204 excluded at this
checkpoint. Its producer detects missing, duplicate, stale and
forged exclusions. It does not infer semantic review from inventory membership
or mark the whole repository reviewed. That remaining file-by-file work is
separate from completing these defect-specific packages.

The combined coverage/parity/hygiene check passes 25 tests (15 coverage, four
parity and six hygiene). Ruff passes. These results do not replace the final
native suite or fixed-source release checks.
