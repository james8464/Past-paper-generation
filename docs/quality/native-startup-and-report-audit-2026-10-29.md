# Native startup and report audit

## Review scope

The application-layer review read every line of AppCommands.swift,
AppConfiguration.swift, KeldinApp.swift, KeldinMigration.swift and
MainWindowRouting.swift at merged PR124. It traced command destinations,
focused creation/document ownership, startup migration, failure presentation,
default storage and the relevant tests. MainWindowRouting already has an
exact-byte review in the ledger. This review does not certify the rest of the
project or every user interaction.

| Application file | Disposition |
| --- | --- |
| AppCommands.swift | Creation follows the focused workspace, including French print size. Document commands use the selected document. Unavailable contexts are disabled. No new defect found. |
| AppConfiguration.swift | Store output and model storage remain app-owned. Direct distribution retains its Downloads default. Preference and secret keys remain stable. No new defect found. |
| KeldinApp.swift | Found raw English startup migration-failure guidance. It now resolves through the saved interface language. Migration results and retry behaviour are unchanged. |
| KeldinMigration.swift | Reviewed current storage, migration containment, idempotence and surfaced failures. Store mode does not silently import the former app's data domain. No new defect found. |

The revised KeldinApp branch was reviewed after the copy fix. The source/catalogue
regression first failed on the raw assignment and then passed for English and
French. These are internal engineering reviews, not teacher or learner reviews.

## Malformed report counters

A separate focused domain review found an unchecked sum of five nonnegative
authoring-provenance counters. A malformed Int.max value could trap while opening
a report. A standalone harness compiled the complete production AppModels.swift
with localisation-only stubs and reproduced SIGTRAP. The correction consumes a
remaining total instead of adding counters. Four malformed maximum-count cases
now return unknown; a consistent maximum total remains readable. Two native
regressions cover these boundaries. This focused check is not an attestation
that every AppModels field has been audited.

## Native test signing

A default personal-development test run compiled but could not load its test
bundle: the host had personal team Z29CKRV8C9 while the bundle was ad hoc. The
project specification and checked-in Xcode project now give the test target the
same personal team and automatic signing as its host. No sandbox, hardened
runtime, library-validation or application entitlement was relaxed. A regression
checks Debug and Release settings for both targets. Earlier failed and
interrupted local attempts are retained; they are not passing evidence.

## Limits

The live six-paper campaign uses the unchanged PR124 frozen helper. These native
changes do not alter French questions, answer keys, marks, model scheduling or
the paper-quality rules. Passing static checks or tests does not establish
complete paper quality, learner timing, App Store approval or full HIG coverage.
