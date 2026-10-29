# Native release safety review, 29 October 2026

This review covers numeric input bounds, credential-clear recovery, MLX setup copy and document selection. It does not certify the whole application, HIG compliance, paper quality or App Store approval. Graphify queries preceded the source reviews. The macOS SwiftUI and localisation skills guided the selector work; the humanizer skill was used for this report's prose.

## Findings and changes

### Numeric bounds

A model ID containing an unrepresentable number before `b` reached an unchecked `Double` to `Int` conversion in `GenerationEstimator`. A single-test subprocess reproduced the fatal overflow. The size-hint parser now accepts only finite values below the integer conversion boundary; other IDs use the existing neutral estimate.

Native benchmark verdicts are held in memory, not read from a cache. The normal Python producer calculates bounded scores. Swift's default JSON decoder rejects nonfinite JSON numbers, but finite `1e100` and missing scores previously reached the verdict path without range validation. `BenchmarkVerdict.validatedScore` now defines the finite `0...1` contract used by the parser, benchmark owner and estimator. Invalid protocol scores produce an error instead of a result; direct typed invalid events also clear the result. Valid zero and one remain unchanged. Samples and individual metric validation were outside this change.

The new invalid-score message uses the existing finite benchmark-copy lookup with an English/French catalogue entry. Unknown system and backend diagnostics remain verbatim.

### Credential-clear recovery

A partially failed explicit clear leaves an empty current-service marker to prevent an older credential from returning. Previously, reopening Settings treated that marker as an ordinary empty value, losing the pending failure and skipping an unchanged-empty retry.

Reading an existing marker now attempts to finish the prior clear without reading the legacy value. A further failure reports `incompleteClear`; only that marker-specific failure establishes a known-empty baseline in `SettingsStore`. An explicit retry can then finish cleanup. A generic failed read still has no baseline and its empty UI placeholder cannot erase an inaccessible key. Tests use an injected fake Keychain, including denial on both the original clear and the reopened store. No personal credentials were accessed or deleted for this review.

### MLX setup copy

The direct-build explanation promised runtime installation although the frozen helper refuses runtime package installation. Both bundled distributions now share selected-language copy describing a support check and model download/preparation. Tests verify English and French, preserve the chosen model ID and reject the old installation/Terminal/password promises. This copy change establishes no new model-quality claim.

### Document selector and immediate actions

The old segmented picker created one segment for every retained PDF. A hosting test measured a 30-document control spanning approximately `-1602...1922` points in a 320-point proposal; the 60-document case was wider still. The selector is now a bounded menu with stable `GeneratedFile.id` tags. Labels show the localised role, stored subject and paper, and a locale-formatted timestamp. Full paths remain available through help. Tests cover 30 and 60 documents at 320- and 900-point proposals through the public `NSHostingController.sizeThatFits(in:)` API. A segmented reference still exceeds those proposals. The PDF region explicitly accepts the available width and height.

The parent agent's candidate UI pass found that the menu fitted a 30-document library at full and half window width and that the PDF visibly rendered. Export showed the selected question-paper filename and was cancelled. An immediate batch of an accessibility menu-item click followed by Command-P showed the previous 24-page scheme; a later invocation showed the 36-page subject. That batch did not acknowledge a completed selection before printing. A keyboard-menu attempt also selected an unintended older document. These tool sequences do not establish a hardware-event race or prove that the final setter had run before Print.

The source separately allowed the picker binding to change view state and wait for SwiftUI's deferred `onChange` to update the action controller. Its setter now resolves and loads the new document and provenance before publishing the new selection. A deterministic test switches between temporary 24- and 36-page PDFs and checks the immediate action target and matching provenance without running the view loop. Another test switches to an unreadable PDF and confirms that the previous document is no longer actionable. The existing external-change observers and scene-focused document actions remain in place. This proves setter-to-action synchronisation, not the ordering of unacknowledged accessibility inputs.

The parent launched the updated Debug candidate at its exact path, confirmed
the running process path and frontend hash, then confirmed each selected menu
value before pressing Command-P. The newest scheme showed all 24 pages and the
newest question paper all 36; both panels were cancelled. Immediate input batches
still returned before menu selection was visibly acknowledged, so those batches
are not claimed as accepted selection-to-print sequences. The candidate was
normally quit after restoring Benchmark navigation. The installed PR116 copy
remained idle; these observations concern the candidate, not final installed
Release acceptance. No paper generation, history deletion, export, print or
clipboard change occurred in this follow-up.

## Test evidence

All paths below are retained local evidence under `tmp/` unless stated otherwise. These focused results do not replace the final frozen-source full suites or signed Release builds.

| Evidence | Result |
| --- | --- |
| `release-safety-estimator-red.log` | Isolated single-test host terminated with the expected integer-overflow fatal error; exit 65. |
| `release-safety-recovery-copy-red.log` | Two tests, 12 assertion failures before credential/copy fixes. |
| `release-safety-native-green.log` | 131 tests passed after the initial fixes. |
| `benchmark-score-boundary-red-2.log` | Two tests, 16 assertion failures for parsed and typed invalid scores; valid boundary cases already passed. |
| `release-safety-boundaries-green.log` | Superseded: three assertions used old test fixtures whose supposedly valid score was `2`. |
| `release-safety-boundaries-final-green.log` | 173 tests passed after valid-result fixtures changed to `0.8`; stale callback and process-ownership assertions retained. |
| `document-selector-red-2.log` | Three tests, 17 assertion failures for overflow and missing contextual/localised labels. |
| `document-selector-final-green.log` | 114 tests passed, including hosting, PDF access and existing document action/provenance coverage. |
| `document-action-race-red.log` | Three tests, six assertion failures for immediate selection/actions and untranslated invalid-score copy. |
| `document-action-race-final-green.log` | 122 tests passed, including immediate 24/36-page target and provenance changes, unreadable selection, and English/French failure copy. |

The first selector RED exited unexpectedly after closing its test windows. The second RED disabled release-on-close and completed normally; no production crash is inferred from that test attempt. The first selector GREEN assumed the menu would expose an `NSControl`, which SwiftUI did not provide. The final hosting tests use the public sizing API instead. Those superseded attempts remain retained and are not acceptance evidence.

The latest tested Debug bundle is `macOS/build/DerivedData/final-native/Build/Products/Debug/Keldin.app`. Its frontend SHA-256 is `cd68a75828174ea43957ad7a1759d2c04317275ad284a62b3394d70f2d26ec33`. Strict deep signature verification passed; proof is in `document-action-race-final-debug-signature.log`. This bundle has not been installed or launched by the reviewing agent. The earlier `document-selector-review` Debug candidate predates the timing fix.

## Source review boundaries

The complete files below were read in full, with the changed small files reread after their fixes. The unchanged lifecycle files retain the exact bytes read at merge `4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`; their hashes were checked again. Scope includes process ownership, cancellation, numeric conversion, persistence ordering, credential failure handling, recommendation loading, document layout, access and action selection. These are file-level review records, not a statement that every possible runtime input has been tested.

Paths are relative to `macOS/Keldin/`.

| Complete file | SHA-256 |
| --- | --- |
| `State/ModelCoordinator.swift` | `05c5978a2f6fdb87606d27e7575656eabeb82f669308167720990c40aad5abce` |
| `State/GenerationCoordinator.swift` | `f44c66928bcf6704f6a18f17ee3bc58d1bdd409dda069f25326e8be12a7b93f4` |
| `State/CoordinatorDependencies.swift` | `fc4057732cd30726d63b05421e3c9b99dddd8974ea6086a1202c3cab57e7dd1e` |
| `Domain/OllamaModelGuide.swift` | `83dd834ae716938cc6c411aee53ca787725d12e73975c55a0c93852cc0cb637f` |
| `Domain/GenerationPresentation.swift` | `f052887636900acf853028234faff96d92791f7f56c5a36c209c2d42a643c3b2` |
| `State/BenchmarkCoordinator.swift` | `5ec7c28f8d854a129fe810841552bca2a6c6b42e45ea6d27b65b901dba336c62` |
| `Domain/GenerationEstimator.swift` | `092d2dbe57041a1d9375188dd8acade7989b7bf6554fe9b9f87598a3a2d485e7` |
| `Services/SecretStore.swift` | `3da69c3a41ee181b5319a078b27596053363962e72e8be3a12335953676396a1` |
| `State/SettingsStore.swift` | `a6f639f5dc3debb97502e4d1a3d2d4ce6cd96ac38065b0e43d2716ea4db2f528` |
| `Features/Documents/DocumentPickerView.swift` | `ae0ade372f695386a80562fd28733db16f1bd38b44f7f7dfca5081b0fa1083c6` |
| `Features/Documents/DocumentPreviewView.swift` | `4bd19687181d66d1271cbe55600e3e8903dbe85b2caa9670fb5aeb043bcd3f3f` |

The following larger files or catalogues received only the stated patch review. Their hashes identify those revisions and must not be used to claim a complete-file review.

| Patch-only file | Scope | SHA-256 |
| --- | --- | --- |
| `Domain/AppModels.swift` | `BenchmarkVerdict` validation and `benchmark_done` decoding. | `15755dc8591009dd46c779351dc9c669d563bce7fc02bcbd4d685eb29f110f31` |
| `State/ApplicationCoordinator.swift` | `mlxSetupExplanation` copy and selected-language resolution. | `2cbe2594adf3526de0b094d07878f852f485c01edc1bc94e5eaefad6d2f1a15d` |
| `Domain/NativeInterfaceCopy.swift` | Finite invalid-score message mapping. | `2ea2567a657c5cbc4ab30d111ab7771ba0f6af4a88eb6478c38470ad28e4f1a0` |
| `Features/Benchmark/BenchmarkView.swift` | Selected-locale resolution of finite failure text; unknown diagnostics unchanged. | `b1d923c4e77dc94bb1312293d6b3520d31da2d5ed53cb87f3964af95a86c1349` |
| `Localizable.xcstrings` | New MLX explanation and invalid-score English/French keys. | `7dd8944513651f6a36e33399ab5c7f858df469aeb360bc96308758e127637093` |

Tests ran against temporary files and isolated preferences with fake credential/backend dependencies. The parent agent owns the real UI observations and remaining candidate acceptance. No teacher records, learner timing observations or external approvals were created by this work.
