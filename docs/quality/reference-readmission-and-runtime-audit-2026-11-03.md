# Reference re-admission and runtime review

## Reproduced reference defect

A failed re-import could leave a previously indexed French source eligible for
retrieval. The importer recorded the failure but retained every registered ID,
including sources that no longer passed their current hash, rights, URL or split
checks. Changing a reference to holdout also exposed a duplicate-alias path:
its immutable metadata conflict failed admission, but a reference copy could be
indexed successfully without the failed holdout participating in deduplication.

Eight regression cases failed before the repair. Independent review then found
an additional case: a rejected holdout with no known byte identity could not be
distinguished from an admitted reference copy. That negative failed separately;
an unrelated valid-source control passed.

The importer now retains only successfully admitted, non-excluded IDs. Holdout
quarantine considers pinned hashes, previous indexed hashes and checked PDF
bytes even when later admission fails. If a registered holdout has no known
identity, reference retrieval is conservatively blocked for that import. The
manifest lists unresolved holdouts and quarantined reference IDs; these are not
claims that every quarantined document is a proven duplicate. Known holdout
hashes do not exclude unrelated valid sources.

A separate negative also reproduced conflicting duplicate register IDs: one
successful row must not override a rejected row for the same ID. Failed IDs are
now excluded even if an earlier row in the import succeeded, and each reported
`indexed` flag reflects final eligibility.

Immutable `ReferenceIndex.add` checks and failure reporting are unchanged. Local
PDFs are preserved. A corrected register can be imported again to restore eligible
references. The tests cover direct rejection, duplicate aliases, both register
orders, unresolved identity, recovery and an unrelated-source positive control.
All fixtures are app-owned PDFs created in temporary directories. No official
PDF, download, model request or real user corpus was used for this reproduction.

## Review scope

The following full-file implementation reviews were completed internally. For
the repaired corpus file, coverage comprises the original complete file followed
by every final production delta and its tail. Other file bytes are unchanged from
the reviewed main165 base. No new P1/P2 finding was established in the other six
files within this scope.

| File | Lines | SHA256 |
| --- | ---: | --- |
| `Backend/Core/computer_science_authoring.py` | 287 | `ef45d9cf779cef3a27f17d813681c3115fa9be91b427714abd5b5a3670523f00` |
| `Backend/Core/exam_cover.py` | 589 | `af262069558928777e832fe4f021da131e0d170dfb0b3392af0c57a1d3789a2f` |
| `Backend/Core/exam_pages.py` | 412 | `d38aa5051bab598ef9ef0c1ab9010e905c69d67babfea6bb9cba7838974d8350` |
| `Backend/Core/france/generation_budget.py` | 72 | `c6152fbed81540a64823ba66f8b3399eee60ab5a04d509300f3bbef751e9136d` |
| `Backend/Core/france/corpus.py` | 534 | `df3b1211f87cdd52f01707a19fd992277443caa30042f58adcf220568aad9309` |
| `macOS/AppleIntelligenceHelper/Package.swift` | 12 | `16115d5e89ed69f961590bd306e3e7e01674387c087611e6ec9ef00c3328d24a` |
| `macOS/AppleIntelligenceHelper/Sources/KeldinAppleIntelligence/Main.swift` | 156 | `e11270e7da8fd4930edec53eb28632ce04a828dec09c20de6da738ceef653d69` |

`quality_status_review` reviewed authoring, covers and page furniture, including
identity binding, declared solver inputs and selective SQL source contracts.
`release_gap_audit` reviewed corpus admission and budget reservation, identified
the re-admission defect and independently cleared the final production repair.
`french_run23_review` reviewed the Apple helper and package, plus its protocol and
protocol tests. That review checked request/output bounds, capability and context
admission, single-request sessions and cooperative cancellation. Selective caller
and dependency inspection is not a full-file attestation of those dependencies.

## Verification and limits

The final corpus/scoped-reference group passed 30 tests. Python lint and maintained
format checks passed for the two changed files. Logs are
`tmp/nov3-french-readmission-red.log`,
`tmp/nov3-french-readmission-unresolved-red.log` and
`tmp/nov3-french-readmission-duplicate-red.log`; the final passing result is in
`tmp/nov3-french-readmission-scoped.log`.

Full-suite, packaged/native and protected checks remain release gates after the
production freeze. This source review does not qualify a model-authored paper,
prove provider cancellation latency, clear third-party rights or certify the
whole repository. Existing French and UK paper-quality holds remain unchanged.
