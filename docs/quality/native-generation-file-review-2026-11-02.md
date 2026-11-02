# Native generation and history file review

Internal engineering review, 2 November 2026. Codex read the three files below through EOF at `af914047`, then reviewed the complete eight-line coordinator repair committed as `d6230923960b84eecafe7d5bdd0506a0bb5d1403`. Final file hashes were checked after that commit. Related callers and tests were inspected where needed; they are outside this complete-file attestation.

| File | Lines | Final SHA-256 |
| --- | ---: | --- |
| `macOS/Keldin/State/ApplicationCoordinator.swift` | 2256 | `6ea92948482ce034ed97c3ecb6b54039310394f0be5a6ac3f693f32852fddf92` |
| `macOS/Keldin/State/GenerationCoordinator.swift` | 118 | `492806bf6cbe338101c9239d0cc197481f58458200a242e69130a989bbf50e58` |
| `macOS/Keldin/State/RecentDocumentStore.swift` | 365 | `d6ccf6dda4c103447d8afddccbde4e2f94355052198a9b38e4f38616e808f08e` |

## Finding and repair

A UK paper operation could exit zero without reporting a question paper and still be saved as completed. The publication method returned early for an empty collection, and the history coordinator accepted the empty artifact list. Private JSON alone or a source booklet alone also reached completed history. An older question paper already in Recents did not belong to that run and could not establish its success.

The process-client contract permits empty stdout followed by exit zero; it does not require a document or done event. Controlled native tests reproduced the resulting coordinator behaviour. No current production helper was observed generating a malformed or empty paper during this review.

UK completion now requires a current-run, file-URL `question_paper` with a PDF extension before publication. All 21 advertised UK component contracts declare that role, including the three AQA CS question banks. This adds no question-paper/mark-scheme pair requirement or fixed artifact count. Existing publication checks still handle missing or unreadable source files. The generic publisher's support-file behaviour is unchanged, as are the separate French manifest and publication guards.

Refusal uses the existing publication-error path, records failure instead of completion, and returns before the success-notification call. Private working files and older library documents are preserved.

## Checks

The new complete-path regression first failed with 17 assertions across four controlled outcomes: no events, done only, private JSON only, and a source PDF only. Each operation incorrectly reached completed history. The source-only case also created a public export without a question paper.

After repair, 149 focused native tests passed with strict concurrency checking and warnings treated as errors. The selected classes were `RunIsolationTests`, `CoordinatorTests`, `UKArtifactPublisherTests` and `FrenchLLMAssessmentTests`. A final two-method rerun passed after adding an explicit question-paper-only positive control. Other positive controls cover an Accounting Paper 2 pair, a CS question-bank pair and an Economics source-booklet route.

Fixtures use isolated UserDefaults, stub credentials and UUID temporary history/output folders. Notifications are disabled; no notification permission or delivery test was performed. Logs and result bundles remain in the author's ignored `macOS/build/logs/nov2-uk-empty-completion/` directory as `red`, `green` and `green-minimum`.

A separate quality-review agent reviewed the bounded guard and test change and reported no scoped correctness finding. That was an independent patch review, not a second complete-file reading of these three files.

## Review limits

The complete-file reading covered captured run ownership and late callbacks, cancellation and history-save failures, provider/configuration persistence, publication and document registration, bookmark handling, history loading, migration, quarantine and retention. No further concrete P1/P2 issue was established in those files. That result is not a guarantee that none remains.

This review does not establish live provider behaviour, model correctness, complete UI behaviour, Store permission behaviour or educational quality. No inference, paid request, canonical-app interaction or user-preference change was used. Only focused Debug native tests were run for this repair; full native, release-build and protected-CI acceptance belong to the later integrated source. The application and existing user history were not cleaned up or altered by this work.
