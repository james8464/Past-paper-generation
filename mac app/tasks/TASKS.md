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
