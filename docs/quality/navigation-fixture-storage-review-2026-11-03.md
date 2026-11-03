# Controlled navigation fixture storage

The opt-in `testNavigationDuringControlledGeneration` fixture created an isolated coordinator but did not bind its hosted SwiftUI root to the same defaults suite. Its `ContentView` could therefore use the operator's standard `AppStorage` values. The compact-sidebar fixture already bound its root correctly.

A scoped static test failed against the old second fixture, then passed after adding `.defaultAppStorage(defaults)` to that exact hosted root. The fixture also snapshots the standard language, sidebar visibility and Settings-pane values. It checks they remain unchanged immediately before the manual journey and again after fixture cleanup. The checks never restore or write standard preferences. Existing controlled generation, navigation and document-preservation assertions are unchanged.

The red and green evidence is in `tmp/nov3-navigation-fixture-storage-red.log` and `tmp/nov3-navigation-fixture-storage-green.log`. Ruff and diff checks passed. No native journey or build was run by this author; compilation and native acceptance remain separate gates. No production UI or real user preference was changed.

The author read all 176 baseline Swift fixture lines through EOF and reviewed the entire final delta, plus all 15 new Python test lines. Root reviewed the delta. The resulting hashes bind this test-isolation scope only:

| File | Final lines | SHA-256 |
| --- | ---: | --- |
| `macOS/Tests/GenerationNavigationInteractiveTests.swift` | 192 | `5862e9af2242b1b45282bdbc792a96733f4ed479b6806b2e80e2b1bf511048c9` |
| `tests/test_native_fixture_storage_isolation.py` | 15 | `b3a6d464ffcb8d01261dfeb80adcaff17a48770ebad24faf637f841e22d1ac3f` |

The static test verifies the root binding; it does not simulate SwiftUI preference propagation. The standard-domain assertions execute only when the existing opt-in native journey is run. No broader test-fixture or whole-app isolation guarantee is claimed.
