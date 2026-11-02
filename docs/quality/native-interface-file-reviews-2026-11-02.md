# Native interface file reviews, 2 November 2026

## Review boundary

This records 20 completed full-file implementation reviews from the internal review batch at `f90d4115791caa632e7742379b584551a9138eea`, plus a full-file review of NativeVisualStyle. All source identities below were checked against candidate `74e68cf9cfd499d749d60097e0b81c33a70d599f`. Its production files are unchanged from the verified earlier candidate `fa9d0f4674c32582be1f7c6648bc0d9660d20869`. Eighteen batch files are unchanged. ContentView and WelcomeHelpViews were freshly reread through EOF after the compact-sidebar and Help-route changes; NativeVisualStyle was also read through EOF. The reviewer column identifies who completed each review, rather than attributing every file to one reader.

The review covers navigation and scene actions, state ownership, busy and cancellation routes, generation guidance, request construction, saved evidence presentation and error-copy boundaries. Dependencies were traced selectively; those inspections do not certify complete dependency files. The review found the compact-sidebar refusal described in the separate compact-navigation record. The candidate repairs its binding and the obsolete Ollama Help route. No other concrete P1/P2 issue was identified within these file reviews.

## Reviewed source identities

| Repository path | Lines through EOF | Internal reviewer | SHA-256 |
| --- | ---: | --- | --- |
| `macOS/Keldin/Navigation/ContentView.swift` | 133 | `quality_status_review` | `0f7d97133dd4448cd95ba78a7c3ded99e8d26312024a2a71e2a1a0841733bf3b` |
| `macOS/Keldin/Navigation/SidebarView.swift` | 184 | `quality_status_review` | `e6ae4d82f0fc39c6490f27f891930a287a4700feac4d4950ddec1a4cd47b36a8` |
| `macOS/Keldin/Application/AppCommands.swift` | 226 | `quality_status_review` | `a7bf9ebe5d050f543f034442959ff65fbcc7e49d2ab3cdb2428d0d254755811c` |
| `macOS/Keldin/Features/Onboarding/WelcomeHelpViews.swift` | 479 | `quality_status_review` | `d198144fec061313f6eac38ef63f0b747ee62c3c19ddff962780c4dce79228c0` |
| `macOS/Keldin/Features/Onboarding/KeldinCreationTips.swift` | 34 | `quality_status_review` | `51af5767b42d0ad36f31ffcdf4ba42cb59e69d95a0fc51efe65fc370d3c2db4b` |
| `macOS/Keldin/Features/Generation/GeneratorWorkspaceView.swift` | 571 | `release_gap_audit` | `c4a8e348c749868f87d44b597785bb669bc1505ab672bf3c7edd682a441df9c4` |
| `macOS/Keldin/Features/Generation/FrenchAssessmentWorkspace.swift` | 283 | `release_gap_audit` | `e28f1a94f13b7e72d00ce75f549439c0892310e918c7438e1fc3cfb32d5f29cd` |
| `macOS/Keldin/Features/Generation/GenerationGuidanceViews.swift` | 106 | `release_gap_audit` | `83be520e644939789b5a272684237497c05387625593d089e4f237fc33b0ed7b` |
| `macOS/Keldin/Features/Generation/GenerationProgress.swift` | 55 | `release_gap_audit` | `3aba1f70520fed5aa30e7b05168121859cb578651315028e012d5194e584f709` |
| `macOS/Keldin/Features/Benchmark/BenchmarkView.swift` | 337 | `release_gap_audit` | `f3f2f37868faad7862ee1328d2ade7dc8453e74eefe0fdc569d1406f2325b4f8` |
| `macOS/Keldin/Domain/AppModels.swift` | 1372 | `french_run23_review` | `bd58dc448a681d747979fc2cc36078243294c3ef539e7a91e7f40668db7c1e33` |
| `macOS/Keldin/Domain/FrenchAssessmentRequest.swift` | 99 | `french_run23_review` | `cd5902a70a25b07f4fece593a08478b28e8bdb55ab2344972a9b1e031d0248f1` |
| `macOS/Keldin/Domain/FrenchLLMAssessmentRequest.swift` | 126 | `french_run23_review` | `7168f87ab1743f9adc5bfaf25c48bba7ba22c9da42ee16c8d879ad6b83e1a6ba` |
| `macOS/Keldin/Domain/FrenchReviewRequest.swift` | 77 | `french_run23_review` | `532e1768bee999223254533fcba64c6b3354739a54ac1d9b678b9ee0478e6b65` |
| `macOS/Keldin/Domain/GenerationPresentation.swift` | 168 | `root` | `9d0769b07ae5adc28486fc14befd8b33ec89836db4c2b91395ba81eb80e3ac54` |
| `macOS/Keldin/Domain/InterfaceText.swift` | 14 | `root` | `532a9b7d1b8a4c4a21a0378b3d33f061ad7ae6caba7fabffe8538ddc333fbed5` |
| `macOS/Keldin/Domain/NativeInterfaceCopy.swift` | 122 | `root` | `5655bc4347b162c48b198092a20e46382e1d32c69847466e0241c738de1c96e0` |
| `macOS/Keldin/Domain/PaperQualityGuidance.swift` | 124 | `root` | `91da407db4f54b368c7768bd72ca0474617f45b587688c349e32535f1385a753` |
| `macOS/Keldin/Domain/FrenchDraftQualityReport.swift` | 96 | `root` | `f404927bdbe7a7db173b1cb649ff23b1ddd675c5c1ae9a9dc1eab2e1a5275ca6` |
| `macOS/Keldin/Domain/HostedModelCandidate.swift` | 23 | `root` | `3e8699c052ea0ae0a81648bc4df4300bb622bf76c3e7179c807bfde11a7b4225` |
| `macOS/Keldin/Components/NativeVisualStyle.swift` | 65 | `quality_status_review` | `7cbf8c18594203138d027bd182d26e2768ac73e963ac07cbf25d8e341e3c97e8` |

## Findings and limits

- ContentView, SidebarView and AppCommands were checked for actual navigation routes and focused scene actions. The compact binding now honours explicit stored sidebar choices while keeping the initial automatic compact layout collapsed. Native geometry acceptance remains separate evidence.
- Welcome and Help views and creation tips distinguish previews, memory-fit suggestions and unqualified paper output. The Help instruction now names Settings > AI > Check Again, including its French translation. Some remaining Help wording is less complete than the provider settings, and the welcome recommendation is less explicit about memory fit. These are minor copy limitations, not paper-quality approval.
- The generation and benchmark view reviews found no further concrete P1/P2 issue. They do not establish live generation quality or measured model performance.
- Request-domain reviews cover native construction and field handling. Backend curriculum, reference, semantic and PDF validation remain separate responsibilities.
- Saved quality reports, model advice and vendor candidates present bounded evidence or configuration choices. They do not independently qualify arbitrary edited packages, vendor availability, output quality or completion times.

These are internal engineering reviews, not teacher or learner evidence. They add no runtime, model, PDF-content, rights, external-policy or whole-HIG certification. No accessibility testing was performed. Previously recorded raw-English Privacy values remain a localization limitation outside this batch. No whole-project audit completion or absence-of-all-bugs claim is made. Only the exact 21 source identities above receive ledger attestations; unread tests, resources and dependencies remain outside this record.
