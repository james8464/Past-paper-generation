# Native Workflow Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce default macOS navigation and French NSI creation to the essentials without losing recovery, review or legacy behavior.

**Architecture:** Keep catalog filtering in `CatalogStore`; use native SwiftUI disclosures in the existing sidebar and French workspace. No backend format or generation changes.

**Tech Stack:** SwiftUI, XCTest, macOS 15+, Python regression suite.

**Spec:** `docs/superpowers/specs/2026-10-13-native-workflow-clarity-design.md`

## Global Constraints

- Keep all currently available UK boards, French NSI, Documents, History and Benchmark accessible.
- Preserve saved navigation, favorites, recents, French/UK package replay and strict generation gates.
- Keep the French non-official and human-review caveats visible at the point of use.
- Follow system controls, menu commands, accessibility labels and responsive layout.

## Review Focus

- A subject with only planned boards disappears at rest but reappears in a matching search.
- A subject with mixed readiness shows only available boards at rest.
- A stored selection of a planned board is not silently rewritten.
- Missing French references leave an obvious recovery action and blocker reason.
- The compact workspace remains usable without clipped or hidden Create/Cancel actions.

---

### Task 1: Focus the catalog sidebar

**Files:** `macOS/PaperCreator/State/CatalogStore.swift`, `macOS/Tests/CoordinatorTests.swift`

**Interfaces:** `filteredSubjects: [CatalogSubject]` keeps its existing API. Empty search selects ready boards; non-empty search retains matching planned boards.

- [ ] Add failing XCTest assertions for ready-only default and planned-board search.
- [ ] Run focused macOS test and observe the intended failure.
- [ ] Make the minimal catalog filter change.
- [ ] Run focused and full macOS tests; review/commit.

### Task 2: Focus French creation

**Files:** `macOS/PaperCreator/Features/Generation/FrenchAssessmentWorkspace.swift`, `macOS/Tests/AccessibilityTests.swift`

**Interfaces:** Keep `FrenchAssessmentWorkspace` entry point, `generateFrenchPaper(largePrint:)`, reference preparation/deletion, teacher review and localization.

- [ ] Add failing presentation/accessibility tests for missing/ready references, advanced options and compact layout.
- [ ] Run focused test and observe the intended failure.
- [ ] Rearrange the native form into essential and disclosure sections; retain recovery/status language.
- [ ] Run focused/full macOS tests, inspect the Debug app in wide/compact modes, and review/commit.

### Task 3: Integration and evidence

**Files:** UI audit note and tests only if observations demand a fix.

- [ ] Run full backend suite, macOS tests, Ruff, repository hygiene and Graphify update/inventory.
- [ ] Inspect the diff and obtain read-only review; fix findings test-first.
- [ ] Create protected PR, wait for Backend/macOS required checks, merge only after success, and fast-forward clean main.
- [ ] Record honest remaining HIG, paper-fidelity and external-review limits.
