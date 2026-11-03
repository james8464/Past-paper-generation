# Sidebar preference stability

## Reproduction and fix

`WorkspaceSidebarPolicy.columnVisibility` previously saved a fixed preference
when its setter received the same visibility its getter already returned. An
automatic wide layout could therefore become permanently `all`; an automatic
compact layout could become permanently `detail`. Subsequent resizing would no
longer use the app's automatic layout policy. Repeated callbacks also wrote the
same preference unnecessarily.

The regression exercises twenty unchanged callbacks in each of the compact,
standard and expanded layouts. Before the fix it failed nine assertions in one
test. The fix shares one pure visibility resolver between getter and setter and
returns without writing when effective visibility has not changed. Actual
changes still save. A second test checks the existing explicit `all`, `detail`
and `double` preferences, including one real change after the repeated callbacks.

Apple documents visibility as a binding used by the split view:
[NavigationSplitViewVisibility](https://developer.apple.com/documentation/swiftui/navigationsplitviewvisibility).
This fix preserves the app's existing width thresholds and stored preference
format; it does not add a new navigation mode.

## Review and verification scope

The author read `NativeVisualStyle.swift`, `SidebarView.swift`, `ContentView.swift`
and `CatalogStore.swift` through EOF. An independent internal reviewer checked
the proposed semantics and red regression before implementation. The full native
suite executed 425 tests, with three skips and zero failures. Local logs are
`tmp/nov3-sidebar-red.log` and `tmp/nov3-sidebar-green.log`. The final production
file SHA256 is `1db48b8dfbdfd36d2b958568c766cf0741b929fd139e0d75e4d4f86d64cc71ab`.
The author reread that final file through EOF. Independent review of the final
source/test delta found no P1/P2 issue. All 39 repository inventory and audit-ledger
tests and the release-compliance metadata checks passed. Protected checks and
native interaction acceptance remain separate release gates.

This is not a proven repair for the earlier 32.5 GB memory hang. The retained
sample places activity in SwiftUI's outline coordinator, but does not identify
the responsible application callback. No settings, history or saved documents
were reset. No paper source, model prompt, validation threshold or film changed.
