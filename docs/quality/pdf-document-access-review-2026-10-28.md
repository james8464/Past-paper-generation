# Saved PDF access and reader state

## Reproduced problem

The signed Store candidate opened a retained direct-distribution Accounting PDF
as an empty preview. The file existed, so toolbar actions were enabled, but
Print did nothing. A new Store-generated preview opened normally. Source review
confirmed that file existence was used as a readability check and a nil PDFKit
document was silently assigned to the view. Historical URLs outside the current
output-folder grant had no separate saved access grant.

## Scoped change

One scene-owned loading result now distinguishes missing, denied, unreadable,
invalid and locked files. Preview and document actions share a validated PDF
snapshot. Every action rechecks current bytes; unchanged bytes retain the same
PDF object so the reader's page and zoom do not reset. Failed reads clear the
old snapshot rather than displaying another selected document's content.

Recovery uses a native file chooser for the exact saved PDF. A different file
cannot replace it. Its read-only security bookmark is separate from the output
folder preference. Cancellation and failed bookmark creation preserve prior
bookmarks and documents. Scopes are balanced on selection change and view exit;
the synchronous terminal deinit fallback uses Foundation's real stop operation,
not the injected callback counted by the scoped tests. No PDF or history bytes
are rewritten by access recovery.

English and French notices explain the unavailable file and the recovery action.
This change does not add password entry, arbitrary relocation or broad directory
access. No sandbox or library-validation entitlement is weakened.

## Evidence and remaining gates

Six initial regressions failed 16 assertions before implementation. The first
six-case green result did not include two incorrectly named existing test filters;
the corrected run covered those tests. A later reader-identity regression failed
one assertion before the snapshot-preservation change. The final targeted run
passes 13 cases: 11 new cases and two existing document-action checks.

Logs remain in `tmp/pdf-access-red.log`, `tmp/pdf-access-final-targeted.log`,
`tmp/pdf-reader-identity-red.log` and `tmp/pdf-reader-identity-green.log`.
The existing fixture now creates a real PDF instead of treating arbitrary text
bytes as a valid document. At `c6e2965`, the full native gate passed 189 tests
with no failures. Personal-development-signed Store Release preflight and strict
signatures passed. Logs are `tmp/native-storage-access-final.log` and
`tmp/native-storage-access-store-preflight.log`.

Computer control verified recovery in that signed Store bundle. The external
preview scheme initially showed the denied-access message and disabled actions.
Cancelling kept that state. Selecting its subject instead produced the explicit
wrong-file refusal. Selecting the exact scheme rendered it and enabled Print;
the native panel showed all 26 pages and was cancelled. After a complete process
exit and restart, the bookmark restored the PDF without another chooser and
Print again showed all 26 pages. The original internal output folder and preview-
off preference were unchanged. The app was closed. No paper was generated,
exported or printed during this recovery check.

Both retained preview PDFs still match the hashes recorded before recovery.
This older 26-page preview is not V11 Accounting content acceptance. These scoped
results do not certify later source changes, whole-HIG compliance or complete
interaction coverage. Protected publication remains a separate gate.
