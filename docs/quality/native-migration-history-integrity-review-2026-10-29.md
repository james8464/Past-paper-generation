# Migration and history integrity review, 29 October 2026

Two source-confirmed storage defects were addressed against main `639643600336767b713c05494c56899dcf1b7467`. This work does not establish whole-app correctness, paper quality or external approval. Graphify queries preceded the review. Both production files listed below were read completely, including the final changes.

## Artifact relocation

The importer preserves an existing destination file when its relative name collides with an older file. Previously, the root-level relocation map could still redirect the older history entry to that different destination, retaining the old artifact ID and provenance.

Relocation now requires matching readable regular-file bytes. A successful comparison records the artifact ID, source path, destination path and destination SHA-256 in isolated application preferences. If the original subsequently disappears, relocation requires that exact saved proof and matching current destination bytes. A root mapping alone does not establish a verified copy. Missing proof, changed bytes, denied reads and unsupported file types retain the original pointer; they do not overwrite either file or grant broader access.

Independent second-pass review found a stale-proof case in the first implementation: after matching A/A, an observed source change to B refused relocation but left the earlier proof, which could become usable again if B disappeared. The final helper revokes a saved proof on verification failure. Tests cover changed bytes, denied reads and symbolic links on both sides, followed by disappearance of the original. Fresh matching files can establish a new proof. Filesystem attributes are read afresh so a replaced link cannot reuse an earlier regular-file classification.

This prevents the tested future substitutions. It cannot retrospectively identify a history entry that an older installation already redirected incorrectly when no original identity evidence remains. The proof also does not certify the content or mark a paper as reviewed. No model-cache files are scanned or hashed by these tests.

## History file identity

History loading previously trusted the decoded UUID without checking the filename. A valid record saved under another name could reappear after removal, since removal targets `<UUID>.json`. A running duplicate could also rewrite a canonical peer during startup migration.

After structural decoding and supported-schema validation, loading now requires the exact filename produced by the history writer. A mismatch raises `RecentDocumentStoreError.noncanonicalFileName` before that record's migration writes. The original JSON is kept, the previous in-memory snapshot remains available, and the valid file is not moved to quarantine. Corrupt JSON and unsupported-schema quarantine behaviour is unchanged. The change deliberately fails closed instead of guessing which duplicate to rename or overwrite.

The current error uses the operating system's localised invalid-filename description. Selected-app-language coverage for that inner diagnostic has not been established. Possible future application-owned copy is: "A saved history filename no longer matches its record. The file was kept unchanged. Restore its original name, then try again." A French equivalent is: "Le nom d’un fichier d’historique ne correspond plus à son enregistrement. Le fichier a été conservé sans modification. Rétablissez son nom d’origine, puis réessayez." These suggestions are not claims about implemented translations.

## Evidence

All regression data used temporary directories and isolated preferences. The reviewing agent did not modify a user's history, documents, credentials or models, and did not invoke app UI. Only focused native test builds were run.

| Retained log under `tmp/` | Result |
| --- | --- |
| `migration-history-identity-red.log` | Four tests, nine expected assertion failures before the fixes. |
| `migration-history-identity-green.log` | 70 tests passed; superseded by the independently identified stale-proof case. |
| `migration-copy-proof-revocation-red.log` | One table-driven test, four assertion failures covering proof reuse and a replaced source link. |
| `migration-history-identity-final-green.log` | 72 tests passed with zero failures. |

The final focused run includes `MigrationTests`, `HistoryStorageTests`, `HistoryDeletionTests` and `CoordinatorTests`. It covers collision preservation, verified and unverified missing originals, revocation/reverification, read failures, link rejection, noncanonical record names, canonical-peer preservation, record snapshots, existing retention/removal behaviour and existing schema/quarantine controls. Earlier positive relocation fixtures were corrected to contain an actual matching original rather than treating an unverified missing original as proof of a copy.

This focused result is not the final release test matrix. The parent agent owns subsequent UI changes, full native/Python suites, signed builds and publication checks.

## Reviewed source hashes

| Complete production file | SHA-256 |
| --- | --- |
| `macOS/Keldin/Application/KeldinMigration.swift` | `0066398df6d5edf67696aa78fa5200240b303cecd943c353079a6d1f9719f307` |
| `macOS/Keldin/State/RecentDocumentStore.swift` | `5393450bea45578cdd35466177e8524a6694c049b4e58e0e7dc5d5faa12ffe6f` |

Regression file hashes identify the exercised revisions; they are not blanket semantic review attestations for every test in those files.

| Regression file | SHA-256 |
| --- | --- |
| `macOS/Tests/MigrationTests.swift` | `e3cfb8c956c3b0ed131f4a98a1cb4330d3fb941b1b797c0495a4efeaeef0730b` |
| `macOS/Tests/HistoryStorageTests.swift` | `95b6806a4ecb075b26f7eeb1e8fee3da1d847c839162d188a840fd3f7a6b2f9c` |
