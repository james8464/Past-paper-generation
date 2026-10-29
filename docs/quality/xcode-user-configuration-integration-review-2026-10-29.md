# User Xcode configuration preservation

Date: 29 October 2026. Integration is isolated on
`main-xcode-and-validation-follow-up`, based on protected main
`63964360`. This record does not certify a new release or App Store approval.

## Preserved changes

The user's primary edits were preserved separately in stash
`149319c68452b9b18fbdd0da8a656b4f669d0105`. The primary checkout was not edited
by this integration. Its current Xcode project was imported without regenerating
or normalising the user's project format: object version 110, Xcode's script
array/omitted defaults and comments remain. Both application configurations keep
marketing version 2.0, personal team `Z29CKRV8C9` and inclusion of all icon assets.
Those three meaningful settings are also in `macOS/project.yml`, so CI's
generation step does not silently restore version 1.0 or discard the team/icon
settings. Existing explicit Info.plist display-name/category values are not
removed. Bundle identity, build number, distribution defaults, entitlements,
sandbox selection and hardened runtime are unchanged.

The three tutorial asset manifests retain the user's empty 2x slots. These are
placeholders, not new higher-resolution screenshots. Existing named 1x images
remain. The user's unrelated AppTests whitespace and the separately owned
DocumentPreview initialiser change were not imported by this task.

## Complete catalogue preservation proof

The catalogue was parsed in full and every entry/localisation value was compared
structurally, rather than treating a large textual diff as translation changes.
The comparison uses immutable main and saved-stash blobs, not a moving primary
file. During integration the primary catalogue changed from 615 to 608 keys;
that transient copy was detected and not accepted as the final catalogue.
The isolated catalogue was reconstructed from the immutable union instead.

- Main `63964360`: 587 string keys.
- Saved stash: 606 string keys.
- Final isolated catalogue: exactly 615 keys, equal to their set union.
- All 606 saved entry objects are preserved exactly as parsed JSON, including
  their Xcode metadata. Saved entries take precedence on overlap.
- Every main key remains. Every localisation `value` leaf from both inputs is
  unchanged, including all French values. No new translation wording was authored.
- Full top-level structure is retained: English source language, version 1.1.
  There are 524 entries with localisations, comprising 522 French and two English
  localisations; ten entries have generated comments and 67 extraction states.

Proof output is retained at
`tmp/xcode-user-integration-catalogue-proof.log`. This is a complete structural
preservation check, not a new linguistic review of all translation wording or
proof that every UI string has a translation.

## CI signing boundary

A personal default team must not cause account/provisioning requirements on a
fresh GitHub runner. Both CI native test and Store-preflight make invocations now
pass `SIGNING_IDENTITY=- SIGNING_STYLE=Manual`. Existing Makefile forwarding and
recursive command-line variable propagation are unchanged; no signing override
was added to normal personal-development builds.

Two config regressions failed before these arguments were added. The focused
signing and release-compliance gate then passed eight tests in 4.20 seconds:

- `tmp/xcode-user-integration-ci-signing-red.log`
- `tmp/xcode-user-integration-ci-signing-green.log`

`xcodebuild -showBuildSettings` completed for Debug and Store-mode Release with
the same ad-hoc/manual settings. Both reported `CODE_SIGN_IDENTITY = -`,
`CODE_SIGN_STYLE = Manual`, the personal default team and
`PROVISIONING_PROFILE_REQUIRED = NO`. Store-mode additionally reported
`ENABLE_APP_SANDBOX = YES`. Logs:

- `tmp/xcode-user-integration-ad-hoc-settings.log`
- `tmp/xcode-user-integration-store-ad-hoc-settings.log`

These commands inspect expanded settings; they do not build, sign, archive or
prove hosted-runner success. No account was added, certificate created,
provisioning requested, security control weakened or artifact uploaded. Parent
review, complete native/Python tests, signed builds and protected CI remain
separate gates. Scoped Ruff lint/format and diff whitespace checks passed.

## Exact reviewed bytes

The project, project-generation source, workflow, regression test and all three
small asset manifests were read completely. The complete catalogue was parsed
and compared at entry/value level as described above, without claiming a fresh
translation-quality review. These hashes identify the snapshot, not an
authenticated review record. This task changed no ledger, Graphify output or
inventory; CI/project bytes need separately refreshed review records.

| Path | SHA-256 |
| --- | --- |
| `macOS/Keldin.xcodeproj/project.pbxproj` | `fc4b5fafc75144eda64c08116d6e81b4a6c9a5541e448b186f0a41286225ae60` |
| `macOS/project.yml` | `b0cc270fead9c252d049a7ba69b1fcf55753276f55ea28e956ef821fa61fb447` |
| `macOS/Keldin/Localizable.xcstrings` | `c882d9f34a01a3ebb540a5c7c6a0091efee168b194f220b8abd44aab88578b78` |
| `.github/workflows/ci.yml` | `89936087ca96ee8c80cddf52f08b354877aa8c989198e6a1311889030e4ca78c` |
| `tests/test_ci_signing.py` | `9df52f55d86e9e9c29810ee5030b2caa82986a78a4378d347ea750eb8827ae9a` |
| `macOS/Keldin/Assets.xcassets/TutorialFrenchNSI.imageset/Contents.json` | `fbd0dd4e1b8bbffca045bd3579b1300bf8ab93a93a0625c0b8cc766867b4c871` |
| `macOS/Keldin/Assets.xcassets/TutorialModelSettings.imageset/Contents.json` | `8aceca0b11e8bacf6107a2bad94d3b83082b96f778062a8df5bbb9b85e7bf0fb` |
| `macOS/Keldin/Assets.xcassets/TutorialWorkspace.imageset/Contents.json` | `ed3ad5ef824d8d243698f84b9c36ba57c8ed86a2fe7e96faf9e95977614f56fa` |
