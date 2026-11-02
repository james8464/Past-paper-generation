# Native backend and document access review

Internal engineering review, 2 November 2026. Codex read all 584 lines of the three services below through EOF on the docs branch at `5b3bc148`. The final hashes were rechecked after reading. No source changes were made for this review.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/Services/BackendClient.swift` | 311 | `c0a431dc54dbc03bcbfb6290bd0f66e237c9f6a61b3682b66a889b5c6c099256` |
| `macOS/Keldin/Services/BackendProcessLifecycle.swift` | 123 | `3ce85f423a656f03b8dc651ae15e2e21df5620e26fd64bc6d5e7e44a916db776` |
| `macOS/Keldin/Services/PDFDocumentAccess.swift` | 150 | `046381db27116bb145129a79ba6a6f5b0e8c4ad6a481b4a8d9658754a129970b` |

## Reviewed behaviour

`BackendClient` launches the bundled helper before considering the direct-build development fallback. Store builds refuse that fallback. The review covered concurrent draining of stdout and stderr, UTF-8 line buffering, unreadable-event handling, main-actor event delivery and completion ordering. An empty successful process remains a valid transport result; the separate UK paper-completion guard is recorded in [the generation file review](native-generation-file-review-2026-11-02.md).

`BackendProcessLifecycle` registers and launches a process under the same mutex gate used by shutdown. Quit closes that gate, requests graceful termination, then escalates only processes still held by the registry. The application delegate waits for the result and reopens the gate if shutdown cannot finish. Process identity is retained directly; shutdown does not search for processes by name or signal a daemon or process group.

`PDFDocumentAccess` validates readable PDF bytes and keeps read-only bookmarks for exact standardised file URLs. The review covered first successful reads, stale bookmark handling, cancelled and wrong-file recovery, read failures and lease release. Remembering another published PDF does not acquire or release the active reader's lease. Bookmark-save failure does not overwrite or delete the PDF.

No new concrete P1/P2 issue was established in these three files. This result does not guarantee that no defect remains.

## Evidence and limits

Relevant portions of `ApplicationCoordinator.swift`, `KeldinApp.swift` and `DocumentPreviewView.swift` were inspected to trace ownership and document access. Existing lifecycle-client, lifecycle and PDF-access tests were inspected for coverage, including shutdown escalation, launch races, recovery, denied access and bookmark preservation. Those caller and test files are outside this complete-file attestation.

No additional tests, helper executions, UI actions, inference or user-settings changes were performed for this batch. Earlier test and runtime results are not presented as newly executed evidence. This source review does not certify Store permissions, every asynchronous interleaving, general security, accessibility or complete application behaviour. Integrated release acceptance remains separate.
