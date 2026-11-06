# Saved generation failure details

## Confirmed gap and repair

Failed jobs previously saved their state and time but discarded the reason. The
current session retained the backend message, but a retry or relaunch removed
that context from History.

History now saves one optional, app-owned failure category. Selecting a failed
job shows its category and recovery advice in the existing History view. Raw
provider messages, model drafts, paths and credentials are not added to history.
Detailed diagnostics remain transient; this change does not promise a saved
transcript of a failed run.

Known quality refusals reuse the existing code-and-first-line classifier. A
generic French failure is not automatically called a failed quality check.
Unknown failures receive a general category. Saving and history-verification
failures receive publication advice. No correctness guard, model prompt, answer,
provider choice or generation limit changed.

The optional field preserves schema 0 and 1 records. Old failures explicitly say
that details were not recorded. Beginning, completing or cancelling a reused job
clears an old category. Job ownership is checked before changing saved state.

## Review scope

Root and an independent code reviewer read the entire patch. The five production
files had existing source-bound review attestations. Their baseline hashes below
were verified against candidate `6832626`; this review covers their complete
delta, not a new complete-file review of the larger coordinator. Both new test
files were read in full. The localization change adds eleven French entries and
translates the existing Generation label; unrelated entries are unchanged.

| File | Reviewed baseline SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `macOS/Keldin/Domain/GenerationPresentation.swift` | `b44d8386b5263d0d3c3a7a2a7b2715895805538985c4aa969d2ce75aea501a83` | `be57f7a153c57538d052a1a0c4e983cdb26b34b162b472c4273222b412fcffc7` |
| `macOS/Keldin/State/ApplicationCoordinator.swift` | `3f65a459a72747b9dc3eb90c4bce8332eff7d2918a5ed483bfc87b437b5de892` | `884893b25e1787a80ac014665c7e9a2eb8f14225028b4b4ab1eb286d5191bc33` |
| `macOS/Keldin/State/RecentDocumentStore.swift` | `d6ccf6dda4c103447d8afddccbde4e2f94355052198a9b38e4f38616e808f08e` | `6f4a1def0572d19d63e261a38147939f36134da72a82b255fbf280881f74f16c` |
| `macOS/Keldin/State/GenerationCoordinator.swift` | `492806bf6cbe338101c9239d0cc197481f58458200a242e69130a989bbf50e58` | `f1e62bda4a50135cc27a8c2479cd8d2f4064fd16b4169f9544e707c22d0f4d6e` |
| `macOS/Keldin/Features/Documents/JobHistoryView.swift` | `ba591d115099a43d5ec68d9a9561f67774287696d2a5459f5e2d2b64710fd189` | `91da341b8f50414b873f1e3f39e34d94fe95afc64f53580ac1af146c9fcecade` |

New tests: `FailureHistoryTests.swift` has SHA-256
`e206bd0272587a1459a222c67c568ecca67d681aed05dd7cb7a16b0b85ca7222`;
`FailurePresentationTests.swift` has SHA-256
`da71fa760a772cdc7402c73ba1e8bc86c8e4734c445cdb6b6e2d649463102373`.
The catalog has SHA-256
`25084c5c4dbf8bbc795581745a4fa3ae6d8c0c9eaadbb15be4e0d93a9934d6e3`.

## Evidence and limits

The first build stopped on a signing-setting mismatch, not a product assertion.
A subsequent compile-only red build established that the required persistence
APIs were missing. After the repair and final copy/translation changes, nine
focused native tests executed with no failures or skips. Tests cover round trips,
legacy decoding, lifecycle clearing, ownership, privacy canaries, backend-to-job
routing and English/French copy. Source hashes were identical before and after
that final run.

An actual candidate-app inspection then found that the bottom safe-area inset
drew failure details over native table rows. That candidate was not published.
The view now lays the table and details out as separate vertical siblings with a
divider, reserving space rather than drawing an overlay. This additional layout
repair requires a fresh native build, test run and on-screen comparison; the
earlier passing tests do not certify it.

All 100 existing JSON document hashes and all 38 current preference values
matched before and after the focused run. No preferences were restored. This is
bounded test evidence, not complete interaction coverage, live paper quality,
whole-project audit completion or distribution approval. Full native release
checks and an actual on-screen History inspection remain separate gates.
