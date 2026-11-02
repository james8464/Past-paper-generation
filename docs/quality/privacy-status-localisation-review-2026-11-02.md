# Privacy status localisation

The Privacy pane passed several values as plain strings, so choosing French left “Direct Download”, “Not required”, “Accepted” and “Not accepted” in English. The fix supplies typed resources to the content views and binds their locale at display time. Consent storage, distribution behavior and the legacy English diagnostic titles are unchanged. App Store and Keychain remain product names.

The initial focused build failed because the typed APIs were absent. After implementation, all six StorageLocalizationTests passed. The subsequent complete native suite reported 422 tests, three skips and no failures. Logs are `tmp/nov2-privacy-localisation-red.log`, `tmp/nov2-privacy-localisation-green.log` and `tmp/nov2-privacy-full-native.log`.

The author, `quality_status_review`, reread both final files through EOF:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/Features/Settings/SettingsPane.swift` | 541 | `e27310df336ec0068a781f18eba8a49ab508fc0dd9025311b55b410fc0bbe9ae` |
| `macOS/Tests/StorageLocalizationTests.swift` | 108 | `009a4ee86baaea1a5c4917db447c19de8944a91d22fc676b213cb65356d76fe7` |

Root reviewed the complete four-file change, active-locale projection and remaining use of the legacy distribution title in diagnostics. The tests cover English and French for both distribution modes, account requirements and both consent states. No further concrete defect was found within this scope.

This does not attest every AppModels semantic, an actual Privacy-screen UI check, complete interaction coverage, model behavior or full HIG compliance. No Core source changed and no model request was made.
