# Local PDF admission

`PDFDocumentAccess.load` now rejects non-file URLs before reading bytes, resolving a bookmark or starting a security-scoped lease. It releases any existing reader lease and returns the existing `.invalid` failure. Regular file URLs follow the unchanged reader and recovery path.

The prior route was reachable through a persisted `GeneratedFile`: decoding accepts a URL, the document picker filters its PDF extension, and the controller calls `load` before checking action availability. A remote URL could therefore reach the default synchronous `Data(contentsOf:)` reader. This finding does not establish the cause of any separate memory incident.

## Evidence

The owned standalone probe compiles the exact production access service with injected collaborators. HTTPS and data URLs each failed before the change: the reader, bookmark resolver and scope-start closure were called once. After the guard, both cases return `.invalid`, all collaborator counts are zero and saved bookmark bytes remain unchanged. The probe makes no network request and uses a UUID-named defaults suite that it removes on exit.

Retained files are under `tmp/nov4-local-pdf-boundary/`: `probe.swift`, `red.log` and `green.log`. Both builds used Swift 5, complete strict-concurrency checking and warnings as errors:

```sh
swiftc -swift-version 5 -strict-concurrency=complete -warnings-as-errors -parse-as-library macOS/Keldin/Services/PDFDocumentAccess.swift tmp/nov4-local-pdf-boundary/probe.swift -o tmp/nov4-local-pdf-boundary/probe
tmp/nov4-local-pdf-boundary/probe
```

Three new XCTest methods cover both URL schemes, unchanged bookmarks, balanced prior-lease release, repeated release and a controller transition from a valid local PDF to a remote URL. The controller must clear its loaded PDF, report `.invalid` and disable document actions without another read. These XCTest cases have not been compiled or executed in this authoring lane; combined native and release gates remain the integrator's responsibility.

## Review scope

The author read all 150 baseline service lines and the four-line guard. Persisted-document restoration, document selection and controller refresh callers were inspected selectively, along with relevant existing tests and all new test code. The test file has not received a new whole-file semantic attestation.

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/Services/PDFDocumentAccess.swift` | 154 | `bc5c74e52a3f34627e8f28b8ba5b734a0669131758ca648e528f7571758b6221` |
| `macOS/Tests/PDFDocumentAccessTests.swift` | 597 | `61fe311e5c4ceab72f2f3ef9d198a2863e51a71b979e74f804275e49cb36626d` |

No installed app, canonical history, user PDF or preference was changed. This repair adds no network fetching, concurrency architecture or sandbox entitlement. Native UI behavior, general PDF resource limits and complete application security remain outside this evidence.
