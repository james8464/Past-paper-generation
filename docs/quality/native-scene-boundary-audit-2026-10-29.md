# Native scene boundary review

## Full-file review scope

The parent reviewer read the complete final versions of the six files below,
including the pending-modal follow-up at `36d048da`. The implementation reviewers
also examined the changed Settings, menu and coordinator call sites. Those scoped
diff reviews do not imply a full-file review of the larger callers.

| File | Review and disposition |
| --- | --- |
| `macOS/Keldin/Application/KeldinApp.swift` | Reviewed launch/test-host separation, scene ownership and the value-keyed Main window. The stable primary value keeps menu-open requests directed at one logical Main scene. Existing test-host defaults avoid real Keychain access. Optional TipKit setup still tolerates failure. Migration errors and Main presentations retain their existing flags. |
| `macOS/Keldin/Application/MainWindowRouting.swift` | Reviewed all routes and action ordering. Pending Main presentations reopen their host without another route mutation, dialog or benchmark. Normal benchmark routing selects and opens its destination before starting work. No view/window object or closure is stored in a focus key. |
| `macOS/Keldin/Domain/KeldinCreationContext.swift` | Reviewed model-free French readiness, enlarged-print selection and disabled modal contexts. Main-owned blocking applies to focused Main; Settings dialogs block their own scene. Recovery routing still refuses new work until the retained Main prompt is resolved. |
| `macOS/Keldin/State/ModelDownloadPresentation.swift` | Reviewed immutable request IDs and model snapshots, visible/dismissing phases, matching consumption and replacement safety. An invisible dismissed request cannot disable commands; explicit cancellation and host disappearance consume the matching request. |
| `macOS/Keldin/State/SettingsActionPresentation.swift` | Reviewed inactive/idle/presented/dismissing transitions, stale callback rejection and error retention. Closing the host discards pending consent but retains errors for reopening. Deferred errors do not overwrite the visible request or flood alerts. The service stores no native window or view. |
| `macOS/Tests/MainWindowRoutingTests.swift` | Read all five tests and the protocol fake. They check all eight pending-modal routes, normal ordering, benchmark visibility ordering, stable repeated identity and restoration coding. These are routing tests, not proof of actual window reuse. |

## Regression evidence

The original Settings-only download failure was observed through computer
control on PR114-byte app builds. Consent and persistence-origin regressions then
failed against the old behavior. The router pending-modal regression reproduced
eight assertion failures across five tests before its guard.

The combined focused native gate passed 129 tests with no failures:
`tmp/settings-origin-router-green.log`. The scoped Python wiring gate passed
seven tests in `tmp/settings-action-host-python-green.log`; Ruff and diff checks
passed. These results cover more code than the six full-file attestations, but
do not automatically mark other files reviewed.

## Limits

Actual Settings-only/window-reuse verification and final signed builds are
separate release gates. The existing output-folder bookmark failure handling is
unchanged by this package. Main's other presentation flags have not been replaced
with a universal queue. This record does not claim full interaction coverage,
complete localisation, HIG certification, Store approval or faster execution.
