# PDF loading isolation

## Reproduction

On main `3d9a5491`, `DocumentActionController.update` called `refresh` and read the PDF synchronously on MainActor. An isolated test injected a one-second file read and requested a main-thread heartbeat from an independent scheduler after reading began. The heartbeat waited 1.015 seconds. The test failed both its thread-isolation and responsiveness assertions.

The fixture used a temporary PDF and isolated preferences. It did not read user history or call a model. This reproduction does not establish the cause of the earlier memory hang.

## Change under review

The document controller loads bytes through a serial reader actor. Only the URL and immutable `Data` cross that boundary. PDFKit parsing, annotation changes, bookmarks and interface state remain on MainActor. A loading indicator appears while reading, and document actions are disabled until validation finishes.

Each read owns a separate security-access lease. Cancelling a task cannot revoke access while its blocking read is still running. Results must match the current request revision, file ID and URL before they can replace the preview or open an action panel. Repeated view updates for the same selection reuse the pending work; explicit refresh and document actions read again. Quick Look holds its own lease until the owned preview closes or is replaced. Leaving Documents closes only the preview owned by that controller.

Print, Export, Quick Look and Reveal validate the file again before use. Export retains the original bytes. Recovery and stale-bookmark renewal preserve the actual security-scoped URL used to acquire access, while keeping the saved document identity unchanged. A representation-spy test checks this boundary; it does not emulate an operating-system permission grant.

## Verification so far

The final native scope passed 33 tests with strict concurrency checking and warnings treated as errors. In the same one-second read fixture, the reader ran off the main thread and the independently queued heartbeat responded during the read. The final log records a 0.000005708-second heartbeat delay during a 1.006278791-second read. This is a bounded fixture result, not a general performance benchmark.

Tests cover late failures after selection changes, cancellation and controller deallocation during a pending read, same-path files with different identities, repeated view updates, permission recovery, balanced leases and all four document actions. The action tests replace the PDF after its initial preview load and verify that each presenter receives the newly read bytes. A separate logical-owner test checks Quick Look lease replacement and close without opening a panel. Loading text is checked in English and French.

The final scoped log is `tmp/nov6-pdf-async-acceptance.log`, SHA-256 `f41a10a0c9273a2474ee919a53782bf3c7427809431d21fedef90102cdcb1353`. Full tests, signed builds, actual native interaction and protected CI remain separate release requirements. At this source freeze, the installed application is still release 176.

## Source review

The service and document-preview implementation were read through EOF. The review covered actor ownership, scoped-access lifetimes, cancellation, stale results, modal action targets and Quick Look cleanup. The test review covered new cases and the necessary asynchronous migrations, not the entire test file.

- `macOS/Keldin/Services/PDFDocumentAccess.swift`: `e7017fa9b416973d7fa93a4f063aefdb0837b15637a230c33b7b179e68aa2d90`.
- `macOS/Keldin/Features/Documents/DocumentPreviewView.swift`: `b7f95bca291812d3f2630a0d52dd692af33b7dec3c747e1579dfb28a3e0f0d0f`.

Apple documents the shared preview panel and its window-delegate inheritance in [QLPreviewPanel](https://developer.apple.com/documentation/quicklookui/qlpreviewpanel) and [QLPreviewPanelDelegate](https://developer.apple.com/documentation/quicklookui/qlpreviewpaneldelegate).

## Limits

PDFKit parsing and annotation preparation still run on MainActor. The generation publisher's synchronous `rememberReadablePDF` path and legacy service methods are unchanged. This change does not establish that every file operation is nonblocking, resolve French paper quality, or certify the whole application.
