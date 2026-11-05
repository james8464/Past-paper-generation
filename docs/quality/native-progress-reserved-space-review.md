# Progress needs its own space

Two controlled generation journeys left the older Recent Documents row hidden
under the progress area. Navigation and protection of the active document worked,
but removing the older record could not be completed. Those failed journeys are
retained; they are not counted as interaction acceptance.

A native measurement reproduced the overlap. In the same 792-point window,
the split view occupied y=0–792 while the progress indicator occupied y=45–65.
The regression failed against the original source. With progress as a real
VStack sibling, the split view occupied y=93–792 and the indicator remained at
y=45–65. The same ordinary native test passed without operator input. A focused
26-test native group passed with no failures.

The change does not add a compensating spacer, special table height, private UI
hook or selection workaround. Width-based layout, sidebar state, minimum window
size, sheets, alerts and focused commands remain unchanged. The complete
134-line ContentView and every added test line were reviewed. The fixture uses
isolated settings and history, a controlled backend and owned temporary PDFs.
The earlier complete baseline test-file review remains separate evidence.

The optional expanded-row check timed out when the Mac locked. It did not run
its geometry assertions. Manual older-row removal remains unverified. Full
release tests, signatures and installed-app checks are separate gates.

| Reviewed file | SHA256 |
| --- | --- |
| `macOS/Keldin/Navigation/ContentView.swift` | `d33b056210dd437cbc762b6a11783f5b465f770d70cb7c565f70104772427687` |
| `macOS/Tests/GenerationNavigationInteractiveTests.swift` | `4101a1aadf96f4a85a16c3c882425585fd02df72f84e4ad447e23d9de67b1392` |

Evidence in the isolated worktree: `tmp/nov5-split-progress-red.log`,
`tmp/nov5-split-progress-green.log`, `tmp/nov5-progress-layout-scoped.log`,
and the retained optional operator logs. No live model or user document was used.
