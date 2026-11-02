# Startup import review, 2 November 2026

## Scope

The application factory previously copied legacy file trees before creating the main window. It now merges permitted preferences first, constructs an immutable URL plan and returns a coordinator whose import-busy state is already set. The existing file-copy actor processes the roots in their previous order. Successful roots are registered on the main actor; history is loaded after copying, and migration completion is recorded only when no copy, history-load or legacy-family import failures remain. Store mode does not read the legacy preference domain.

Manual and startup imports share their short busy/error lifecycle. Only manual imports acquire and release a user-selected folder scope. This change adds no general job framework, model work, migration overwrite policy or new download.

History loading and artifact-byte verification still run synchronously after copying. No whole-startup latency, large-dataset benchmark, cancellation, every-button, HIG or Store-approval claim follows from this repair.

## Regression and acceptance evidence

Independent review caught an ordering defect in the first candidate: initial history loading could persist a completed record as missing before pending copies restored its artifact. A real failing test reproduced both the changed state and timestamp. The corrected path skips that initial load only when a startup plan exists. It never generally upgrades missing-artifact records.

The final focused author suite passed 230 tests with strict concurrency and warnings treated as errors. Tests cover a held copy with main-actor heartbeat/navigation, preferences available before coordinator initialization, deferred Apple availability checks, no Store legacy-domain reads, off-main copy execution, partial success, non-overwrite retry, malformed history and completion-version handling. The history-ordering test uses owned byte fixtures at PDF paths to test persistence ordering, not PDF validity. Its failed-copy control still reports missing artifacts and keeps migration pending.

An opt-in native window check passed once against `78e1b494` in 106.929 seconds. It constructed the coordinator with a temporary startup plan and held copy before presenting the real ContentView and SettingsPane. Computer control visited History and Documents, observed progress and disabled import/retention controls, recorded navigation, released the copy, then released and dismissed a subsequent manual-import failure. Controls recovered. Assertions verified owned PDF-byte equality, root mapping, pending-to-complete versioning, manual scope cleanup, no backend requests and three unchanged standard preference keys. Both hosted roots used isolated defaults; no installed history or model inference was used.

This exercises coordinator startup restoration and real views with controlled temporary data. It is not a claim that a large real legacy installation was migrated or that all preferences were byte-audited. The fixture retains its separate manual-only opt-in mode; ordinary test runs skip it rather than pretending to provide interaction coverage.

Local evidence: `tmp/nov2-startup-ui.log` and `macOS/build/logs/nov1-cancel-history-native/startup-ui.xcresult`. Author red/green logs remain in the author worktree under `tmp/nov2-manual-import/startup-order-{red-final,green-final}.log`. Earlier missing-API and fixture compile errors are retained separately and are not runtime regressions. Final aggregate tests, signed builds and protected CI must be recorded in the pull request before merge.

The controlled run also logged AppKit layout warnings. No concrete visible failure was established by these checks; their cause remains unresolved. No unrelated layout workaround or security weakening was introduced.

## Internal implementation review

| File | Exact review scope | SHA-256 |
| --- | --- | --- |
| `macOS/Keldin/Application/KeldinApp.swift` | Fresh full EOF, 67 lines, including isolated XCTest launch and shared scenes | `598630bc372237cae43ffb797c5aa154685632bf3d28568d6a060e21c3611ede` |
| `macOS/Keldin/Application/KeldinMigration.swift` | Fresh full EOF, 312 lines, including planning, completion, copying and unchanged containment rules | `b42ff81ccd134316b21b2b504eab29106cc47a994133060d258fdc9795e2b7bf` |
| `macOS/Keldin/State/ApplicationCoordinator.swift` | Prior 2,294-line EOF plus complete final manual-import and startup deltas; current 2,340 lines, not a new full-file reread | `f2e3a527772f828a6a6d5f2f0620d815620ef2e6b2ab4d2852797d083c3e19e6` |
| `macOS/Tests/PreviousDataImportInteractiveTests.swift` | Prior full 213-line EOF plus complete startup-mode delta; current 242 lines | `f24fbb990bad59cc7505852d9e8cc1897baf1cbb8fb08b2551010fe46d424b5a` |

The new MigrationTests cases received scoped review. This is internal engineering evidence, not teacher review, learner calibration, model qualification or completion of the whole implementation audit. French live-paper and distribution-signing holds are unchanged.
