# Tasks

## Task IDs

1. swiftui-app
   Id: 1-swiftui-app
   Scope: Native SwiftUI app and Python JSON bridge
   Files: Sources app_backend.py tests README
   Note: Implemented SwiftUI shell, JSON backend bridge, tests; build/test pass with DEVELOPER_DIR
   Detail: tasks/details/1-swiftui-app.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T15:00:58Z
   Done by: CODEX
   Done at: 2026-05-12T15:12:01Z

2. app-error-hardening
   Id: 2-app-error-hardening
   Scope: Swift app backend error handling
   Files: PastPaperCreator/*.swift app_backend.py tests
   Note: Hardened backend/app error paths; pytest, smoke, and xcode tests pass
   Detail: tasks/details/2-app-error-hardening.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T16:19:44Z
   Done by: CODEX
   Done at: 2026-05-12T16:24:10Z

3. swift-code-quality
   Id: 3-swift-code-quality
   Scope: Swift code quality, portable defaults, backend constants
   Files: PastPaperCreator/*.swift ../app_bridge/*.py
   Note: Refactored SwiftUI files, centralized defaults, removed user-specific paths, pytest and xcode tests/build passed
   Detail: tasks/details/3-swift-code-quality.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T20:15:13Z
   Done by: CODEX
   Done at: 2026-05-12T20:28:37Z

4. adaptive-ui-polish
   Id: 4-adaptive-ui-polish
   Scope: Adaptive SwiftUI layout polish and native progress/empty states
   Files: PastPaperCreator/*.swift
   Note: Finished adaptive UI polish. Verified: make test, pytest backend tests, git diff --check after cleanup, and make build-app-store.
   Detail: tasks/details/4-adaptive-ui-polish.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T20:35:37Z
   Done by: CODEX
   Done at: 2026-05-12T20:37:04Z

5. backend-launch-hardening
   Id: 5-backend-launch-hardening
   Scope: Fix Xcode generation crash, harden backend launch errors, and consolidate launch configuration
   Files: PastPaperCreator/*.swift project.yml Makefile Tests/*.swift
   Note: Fixed direct/App Store signing split, hardened backend Python errors, added BackendClient launch test. Verified direct build/test, Python tests, dry-run generation, and App Store build.
   Detail: tasks/details/5-backend-launch-hardening.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T20:42:53Z
   Done by: CODEX
   Done at: 2026-05-12T20:48:45Z

6. generator-view-layout
   Id: 6-generator-view-layout
   Scope: Refine generator workspace hierarchy, spacing, and alignment
   Files: PastPaperCreator/GeneratorWorkspaceView.swift PastPaperCreator/SharedViews.swift PastPaperCreator/NativeVisualStyle.swift
   Note: Reworked generator workspace into a HIG-style full-width hierarchy: header, readiness, setup, activity, documents. Verified with Swift tests.
   Detail: tasks/details/6-generator-view-layout.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T20:53:50Z
   Done by: CODEX
   Done at: 2026-05-12T20:57:52Z

7. benchmark-expanded-measures
   Id: 7-benchmark-expanded-measures
   Scope: Add broader diagnostic benchmark suitability measures
   Files: app_bridge/benchmark.py mac app/PastPaperCreator/AppModels.swift mac app/PastPaperCreator/BenchmarkView.swift mac app/Tests/AppTests.swift tests/test_app_backend.py
   Note: Added memory pressure/swap, output storage, small-file latency, network download, Ollama latency, PDF render throughput, thermal limit and power metrics with Swift decoding and charts.
   Detail: tasks/details/7-benchmark-expanded-measures.md
   Claimed by: CODEX
   Claimed at: 2026-05-12T21:00:44Z
   Done by: CODEX
   Done at: 2026-05-12T21:08:02Z

8. paper-render-polish
   Id: 8-paper-render-polish
   Scope: Improve generator render efficiency and visual paper fidelity
   Files: a-levels/economics/edexcel-a/generator/pastpapergen/render_pdf.py a-levels/computer-science/aqa/generator/cspapergen/render_pdf.py tests
   Note: Matched Edexcel question-paper bleed/crop boxes, tightened answer-frame geometry, cover details and mark-scheme page style; added render regression tests.
   Detail: tasks/details/8-paper-render-polish.md
   Claimed by: CODEX
   Claimed at: 2026-05-13T07:36:26Z
   Done by: CODEX
   Done at: 2026-05-13T08:24:18Z

9. graph-code-stimulus-variety
   Id: 9-graph-code-stimulus-variety
   Scope: Improve graph/table/diagram/code-block rendering and question variety
   Files: a-levels/economics/edexcel-a/generator/pastpapergen/generator.py a-levels/economics/edexcel-a/generator/pastpapergen/render_pdf.py a-levels/economics/edexcel-a/generator/tests a-levels/computer-science/aqa/generator/cspapergen/question_bank.py a-levels/computer-science/aqa/generator/cspapergen/render_pdf.py a-levels/computer-science/aqa/generator/tests
   Note: Expanded economics Section A stimulus pools and CS Paper 2 visual question styles; improved graph/table/code/diagram rendering and added regression coverage.
   Detail: tasks/details/9-graph-code-stimulus-variety.md
   Claimed by: CODEX
   Claimed at: 2026-05-13T08:42:55Z
   Done by: CODEX
   Done at: 2026-05-13T09:26:35Z
