# Bounded release configuration review

Date: 29 October 2026. Reviewed on `main-release-safety-audit`, based on merged
`4427e1c642c5ffe36eb26f9529eae5bd3ea0652e`. Graphify was queried first; the 18
files below were then read completely, totalling 575 lines. Their ledger status
was pending when selected. This report records source review, not an
authenticated attestation or whole-project clearance.

## Contracts inspected

- The Graphify hook defines a development-tool command only. Its availability
  depends on the developer's installed Graphify; it is not an application
  runtime dependency. No hook was executed as a release acceptance check.
- CODEOWNERS applies repository-wide ownership. Issue forms have stable unique
  field IDs and required reproduction/problem fields. The bug form asks users
  to remove personal data and API keys; the improvement form warns against
  uploading copyrighted reference papers. The private-disclosure link is a
  source configuration, not proof that GitHub's private reporting is enabled.
- Dependabot is scoped to weekly GitHub Actions updates. It does not promise
  Python dependency monitoring or automatic release acceptance.
- The macOS ignore file excludes local builds, agent selection and Xcode user
  state. Project configuration includes the app/test targets, shared scheme,
  resource manifests and standalone-backend prebuild script. Its defaults are
  direct distribution. Existing Makefile Store targets explicitly override the
  distribution mode, sandbox flag and entitlements file. The prebuild script's
  dependency analysis is disabled, so its abbreviated input list is not being
  mistaken for a complete incremental cache fingerprint.
- The workspace references its containing project. Shared scheme references
  consistently identify Keldin and KeldinTests, with Debug test/run/analyse and
  Release profile/archive configurations. This source inspection did not run
  Xcode, regenerate the project or verify an archived binary.
- Branding metadata describes independent artwork, a warm palette and no Apple
  endorsement. Icon Composer configuration references seven existing SVG
  components. The legacy icon catalogue lists existing macOS size/scale assets.
  Accent colours have default, dark, increased-contrast and combined variants.
  Tutorial image manifests reference existing named images; the catalogue root
  uses the ordinary Xcode metadata contract.

No additional confirmed defect was found within these files. This is not a
visual evaluation of the raster artwork/tutorials, contrast measurement,
whole-HIG certification, signing/entitlement verification, legal clearance or
Store approval. Asset file existence was checked, but referenced binary image
bytes and SVG contents were not part of this 18-file complete-read batch.
No production file, test, coverage ledger, Graphify output, inventory or prior
review report was changed. No tests, builds, models or cleanup scripts ran.
The broader implementation audit remains incomplete.

## Reviewed byte identities

These SHA-256 values identify the actual completely read files. They are
evidence for a later review-record refresh, not themselves an authenticated
review record.

| Path | SHA-256 |
| --- | --- |
| `.codex/hooks.json` | `3847c5f5ccd075d965728ee0d497e74b6b76ff8f080f0cb9081b39e9ca382311` |
| `.github/CODEOWNERS` | `84b78abad959192c67d3ac7c433e333bf6cfd63ca756d335ac962c45b964a42e` |
| `.github/ISSUE_TEMPLATE/bug.yml` | `8b6f233103aa0e09548445ecad065a2b848494d7b9533b56314c8eeda47c5345` |
| `.github/ISSUE_TEMPLATE/config.yml` | `abc40854e7671a899bf3396ef0b65bfadf28e28c55b0dcc6ac68cbf51ed33594` |
| `.github/ISSUE_TEMPLATE/improvement.yml` | `4a5fcc2b07c2719071da6cd12ac78618fe1c9a4a94bb05c161445a1d33dc8be1` |
| `.github/dependabot.yml` | `5e54c7e473646e7b15345ac8dc7749922495be1cac57135cdf3cde5e4d20911f` |
| `macOS/.gitignore` | `7a57880ddd4081712335c6d56fba80beb420892c1c293accb2ed3679c4b51e7b` |
| `macOS/project.yml` | `74d205ac5bb761deeda3fae18e4bd2012161af3f6876ad2ee3c50cf2816ec40c` |
| `macOS/Keldin.xcodeproj/project.xcworkspace/contents.xcworkspacedata` | `7f3b00b5c3fdb45242d7b87e1e5c4e25d1fa8129a16c94295ecc4e8ea2235c5f` |
| `macOS/Keldin.xcodeproj/xcshareddata/xcschemes/Keldin.xcscheme` | `f8484b40ca716ee2382d90cdfda2f2efb3c82a1da1ac0eb60e7b59fe4294559b` |
| `macOS/Branding/icon-design.json` | `2bfd35ff333f20cdba1229868bbd25f0b55beffed119dcc2e0d73732c6b25946` |
| `macOS/Keldin/AppIcon.icon/icon.json` | `6a4ab129fb75fb17704bae146a7ecb023d34bafe9492aac9dbcded9dc7f12122` |
| `macOS/Keldin/Assets.xcassets/AccentColor.colorset/Contents.json` | `2e1ef28e55fc721e195b1f0aa7caddf27b489eb4bc38f95a0a298d0eeff76874` |
| `macOS/Keldin/Assets.xcassets/AppIcon.appiconset/Contents.json` | `84b151d2ff91504e722d6d188de9d9b4a56e733b3b4346c641fc676b3a939b3e` |
| `macOS/Keldin/Assets.xcassets/TutorialFrenchNSI.imageset/Contents.json` | `ece220a9828d29e503bf10663425ceb037e75b42d0c305acb4c73319a72b6cd2` |
| `macOS/Keldin/Assets.xcassets/TutorialModelSettings.imageset/Contents.json` | `40cbe15d250ed72122bec9eda99bcc86c55c836d015d4fd85a2156a914dd542d` |
| `macOS/Keldin/Assets.xcassets/TutorialWorkspace.imageset/Contents.json` | `28642d4b6d299eef7618b88f4cac866c060c9ed11406c4c267d024252eaed641` |
| `macOS/Keldin/Assets.xcassets/Contents.json` | `0fd49ba3c3585c709678e0046a821c3c60685ec7063720d30d3a3448be3a208b` |
