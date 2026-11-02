# Previous-data import review, 2 November 2026

## Change and limits

Manual import previously copied a complete directory tree synchronously from the main actor. The revised path holds the selected folder's access lease while a dedicated file-copy actor works. Preference merging and history publication remain on the main actor. Navigation and document viewing remain available; generation, benchmark, data maintenance and another import are refused while copying. Settings shows progress.

The copy retains the existing no-overwrite, containment, symlink and atomic sibling-copy rules. A failed history reload now remains an error instead of being overwritten by an import-success message. Choosing the current data folder, or a parent containing it, produces a specific English or French explanation. History retention still applies; the picker no longer promises that history cannot change.

Startup migration still calls synchronous `prepare`. This change does not establish responsive startup for large legacy trees, cancellable import, whole-app interaction coverage, paper quality or Store approval.

## Tests and native observations

- The author reproduced the false-success path with a failing assertion, then passed the focused suite. Four message assertions initially failed before the typed folder-choice error was added. The final focused suite passed 153 tests with strict concurrency and compiler warnings treated as errors.
- An isolated, opt-in native test passed once in 162.419 seconds against `e9836609`. Its separate defaults and temporary files did not use real history. It verified navigation during held copying, disabled conflicting controls, source/destination PDF-byte equality, success and failure lease cleanup, and recovery after failure. The test is skipped by default; that skip is not native acceptance evidence.
- The final `fc564f3f` Debug build was launched normally. Choosing the existing current data folder showed: “This is Keldin’s current data folder. Choose the previous app’s folder.” The refusal created no copied data. Every JSON-file hash in the current data tree matched before and after. Output remained Downloads, preview remained off, and the Settings tab was restored to AI before quitting.
- No AI generation, inference or paid API call was made for these checks.

Retained local logs include `tmp/nov2-manual-import-native-correct-project.log`, `tmp/nov2-import-final-debug-build.log` and `tmp/nov2-import-clear-error-{before,after}.sha256`. The first native invocation referenced a nonexistent workspace and failed before running tests; it is not a source regression. Author red/green logs remain under `tmp/nov2-manual-import/` in the author worktree.

AppKit logged layout-recursion and negative-geometry warnings in both the controlled host and a normal candidate process. The observed windows had no clipping or failed interaction. A bounded source/log investigation did not identify a concrete application cause; the warnings remain unresolved, not certified harmless or suppressed.

## Implementation-review scope

Internal read-only review found no further concrete defect in the scoped fix. This is not teacher or learner evidence.

| File | Review coverage | SHA-256 |
| --- | --- | --- |
| `macOS/Keldin/Application/KeldinMigration.swift` | Fresh full 275-line EOF review, including final typed errors | `01a368ed913e491aaf07390b520e45224d3c15b6176bfa2d5b6479e5e03ba056` |
| `macOS/Keldin/State/ApplicationCoordinator.swift` | Full 2,294-line baseline at `b339f331`, followed by the complete two-line final typed-error catch delta; current 2,296 lines | `ea045d0f09a0afc5cb6b1a81fb5e46295f805e0b9ba4f6db509001cdd825f53f` |
| `macOS/Keldin/Features/Documents/JobHistoryView.swift` | Full baseline EOF and complete final three-line guard delta; current 151 lines | `ba591d115099a43d5ec68d9a9561f67774287696d2a5459f5e2d2b64710fd189` |

The new interactive test was read in full (213 lines). Other changed files received scoped diff review only; their broader implementation audit remains separate. Final aggregate test/build and protected CI results belong to the pull request, not an assumed claim in this source note.
