# Startup import review, 2 November 2026

## Scope

The application factory previously copied legacy file trees before creating the main window. It now merges permitted preferences first, constructs an immutable URL plan and returns a coordinator whose import-busy state is already set. The existing file-copy actor processes the roots in their previous order. Successful roots are registered on the main actor; history is loaded after copying, and migration completion is recorded only when no copy, history-load or legacy-family import failures remain. Store mode does not read the legacy preference domain.

Manual and startup imports share their short busy/error lifecycle. Only manual imports acquire and release a user-selected folder scope. This change adds no general job framework, model work, migration overwrite policy or new download.

History loading and artifact-byte verification still run synchronously after copying. No whole-startup latency, large-dataset benchmark, cancellation, every-button, HIG or Store-approval claim follows from this repair.

## Regression and acceptance evidence

Independent review caught an ordering defect in the first candidate: initial history loading could persist a completed record as missing before pending copies restored its artifact. A real failing test reproduced both the changed state and timestamp. The corrected path skips that initial load only when a startup plan exists. It never generally upgrades missing-artifact records.

The final focused author suite passed 230 tests with strict concurrency and warnings treated as errors. Tests cover a held copy with main-actor heartbeat/navigation, preferences available before coordinator initialization, deferred Apple availability checks, no Store legacy-domain reads, off-main copy execution, partial success, non-overwrite retry, malformed history and completion-version handling. The history-ordering test uses owned byte fixtures at PDF paths to test persistence ordering, not PDF validity. Its failed-copy control still reports missing artifacts and keeps migration pending.

A test-only follow-up verifies the exact displayed startup-failure message in both English and French; all 27 migration tests passed. Two Python source checks initially failed because they required the removed synchronous factory call. Their replacements check worker wiring, history-before-version ordering, preservation of load failures and the selected-language error route, while retaining the exact translation checks. The targeted current-source suite then passed 150 tests. No production behavior was weakened to satisfy these checks.

An opt-in native window check passed once against `78e1b494` in 106.929 seconds. It constructed the coordinator with a temporary startup plan and held copy before presenting the real ContentView and SettingsPane. Computer control visited History and Documents, observed progress and disabled import/retention controls, recorded navigation, released the copy, then released and dismissed a subsequent manual-import failure. Controls recovered. Assertions verified owned PDF-byte equality, root mapping, pending-to-complete versioning, manual scope cleanup, no backend requests and three unchanged standard preference keys. Both hosted roots used isolated defaults; no installed history or model inference was used.

This exercises coordinator startup restoration and real views with controlled temporary data. It is not a claim that a large real legacy installation was migrated or that all preferences were byte-audited. The fixture retains its separate manual-only opt-in mode; ordinary test runs skip it rather than pretending to provide interaction coverage.

Further review found that Ollama's Check Again and Apple's Check availability looked enabled during import although their coordinator actions refused to run. Separate failing source checks reproduced each missing disabled predicate; both now follow the existing import guard. An expanded native run at `96b2bb85` observed both buttons disabled while the copy waited. Its first attempt exceeded the 180-second held-phase limit because navigation was recorded too late; that failed run remains retained. An unchanged-source retry passed in 113.215 seconds within the same limit, with no weakened assertions or timeout. Both provider choices used isolated defaults and a fake Apple availability checker; no model request was made.

Local evidence: `tmp/nov2-startup-ui.log` and `macOS/build/logs/nov1-cancel-history-native/startup-ui.xcresult`. Author red/green logs remain in the author worktree under `tmp/nov2-manual-import/startup-order-{red-final,green-final}.log`. Earlier missing-API and fixture compile errors are retained separately and are not runtime regressions. Final aggregate tests, signed builds and protected CI must be recorded in the pull request before merge.

Expanded controls evidence: `tmp/nov2-startup-controls-ui.log` (timed out), `tmp/nov2-startup-controls-ui-retry.log` (passed), and `tmp/nov2-startup-{availability-red,apple-availability-red,availability-green}.log`. The first invocation placed wrapper results in a root build folder; after it exited, that folder was moved intact to `tmp/nov2-startup-controls-wrapper-build`. The successful retry's result is `macOS/build/logs/nov1-cancel-history-native/startup-controls-ui-retry.xcresult`.

The controlled run also logged AppKit layout warnings. No concrete visible failure was established by these checks; their cause remains unresolved. No unrelated layout workaround or security weakening was introduced.

## Internal implementation review

| File | Exact review scope | SHA-256 |
| --- | --- | --- |
| `macOS/Keldin/Application/KeldinApp.swift` | Fresh full EOF, 67 lines, including isolated XCTest launch and shared scenes | `598630bc372237cae43ffb797c5aa154685632bf3d28568d6a060e21c3611ede` |
| `macOS/Keldin/Application/KeldinMigration.swift` | Fresh full EOF, 312 lines, including planning, completion, copying and unchanged containment rules | `b42ff81ccd134316b21b2b504eab29106cc47a994133060d258fdc9795e2b7bf` |
| `macOS/Keldin/State/ApplicationCoordinator.swift` | Prior 2,294-line EOF plus complete final manual-import and startup deltas; current 2,340 lines, not a new full-file reread | `f2e3a527772f828a6a6d5f2f0620d815620ef2e6b2ab4d2852797d083c3e19e6` |
| `macOS/Tests/PreviousDataImportInteractiveTests.swift` | Prior full 213-line EOF plus complete startup-mode and fake-checker deltas; current 243 lines | `064271c970a5964126969af95dada24d5f14a47b11cbe9a188595b6b47228ae5` |
| `macOS/Keldin/Features/Settings/SettingsPane.swift` | Fresh full EOF at `96b2bb85`, 526 lines; action dependencies traced selectively | `2def2e837ca8d37d8f51c36854dfaf72f4f7d796b0460bf31434b91cce6c5372` |
| `macOS/Keldin/Features/Documents/DocumentPreviewView.swift` | Fresh full EOF at `27ecbbd0`, 327 lines, unchanged in the controls follow-up; selected access/export/print/provenance dependencies traced | `b8487c162f2f1af6626cfdfbaaab7bc510bca31ba7d023596b7c4c51fcef4dc8` |
| `macOS/Keldin/Domain/GenerationEstimator.swift` | Fresh full EOF at `27ecbbd0`, 335 lines, unchanged in the controls follow-up; both focused test files and selected callers inspected | `c0b204433261b12cbd3796101b4ee6a9520a8058c5d3910e7f031023d924d359` |

The new MigrationTests cases received scoped review. The additional document and estimator audits were read-only, without new print/export/model execution. ETA factors and confidence remain heuristics, not measured model speed or learner timing. Some Privacy values remain raw English; this review does not certify complete French localization. This is internal engineering evidence, not teacher review, learner calibration, model qualification or completion of the whole implementation audit. French live-paper and distribution-signing holds are unchanged.
