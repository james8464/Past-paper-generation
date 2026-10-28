# Bounded file-level implementation reviews

These records identify files actually read, not merely counted by a formatter or
inventory. A review with findings is not clearance. Later edits require review
against their new content. The initial coverage ledger still records pending
work; this document supplies provenance for these bounded reviews without
claiming the whole project has been examined.

## Native UI review

Read-only source: `d55b176697624798853f90712b46068f62d2cd34`.
Paths below are relative to `macOS/Keldin/`.

- `Application/AppCommands.swift`
- `Navigation/ContentView.swift`
- `Navigation/SidebarView.swift`
- `Features/Generation/GeneratorWorkspaceView.swift`
- `Features/Generation/FrenchAssessmentWorkspace.swift`
- `Features/Settings/SettingsPane.swift`
- `Features/Documents/JobHistoryView.swift`
- `Features/Onboarding/PaperCreationTips.swift`
- `Features/Benchmark/BenchmarkView.swift`
- `Features/Onboarding/WelcomeHelpViews.swift`
- `Components/SharedViews.swift`

The review covered action wiring, selected-language presentation, state ownership,
accessibility labels and persistence callers. It found:

1. The benchmark toolbar calls its coordinator directly, bypassing the
   application's busy/session guards used by the menu command.
2. Benchmark failures are stored but not displayed in the view. A verdict can
   obscure a later failure.
3. Removing a recent document updates the fallback list, but restart restores
   the document from job history. URL-based hiding must cover older duplicate
   records without deleting their history or PDFs, and a new generation at that
   URL must be able to appear again.
4. Finite dynamic strings in generation, history, quality and shared empty states
   bypass selected-locale resource lookup. Benchmark accessibility uses the
   system locale instead of the interface selection.
5. Benchmark verdict text still applies status colour to the whole headline.
   Use semantic text and a distinct status symbol; existing composited AppKit
   measurements are evidence about colours, not screenshot certification.

ApplicationCoordinator and quality-policy caller traces supported these findings;
they are not additional full-file reviews. A possible large-view split is a
maintainability suggestion, not a measured performance defect. This review does
not certify all Apple HIG sections or every interaction.

## Tooling review

Read-only source: `6005567fb9bfe4b34207c2f5363159c8a2d5012f`.
Paths below are relative to `tools/`.

- `aqa_accounting_calibration.py`
- `aqa_business_calibration.py`
- `ocr_economics_calibration.py`
- `ocr_computer_science_calibration.py`
- `difficulty_calibration.py`
- `coverage_matrix.py`
- `repository_hygiene.py`
- `release_compliance.py`
- `scaffold_generator_family.py`
- `validate_generator_migration.py`
- `build_supported_layout_masters.py`

Complete maintained code paths were read for entry points, validation, errors,
cleanup, units, serialization and reuse. Giant JSON data files and the complete
dependency tree were not included. Findings:

1. Accounting calibration uses the shared stimulus removed by V11, a literal
   wording count and obsolete two-quantitative-item assumptions. Candidate-visible
   source and declared demand metadata need a new explicit report policy.
2. Migration validation can return success when the registry is missing, corrupt
   or has no advertised families. Empty iteration must not stand for a pass.
3. Several variety checks hash full models including the seed. Identity variation
   does not demonstrate assessed-content variation. Name and compute the new
   exact-content measure explicitly; it is still not semantic novelty or
   difficulty calibration.
4. OCR Computer Science and AQA Economics PDF subprocesses remain unbounded after
   the earlier three-tool deadline fix.
5. Scaffold identifiers can produce invalid digit-leading Python imports, paper
   IDs can repeat, and the generated test checks callability rather than the
   promised fail-closed behaviour.
6. The dependency-bound check examines root requirements, not every editable
   project manifest. Narrow its claim or validate the additional declarations.
   No current installed-version failure was demonstrated.

Ordered basename/content fingerprints, integer bands and sequence inventories
are suitable shared helpers. Keep subject parsers, filename rules and report
policies separate. Preserve order and duplicate semantics rather than silently
changing historical fingerprints.

No additional actionable issue was identified in the reviewed coverage,
repository-hygiene or layout-master-builder code paths. That is a bounded static
finding, not a fresh execution result or qualification of their input data.

## Implementation and acceptance rules

Each claimed defect needs its own failing regression before the fix. Keep old
reports and PASS/HOLD evidence; changed calibration semantics need versioned
outputs, not rewritten historical successes. Record exact fixed-source gates in
the relevant package reviews. These source reviews themselves made no model
requests, accessed no credentials and established no teacher or learner evidence.

## Later complete-file review at ebf33f6

The following files were read completely at
`ebf33f615e1c34f4afaa8af596dd477fbc58b9a8`. Hashes identify that reviewed
checkpoint, not later clearance of edited files.

| File | SHA-256 at review |
| --- | --- |
| `macOS/Keldin/Domain/KeldinCreationContext.swift` | `cda923193b4c413badbe7076c47fdc10cf62376e692baf502e7f63a3b08ea956` |
| `macOS/Keldin/Application/AppCommands.swift` | `d3493ac63877aabb451f3bfc06a9389f9698bfd44c0903cde273b3aa5630f2bd` |
| `macOS/Keldin/Domain/WorkNotification.swift` | `c4675a8e5b3202a600c526ab212c513162133e356f1a7150946eb565b06e7c62` |
| `macOS/Keldin/Services/BackendClient.swift` | `37617d50cb0b178fb20745edbd1e978639304fac6c8cb0a3540a9358e968159e` |
| `macOS/Keldin/Application/AppConfiguration.swift` | `5467ca1aa79567353eee1683a8d812a3faa137b78b20e18f96b748f87409803c` |
| `tools/audit_coverage.py` | `ed66424637fbccd4b1c3572512908583a3a81593e65442d7c2c077e4b1baec67` |
| `tools/live_process.py` | `68e2c19850c9140a64957273ec504bb05ed3ffcc86c52b9b43a54cf8bd8d0a2e` |
| `tools/calibrate_student_responses.py` | `81efacf64efea96a9d02a1576e046b65976fcd219972b61a9bf958397a65df48` |

The native scope covered routing, modal/busy guards, selected-language finite
copy, raw error detail, persistence defaults, process/pipe ownership, decoding
and launch fallback. It found dropped malformed collection output, unreported
nonzero exits with empty stderr and incorrect implicit development-root depth.
`d52024e` fixes those findings, including the demonstrated CRLF splitting fault.
Ninety-four focused native tests pass. The existing strict byte-line decoder was
already correct; an initially suspected replacement-decoding flaw was disproved
by reading it and its existing embedded-invalid-UTF8 tests. No additional
actionable defect was identified in the other four native files within this
scope; this is not whole-app or HIG certification.

The tooling scope covered validation before side effects, ownership, cleanup,
error paths, repetition and maintainability. It found a deadline initialisation
outside the post-spawn cleanup guard. A fake clock interruption reproduced the
missing kill/reap. `8d5c675` fixes it, with 33 related cases passing. Review-ledger
hashes bind source and evidence bytes but do not authenticate a reviewer. The
secure dataset CLI's repeated validation is intentional boundary protection;
removing a repeated missing-input branch is optional cleanup, not a demonstrated
release fault. No other actionable defect was identified in those two tooling
files within this scope.

These records did not automatically promote ledger entries or claim the full
project has been semantically reviewed. The later final local gate passed 4,506
Python tests with two optional-notes skips and 224 native tests. The consolidated
acceptance record separates those gates from live-model and publication work.
