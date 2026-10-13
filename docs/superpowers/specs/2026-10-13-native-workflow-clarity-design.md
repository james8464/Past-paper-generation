# Native workflow clarity — design

## Intent

Make PaperCreator's default macOS journey feel calm and direct: choose an available paper, create a non-official draft, then inspect the output and its qualification limits. Preserve every existing route, saved selection, package format and generation rule. This is a usability increment, not a claim that the app meets every HIG criterion or that all papers match official examinations.

## Navigation

The sidebar shows available A-level boards by default. Search expands matching subjects and may reveal planned boards, labelled "Coming soon", so they remain discoverable without dominating ordinary navigation. Clearing search restores saved disclosure state. Favorites and recent configurations remain visible and function as before. France NSI, Documents, History and Benchmark remain first-class destinations.

## French written-paper workspace

The first screen exposes only the essential task: a short non-official identity and exam summary, reference readiness with its recovery action, local-model readiness, print size, and Create a draft. Output location and interface language live under More options. Reference deletion and the official-rules/help links live under References and privacy. Teacher review stays directly discoverable after creation and remains possible for retained packages. Reference setup remains a visible action whenever missing; an available corpus must not be described as proving coverage or rights. If Ollama is unchecked, stopped, absent or lacks the selected model, show the precise blocker and an available recovery action.

Use native SwiftUI Form, DisclosureGroup, system typography and symbols, standard toolbar and menu commands, semantic color, accessible labels and focus behavior. Do not replace system components with decorative cards or custom chrome. A disabled Create action has a nearby, actionable explanation. Running state shows progress and cancellation; completion remains explicitly a draft requiring human review.

## Quality boundary

Presentation must distinguish engineering checks, official-paper fidelity and teacher/learner validation. Model choice does not imply equivalent quality. The deterministic package validators remain fail-closed for every model and older UK/French replay; no static page-count target or filler is introduced. Paper-fidelity improvements are a separate versioned source task with official-source comparison and human gates.

## Verification

Test ready-only default navigation and search discoverability of planned boards, saved selection/replay, French reference-ready/missing presentation and disabled-action explanation. Build and run macOS unit/accessibility tests in a clean worktree, inspect the current Debug app at wide and compact window sizes, run backend regression tests, and review the diff before a protected PR. A screenshot review alone does not prove VoiceOver, keyboard or full HIG compliance.
