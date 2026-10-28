# Bounded native interface audit

The source review began at `d55b176697624798853f90712b46068f62d2cd34`. It covered eleven maintained Swift files, not the whole app or the complete Human Interface Guidelines. No performance bottleneck was measured.

## Source findings addressed

- The benchmark toolbar started its coordinator directly, bypassing the application's busy checks and discovery-request invalidation. Start and Cancel now use the same application methods as the menus. A retained historical job alone does not incorrectly disable the toolbar.
- Benchmark failures were recorded without appearing in the workspace. The overview now shows the failure, diagnostic detail and a retry action. A nonzero exit no longer overwrites a more useful backend error. Status text uses the semantic primary colour; colour remains on the distinct status icon.
- Remove from Recents changed only the current list. Restoring artifacts from job history made removed entries reappear. A separate standardized-URL exclusion list now survives restart, hides all duplicate entries at that URL and is cleared when a new file event publishes that URL. History records and PDF bytes are not removed.
- Finite dynamic creation, blocker, history, document, empty-state and quality labels now use localizable resources. Quality presentation accepts the selected locale without changing qualification decisions. Benchmark chart summaries use the selected locale for text and numbers. Backend evidence gaps, identifiers and other diagnostic data remain verbatim rather than receiving invented translations.

## Original review snapshot

Paths are relative to `macOS/Keldin`. Hashes are SHA-256 of the reviewed pre-fix files.

| File | SHA-256 |
| --- | --- |
| Application/AppCommands.swift | `314070ee1016ec5f71f3e8b01c3719c50f99b1ebe0a6e1bf15c1a8e1c2d0e3e5` |
| Navigation/ContentView.swift | `1466f2065ad1857d655f6cdc068e6f3655f33cefb2d968de4fa4b5888e4f80fb` |
| Navigation/SidebarView.swift | `2a7e6a883a1a3c58b656db5df1e2ad4df1976b8949af32da7c358e0922e523a8` |
| Features/Generation/GeneratorWorkspaceView.swift | `1019f37e541042059dcc9f21e35f017a2779b335510dadf6dce3426804f015a1` |
| Features/Generation/FrenchAssessmentWorkspace.swift | `e2c7761c945bb004b58103366e058e1c322006e6cc22ba4d60c0b1d140a64166` |
| Features/Settings/SettingsPane.swift | `be5d3c1115b95d1e3fad457f67d8d1704b1c8d8f678a958da3700884436ccae2` |
| Features/Documents/JobHistoryView.swift | `9b569e1fad375de3a06ca26b45f4b7d5a7d8c43dd5dbe74b4cdbf30eadbdf577` |
| Features/Onboarding/PaperCreationTips.swift | `9c66da84b425db71a82e84dceff58fecf9d6b72702e38dacc08402b34453472f` |
| Features/Benchmark/BenchmarkView.swift | `3099a8ea51db68373fccabd2c209c24c65054d45a3f288a58c1ec774aee1da57` |
| Features/Onboarding/WelcomeHelpViews.swift | `20987651c2d2c2edc9dfe4dbe6dad2303c7f31cf0f140eb695892414cba9ec47` |
| Components/SharedViews.swift | `bca7865b3ca2ab5fb863c66c8bc3dd97af8393e6b2c54f096c8462cd65465199` |

ApplicationCoordinator callers were traced for ownership and persistence; this was not another full-file review of that coordinator.

## Targeted evidence

- `tmp/native-interface-audit-red.log`: four tests, eleven assertion failures. This combines deterministic restoration/localisation checks with an explicit source-wiring check, not observed GUI interaction.
- `tmp/benchmark-visible-error-red.log`: one test, one assertion failure reproducing the overwritten failure detail.
- `tmp/native-interface-audit-green.log`: 65 targeted tests passed.
- `tmp/native-interface-audit-final.log`: 70 targeted tests passed.
- Final source: `tmp/native-interface-localized-quality-final.log`, 70 targeted tests passed with zero failures. Result bundle: `macOS/build/logs/native-interface-localized-quality-final/test.xcresult`.

The final set includes five interface cases, 22 process-isolation cases, 40 coordinator cases and three existing quality-policy cases. It checks immediate duplicate removal, restart persistence, artifact/history preservation, explicit URL reuse, English/French state and quality copy, preview and live interpolation, French decimal chart summaries, preserved benchmark errors and retry reset. Existing qualification-policy assertions remain green.

Full native tests, signed Store-mode checks and native interaction testing remain separate release gates. This audit does not claim complete interaction coverage, complete French translation coverage, full HIG compliance or Store approval.

## Finite benchmark copy follow-up

The benchmark protocol supplies four fixed verdict/detail pairs, 24 fixed metric names and five fixed explanatory or unavailable-value messages. The UI now resolves those exact strings through a bounded resource map in `NativeInterfaceCopy`. Unknown backend messages, platform descriptions, processor names, version strings and power-source values are left verbatim.

Metric display accepts the selected locale, retaining the existing zero-to-two-decimal precision and the raw numeric value, score and unit code. Display labels use French `cœurs`, `Go` and `Mo/s` where applicable; no quantity conversion is performed. The thermal-speed measurement remains a percentage, never a temperature. Chart summaries, value labels and axis units use the same display-unit helper. Existing score thresholds and backend verdict decisions are unchanged.

- `tmp/benchmark-finite-copy-red.log`: four tests with 20 assertion failures before the copy and formatting changes.
- `tmp/benchmark-finite-copy-green.log`: 31 targeted tests passed, zero failures. Result bundle: `macOS/build/logs/benchmark-finite-copy-green/test.xcresult`.

The final set covers all eight verdict/detail strings in English and French, all 24 metric labels, all five fixed helper messages, unknown/OS values, raw-field preservation, French decimals and display units, and unchanged thermal-percentage meaning. The five interface and 22 process-isolation cases remain green. No backend benchmark code, solving code, full suite, signed release build or new performance measurement was included in this follow-up.

## Combined frozen-source gates

At `f83165e109929e5e70e0cfe72231dabb48ab4100`, the full Python suite
passed 4,239 tests with two skips in 546.48 seconds. The full native suite passed
205 tests with no failures. Personal-development-signed Store Release preflight
and strict signatures also passed. Retained logs are
`tmp/native-ui-final-full-suite.log`, `tmp/native-ui-final-native-tests.log` and
`tmp/native-ui-final-store-preflight.log`.

These results include the separately reviewed P7 calculation-handler refactor.
Later direct-release interaction and protected publication need their own actual
results. No live model qualification, teacher evidence, full HIG compliance or
Store approval follows from these engineering gates.

## Actual system app-language follow-up

The PR111 direct Release was opened with a temporary macOS app-only French
language override. The NSI workspace and menus translated correctly, but the
benchmark title, Results heading, launch button and initial explanatory text
remained English. The catalogue entries were empty. Seven resource assertions
failed before the translations were added; the combined 83-test ownership and
benchmark gate now passes. Score/progress accessibility resources were included.

macOS initially relaunched a different registered candidate. That copy was closed
before explicitly opening the exact tested primary Release, so the observed
benchmark finding is tied to that build. No paper was generated. Afterwards the
candidate was closed, the temporary override removed and System Settings returned
to General. The app-language override list is again empty; English (UK), region,
units, provider/model, credentials, output settings and saved papers were retained.
Detailed observations remain in `tmp/french-system-language-native-20261028.md`.
Fresh native verification of the corrected labels and final release gates remain
required. This bounded check does not establish complete translation coverage.

The corrected direct Release subsequently completed an actual benchmark in
French. Its title, launch/cancel controls, progress accessibility label, result
heading and verdict translated. That run exposed three further untranslated
table headers. Three assertions then failed before their catalogue fix. The
final direct Release completed another benchmark and displayed Mesure, Valeur,
Score and Détail. OS-reported values remain verbatim; number formatting retains
the user's UK region. No paper or model was downloaded or generated.

The final full native suite passed 214 tests with zero failures. The signed
Store-mode preflight and direct Release build passed, with strict signatures.
Thirty repository/branding/coverage checks passed; an earlier mistyped test path
ran no tests and is retained separately, not counted as acceptance. Logs are
`tmp/owned-operation-final-headers-native.log`,
`tmp/owned-operation-final-headers-store.log`,
`tmp/owned-operation-final-headers-direct.log` and
`tmp/owned-operation-hygiene-green.log`. Core source matches merged PR111.

An unexpected one-line Core comment edit was found between earlier gates and a
later resource red run. Its proposed wording was preserved separately before
restoring the exact committed bytes; the writer was not established. The final
gates above ran after restoration. No historical identity check was relaxed.
The candidate is closed and the temporary app-language override again removed.
