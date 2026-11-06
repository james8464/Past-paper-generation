# PDF loading isolation

## Reproduction

On main `3d9a5491`, `DocumentActionController.update` called `refresh` and read the PDF synchronously on MainActor. An isolated test injected a one-second file read and requested a main-thread heartbeat from an independent scheduler after reading began. The heartbeat waited 1.015 seconds. The test failed both its thread-isolation and responsiveness assertions.

The fixture used a temporary PDF and isolated preferences. It did not read user history or call a model. This reproduction does not establish the cause of the earlier memory hang.

## Change under review

The document controller loads bytes through a serial reader actor. Only the URL and immutable `Data` cross that boundary. PDFKit parsing, annotation changes, bookmarks and interface state remain on MainActor. A loading indicator appears while reading, and document actions are disabled until validation finishes.

Each read owns a separate security-access lease. Cancelling a task cannot revoke access while its blocking read is still running. Results must match the current request revision, file ID and URL before they can replace the preview or open an action panel. Repeated view updates for the same selection reuse the pending work; explicit refresh and document actions read again. Quick Look holds its own lease until the owned preview closes or is replaced. Leaving Documents closes only the preview owned by that controller.

The rendered PDF view participates in AppKit's preview-panel responder callbacks. Quick Look is available only when that view is attached to the current window. Pending and active preview requests have separate leases, so an old view's cleanup cannot discard a newer request. Print and Export do not require a Quick Look responder.

Print, Export, Quick Look and Reveal validate the file again before use. Export retains the original bytes. Recovery and stale-bookmark renewal preserve the actual security-scoped URL used to acquire access, while keeping the saved document identity unchanged. A representation-spy test checks this boundary; it does not emulate an operating-system permission grant.

## Verification so far

The initial loading scope passed 33 tests with strict concurrency checking and warnings treated as errors. In the same one-second read fixture, the reader ran off the main thread and the independently queued heartbeat responded during the read. That log records a 0.000005708-second heartbeat delay during a 1.006278791-second read. This is a bounded fixture result, not a general performance benchmark.

Tests cover late failures after selection changes, cancellation and controller deallocation during a pending read, same-path files with different identities, repeated view updates, permission recovery, balanced leases and all four document actions. The action tests replace the PDF after its initial preview load and verify that each presenter receives the newly read bytes. A separate logical-owner test checks Quick Look lease replacement and close without opening a panel. Loading text is checked in English and French.

The initial scoped log is `tmp/nov6-pdf-async-acceptance.log`, SHA-256 `f41a10a0c9273a2474ee919a53782bf3c7427809431d21fedef90102cdcb1353`. The responder follow-up passed 35 focused tests with the same strict compiler settings, recorded in `tmp/nov6-quicklook-initial-show.log`. These include old-view handoff, same-view replacement and missing-claimant refusal. The test review remains limited to changed cases and migrations.

## Native follow-up

The first release candidate passed 451 native tests, but actual Quick Look replacement failed. Its full Python run was stopped before source changed, and its CI run was cancelled. Those results do not certify the final patch. Removing a cleanup call did not fix replacement.

The responder-based candidate initially refused to show its panel. Runtime logging established that the expected PDF view was the first responder and the application was active, but `currentController` was still nil. No framework control callbacks had run. The implementation was checking ownership before showing a hidden panel. It now shows the panel once, lets AppKit acquire control, and checks ownership before updating the preview. A failed initial request can hide only a panel it opened that remains unclaimed. This follows the initial presentation used in [Apple's QuickLookDownloader sample](https://developer.apple.com/library/archive/samplecode/QuickLookDownloader/Listings/QuickLookDownloader_AppDelegate_m.html).

Actual computer-control checks on source `0a8e881c` verified the mark scheme opening, replacement by its paired question paper, closing and reopening that question paper, and navigation to History while a preview was open. Cmd-P did nothing in History. Back in Documents, Print showed All 26 Pages and was cancelled without printing. A native export to an owned temporary folder matched the source PDF byte-for-byte, SHA-256 `2c65b6cde2da4345caae0e4cea8264e4010c35ae459a7bd8662a8661b345a5f0`.

The original Documents selection and Save panel folder were restored. The candidate quit normally, and all 81 regular user JSON files retained their hashes. The runtime log records three successful presentations with actual AppKit acceptance and begin callbacks. Diagnostics contain bounded type names and focus flags, without file URLs or document contents. Evidence is retained in `tmp/nov6-pdf-native-acceptance.json` and `tmp/nov6-quicklook-runtime.log`.

These checks used a retained layout-preview PDF, not a newly qualified generated paper. Final full tests, signed builds and protected CI remain separate release requirements. At this source freeze, the installed application is still release 176.

## Source review

### Older SDK compatibility

GitHub's Xcode 16.4 build rejected the three responder overrides because that SDK imports the callbacks without main-actor isolation. The newer local SDK accepted the same source. The callbacks now declare `nonisolated` and enter `MainActor.assumeIsolated` synchronously before reading UI state. This checks AppKit's main-thread callback invariant without delaying acceptance or lease handoff in a task. [Apple documents the executor check](https://developer.apple.com/documentation/swift/mainactor/assumeisolated(_:file:line:)). The final protected build must still verify the older SDK.

The full Python run on `cbf89513` found one stale menu-source assertion: it expected four identical document guards, although Quick Look now also requires an attached preview responder. The test now checks the three ordinary guards and Quick Look's combined guard and disabled state separately. Its 14-test file passes. This corrects the assertion without removing the modal-window protection. The earlier run recorded 6,994 passes, one failure and two skips; it is not final acceptance.

The service, document-preview implementation and menu commands were read through EOF, with the subsequent logging and initial-show deltas reviewed separately. The review covered actor ownership, scoped-access lifetimes, cancellation, stale results, modal action targets and Quick Look cleanup. The test review covered new cases and the necessary asynchronous migrations, not the entire test file.

- `macOS/Keldin/Services/PDFDocumentAccess.swift`: `e7017fa9b416973d7fa93a4f063aefdb0837b15637a230c33b7b179e68aa2d90`.
- `macOS/Keldin/Features/Documents/DocumentPreviewView.swift`: `2c7d33258a45d8434a468eeee8feb1b1195791c5629e02eacc5c00e7b0ddca64`.
- `macOS/Keldin/Application/AppCommands.swift`: `1e91189f2395200149bdc901b7db2f169c9351e156423b75e27ec01999d6d421`.

Apple documents the shared preview panel and its window-delegate inheritance in [QLPreviewPanel](https://developer.apple.com/documentation/quicklookui/qlpreviewpanel) and [QLPreviewPanelDelegate](https://developer.apple.com/documentation/quicklookui/qlpreviewpaneldelegate).

## Limits

PDFKit parsing and annotation preparation still run on MainActor. The generation publisher's synchronous `rememberReadablePDF` path and legacy service methods are unchanged. This change does not establish that every file operation is nonblocking, resolve French paper quality, or certify the whole application.
