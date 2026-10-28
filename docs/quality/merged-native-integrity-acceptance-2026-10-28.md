# Merged native integrity acceptance

Protected PR109 merged at `df7200bd30f76ad3024e2ac079c9db42cbd100b3` after Backend
16m07s and macOS 8m42s. Its squash tree equals tested head
`dd18266e5cb825eac467005e81f8fe2da18512ad`. Main was fast-forwarded and the resolved
topic deleted. GitHub then had only main and no open pull requests.

The tested personal-development-signed direct Release replaced the installed
app. Strict signatures pass, and installed frontend and frozen-helper bytes
match the tested bundle. The preceding copy remains recoverable at
`/Users/james/.Trash/Keldin-before-run-integrity-20261028.app`.

## Native verification and resolver limitation

The computer-control service cached the old identifier for the canonical app
path even after replacement. The actual installed bundle was temporarily moved
to `Keldin-Release-Validation.app`, not copied or rebuilt. Computer control could
then address the same merged bundle and its existing user profile directly.

Observed checks:

- The French workspace displays five finite families and uncalibrated notices.
- Existing History records remain visible. Create, Cancel and all document
  commands are disabled in History without an applicable selection/context.
- Selecting a completed French record enables Duplicate Configuration. Invoking
  it opens the French workspace without launching generation.
- Documents opens the existing saved Accounting scheme. Cmd-P shows the selected
  document's 26 pages. Cancel closes the print panel; nothing was printed.
- Cmd-Q closes the app. The bundle was moved back to the canonical
  `/Users/james/Applications/Keldin.app` path and its signature checked again.

SHA-256 inventories of all existing history JSON files before and after these
checks are identical. Logs remain at primary
`tmp/installed-109-history-{before,after}.sha256`. No history entry or retained PDF
was deleted. Some old test/failure entries already existed and were preserved.
The previously saved scheme is not evidence for current Accounting V11 content.

The canonical path is restored and the installed app is closed. Its canonical
path still has the computer-control cache limitation; the temporary-path test
is described explicitly rather than presented as a canonical-path lookup.
These are scoped interaction checks, not every-button coverage or whole-HIG
certification. No App Store upload or approval occurred.
