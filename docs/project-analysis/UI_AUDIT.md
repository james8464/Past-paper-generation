# macOS UI audit

Date: 29 July 2026

## Scope

Combined UX and screenshot-level accessibility audit of the built macOS app’s
main paper-creation flow and its AI-unavailable state. The target is a
recognisably native, low-friction macOS workflow aligned with Apple’s current
guidance for sidebars, settings, toolbars, menus, and progress indicators.

## Step 1 — deterministic paper workspace

Health: **Good**

![Deterministic paper workspace](ui-audit/01-main-workspace.png)

Confirmed strengths:

- native `NavigationSplitView` hierarchy with disclosure rows for subjects and
  board choices beneath the selected subject;
- segmented paper picker is close to the object it changes;
- one clear primary action;
- output location is visible in the task rather than hidden in Settings;
- the generator mode, visual-review state, and unverified difficulty are
  expressed in text as well as colour;
- the empty recent-papers state explains what will appear;
- the sidebar does not place critical status at its bottom edge.

Risks and improvements made:

- “Visual calibration passed” overstated the evidence; it is now “Visual profile
  reviewed.”
- recent files previously disappeared between launches; metadata now persists
  and missing files can be removed from history.
- the action and status row could become crowded under large accessibility text;
  the window now has a practical minimum size, but enlarged-text and VoiceOver
  testing remain necessary.

## Step 2 — AI-assisted paper blocked on Ollama

Health: **Good**

![AI-assisted paper with exact blocker](ui-audit/02-ai-assisted-blocked.png)

Confirmed strengths:

- the primary action is disabled and its accessibility help states the exact
  blocker;
- the warning gives a plain-language recovery path;
- `Check Again`, `Get Ollama`, and `Settings` are available at the point of
  failure;
- local-vs-hosted generation is no longer implied for deterministic families;
- warning meaning is not conveyed by colour alone.

Risks:

- the orange evidence text is small and should receive a contrast check in both
  appearances;
- three recovery actions in one banner are defensible but should be tested with
  first-time users to confirm that “Settings” is understood as the hosted/model
  route.

## Step 3 — Settings

Health: **Source- and test-verified; screenshot blocked**

Opening Settings caused the Computer Use accessibility pipe to close before a
valid screenshot could be saved. This is an audit-tool blocker, not evidence of
an application crash, so no screenshot claim is made.

The implementation and native tests confirm:

- `⌘,` opens Settings through the app’s Settings scene;
- panes have stable sidebar navigation and a pane-specific window title;
- changes save immediately, with no redundant Save/Apply button;
- the last selected pane is restored;
- minimum/zoom controls are disabled for the fixed settings window;
- provider controls explain when the current generator is constrained and does
  not use AI.

## Apple HIG alignment

The changes follow the applicable official guidance:

- [Settings](https://developer.apple.com/design/human-interface-guidelines/settings):
  standard app-menu access, stable panes, immediate application, and task-local
  options kept out of Settings.
- [Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars):
  disclosure hierarchy, adaptive sidebar visibility, and no critical content
  stranded at the bottom.
- [Progress indicators](https://developer.apple.com/design/human-interface-guidelines/progress-indicators):
  determinate progress when available, stable progress updates, and cancellation.
- [Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos/):
  keyboard commands, resizable windows, native controls, menu commands, and
  familiar sidebar/detail structure.

## Evidence limits

Screenshots cannot establish complete accessibility compliance. Before release,
test VoiceOver order and announcements, Full Keyboard Access, reduced motion,
Increase Contrast, light/dark appearances, 200% text, smallest supported window,
and long localised strings. The generation-success and cancellation states are
covered by code/tests but were not recaptured in this screenshot run.
