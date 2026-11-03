# Test preference cleanup

Eight test fixture creation sites made unique `UserDefaults` domains without
registering domain cleanup. They now use the existing `isolatedDefaults()`
helper, which registers `removePersistentDomain` in an XCTest teardown block.

- `HistoryDeletionTests.swift`: three fixtures.
- `StorageLocalizationTests.swift`: two fixtures.
- `NativeInterfaceAuditTests.swift`: two fixtures.
- `PDFDocumentAccessTests.swift`: the shared `defaults()` fixture factory.

Each fixture still gets its own fresh domain. Tests that construct several stores
or application instances with the same fixture continue to share that one
instance until the test finishes. Cleanup does not run between those instances.
No assertion, test input, application source, production preference key or user
document changed. This is test-lifecycle maintenance, not a change in app behavior.

A separate read-only count found 30,861 old `KeldinTests.UUID.plist` files. These
eight creation sites used different prefixes, while the existing `KeldinTests`
helper already registered teardown. That count is therefore not attributed to
these sites. Domain removal is not a guarantee of physical plist removal, and
historical files were not opened or deleted by this work.

The first scoped run passed after five replacements. The final eight-site native
suite executed 423 tests, with three skips and zero failures, as recorded in
`tmp/nov3-test-preference-cleanup-final.log`. Independent review of all eight
replacements found no issue. This branch is based on main165; PR166's two sidebar
regressions will also be rerun after integration with that separate change.
No inference request, GUI action, preference reset or cleanup of real history was
performed for this change.
