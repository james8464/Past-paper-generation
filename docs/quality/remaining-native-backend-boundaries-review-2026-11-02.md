# Remaining native and backend boundary reviews, 2 November 2026

## Scope and attribution

This consolidates 15 exact source identities at `e4649b83`. Each reviewer read the stated file through EOF or reviewed the explicitly identified final delta. Consolidation and hash checks are not additional independent full-file reviews. Dependencies and tests were traced selectively unless a row says otherwise.

| Repository path | Lines | Internal reviewer and coverage | SHA-256 |
| --- | ---: | --- | --- |
| `macOS/Keldin/Application/AppConfiguration.swift` | 141 | `quality_status_review`: EOF; `root`: EOF and final comment-only correction | `5bc4d204ce39f310a44396340f96966a08e6fdd8217eaa900328fa9bdf40420e` |
| `macOS/Keldin/Components/SharedViews.swift` | 89 | `quality_status_review`: EOF | `828e4ec018f2911aa840515f26c89bb0aac98f1f2ada4bee668a17973302fdfa` |
| `macOS/Keldin/Features/Settings/HostedModelCandidatesView.swift` | 21 | `quality_status_review`: EOF | `1cbbdad53c0b505c64714b4be0f9aabd0fbe2b658eb323a91428279dbcb3463c` |
| `macOS/Keldin/State/BenchmarkCoordinator.swift` | 108 | `release_gap_audit`: EOF | `5eddcc18bbea3fd16c9e53ec82f24b36ef969a57550a717d33487dae532b2b77` |
| `macOS/Keldin/State/CatalogStore.swift` | 181 | `release_gap_audit`: EOF | `77d439e55983ec3eba78e58940b44398500927d6dffed46f4a18730b9996f010` |
| `macOS/Keldin/Domain/AssessmentBundleExporter.swift` | 28 | `french_run23_review`: EOF | `02ebc95c6b5a67b42ce3a0a9fa542b8eace0777be4a172798e8a9d42498c5b2e` |
| `macOS/Keldin/Services/AppleIntelligenceAvailability.swift` | 94 | `french_run23_review`: EOF | `e0cb71870cc61ecf7defd162c5a1f92580a0cd20149776c7bbc9306a8f9914e1` |
| `Backend/Core/candidate_paths.py` | 523 | `release_gap_audit`: EOF | `1ac18771b8b25e1c60aa7593ceb20899d77153649a899ec9686379a2ac7b19d0` |
| `Backend/Core/board_profiles.py` | 72 | `release_gap_audit`: EOF | `d6847e666e25ed022769c764c541d10d1fd75d3bba34b36d9b25733ebda84305` |
| `Backend/Core/branding.py` | 5 | `release_gap_audit`: EOF | `3b1f74e025c63e623e06740af1de3278a30941b72fa65eacae5ae6fc1c6f3f35` |
| `Backend/Core/assessment_prompts.py` | 634 | `french_run23_review`: EOF | `d9a8b444b7387b4b20d1c72a809ef119354fbedbb5c31f1906eb022d648c10cc` |
| `Backend/Core/exam_blueprints.py` | 634 | `french_run23_review`: EOF | `d72643a90414b365c63698822d3e426ab9000ae790ae7de93bd4fbd6831b76a9` |
| `Backend/Core/cli.py` | 304 | `root`: EOF | `104d7192da5493f66190ae05ce4b27066f49775fffb9980839246362f025c650` |
| `Backend/Core/benchmark.py` | 732 | `root`: prior 723-line EOF plus complete 11-line fix delta, not a fresh final EOF reread | `ff719ab1a3ee185aaa75523910f3835fa6e1a362d84cf8c4d69fd675e7d4bb54` |
| `tests/test_benchmark_duration.py` | 89 | `root`: EOF; `release_gap_audit`: complete fix/test diff review | `427675c7ab092c04eb23101b2762b01d2cb56ed87682681f108764616a568464` |

## Findings and repair

The benchmark accepted infinite CLI durations, so its elapsed-time loop could not finish normally. The repair rejects NaN and either infinity before resolving an output path, creating directories, allocating probe data or contacting services. Finite durations retain their default, fractional values and one-second minimum. Four non-finite regressions failed safely before work under the original code; five finite controls remained valid. The final focused selection passed 13 tests using fake clocks and measurements. Independent source/test review found no further concrete issue in that fix. These are controlled software tests, not Mac or model performance measurements.

AppConfiguration's comment now reflects deferred startup import: paths are constructed before copying, and conflicting work remains guarded. This correction changes no behavior.

The remaining reviewed boundaries yielded no further confirmed P1/P2 in their stated scope. Native reviews cover defaults, document-action ownership, catalogue persistence, benchmark sessions, provider candidate bindings and helper availability handling. AssessmentBundleExporter had no production caller in the inspected search; its review does not establish executed export acceptance.

Backend reviews cover legal candidate-answer paths, leaf membership and mark totals, per-path timing and objective budgets, correlated reference comparison, board identifier normalization, shared branding, request guidance and blueprint contracts. Candidate paths are answer-selection topology, not filesystem paths. Board profiles are trusted repository resources; nested dictionaries are not deeply immutable, and this review does not certify hostile resource replacement. Generated objective budgets describe existing design policies, not measured learner demand or annual board targets.

## Limits

Prompt instructions cannot ensure model obedience, novelty, answer correctness or appropriate depth. Author/reviewer metadata is not a blind public-only projection; blind answer-key removal is a separate dependency. Legacy hydration establishes structural compatibility, not that generic marking guidance merits educational credit. Vendor model availability was not independently verified.

The source audits made no model, native UI, helper or network calls. Only the separately described fake benchmark regression tests were executed for the repair; no additional tests ran during evidence consolidation. This adds no paper-quality, teacher, learner, curriculum-equivalence, privacy, security, rights, runtime, accessibility or whole-HIG certification. No whole-project completion or absence-of-all-bugs claim is made. Unread dependencies and other audit rows remain outside these 15 attestations.
