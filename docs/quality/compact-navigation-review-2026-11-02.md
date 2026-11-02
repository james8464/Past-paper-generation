# Compact navigation review, 2 November 2026

## Defect and repair

The previous ContentView forced the sidebar hidden below 840 points and ignored visibility writes. The main window permits widths down to 720 points, so the normal Show Sidebar action could not reveal the only subject, board and French-workspace selector in that range. Native baseline testing at 760 points confirmed that Show Sidebar did nothing; the diagnostic ended with two failed assertions for French selection and persisted visibility.

The candidate routes the real ContentView binding through a small WorkspaceSidebarPolicy. An unset automatic choice initially collapses compact windows and shows the sidebar in wider windows. Explicit all, double-column and detail-only choices persist and apply at every width. The minimum window width remains 720 points. Generation ownership, progress, cancellation and navigation routes are unchanged.

Two focused native binding tests first reproduced 14 failed assertions with the original predicates. The repaired author suite passed 142 tests; two opt-in interaction checks were skipped. A separate English/French Help-route regression first failed for the missing French resource, then its focused suite passed 72 tests. These tests are not full interaction coverage.

## Native geometry evidence and pending acceptance

The first candidate interaction successfully revealed the sidebar and selected French while preserving the controlled active job. macOS grew the window from 760 to about 904 points when revealing the sidebar. The original test required the final width to remain below 840 even with the sidebar shown, so that run failed its width assertion and is retained. It is not recorded as a pass.

Further native inspection confirmed that the window content minimum remains 720 points. The final acceptance journey starts compact, records its geometry and minimum, reveals the sidebar, selects French, hides the sidebar, and uses the normal macOS Window > Move & Resize > Left action to return to about 757 points before finishing. The final gate still requires width below 840, unchanged minimum, French selected, persisted detail-only visibility and the original active job. It no longer requires macOS to retain a compact width while displaying the sidebar.

That final native acceptance is running and has not yet been recorded as passed in this document. Protected checks, aggregate tests and installation are separate release gates. This repair does not prove every native interaction or full HIG compliance.

## Retained evidence

- Original native baseline: identifiers worktree `macOS/tmp/nov2-compact-baseline-ui.log`, diagnostic `f1f6e8dc28115be3785b90bf599cf4f1be53d329` based on the old production source.
- First candidate and failed width assertion: capacity worktree `tmp/nov2-compact-sidebar-ui.log` and `macOS/build/logs/nov1-cancel-history-native/compact-sidebar-ui.xcresult`.
- Author binding and Help red/green logs: documentation worktree `tmp/nov2-manual-import/compact-sidebar-{red,green}.log` and `help-route-{red,green}.log`.
- Final acceptance fixture: `macOS/Tests/GenerationNavigationInteractiveTests.swift` at `fa9d0f4674c32582be1f7c6648bc0d9660d20869`, opt-in `KELDIN_INTERACTIVE_COMPACT_SIDEBAR_CHECK=1`.

All checks use controlled local data and a fake backend. They make no live model request or paper-quality claim. No accessibility testing was performed. The original failed runs remain evidence rather than being overwritten or relabelled.
