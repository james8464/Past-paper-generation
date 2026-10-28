# Native identifier integration

This package selectively integrates the native identifier changes from
`31ec4cd14bd442a29050ceed7ac2ff97833bb517` onto the current PR112 source,
`eb68350`. It does not copy old branch files or integrate that commit wholesale.

## Scope

- `PaperCreationContext` becomes `KeldinCreationContext`, with its file renamed.
- The focused-value key and property become `KeldinCreationContextKey` and
  `keldinCreationContext`. Current menu and UK/French workspace callers use them.
- `PaperCreationTips` becomes `KeldinCreationTips`, with its file renamed and
  current workspace callers updated.

The current busy-state, document-command and selected-language bodies remain
unchanged. The context still distinguishes UK creation from French normal and
enlarged print, with the same readiness and busy guards. The original TipKit
conformer names remain `ModelRecommendationTip`, `PreviewTip` and `QualityTip`;
their persisted tip IDs are checked directly by a native test.

No bundle identifiers, user-default keys, document/history bytes, public backend
APIs or migration aliases change. Generic wording such as “paper creation” is
not treated as a former brand. Optional copy changes, broad comment edits,
historical French modules and the Edexcel package rename are excluded.

## Evidence

This is a rename-only integration, not a newly reproduced runtime defect.
The renamed context and tip files match their baseline bytes after replacing
only the respective type name. Their SHA-256 values are:

- Context: `68fd4f133a73ca8993a3d9e8b20ca20199d4b92dc70aec6bc74711bf4b156925`.
- Tips: `9f1391b54ce295efb98ad7f4de49f6f0a46a4fb3a6ae15399338ef8d44021f7a`.

The first compile attempt rejected a proposed test fixture because SwiftUI's
`FocusedValues` initializer is internal. That unsupported synthetic fixture was
removed; production focus routing was not changed to accommodate the test.
The log is retained at `tmp/compatible-native-brand-names-green.log`.

The final targeted native gate passed 85 tests: 55 application tests and all
30 run-isolation tests, with warnings treated as errors and strict concurrency
checking. Existing context readiness/print-choice checks were retained, and the
new test verifies the three original TipKit IDs.

- Log: `tmp/compatible-native-brand-names-final-green.log`.
- Result: `macOS/build/logs/compatible-native-brand-names-final/test.xcresult`.

This targeted compile/test pass does not replace the parent's full native,
release-signing, native interaction or protected CI gates. No full-app,
whole-HIG or paper-quality approval is claimed.
