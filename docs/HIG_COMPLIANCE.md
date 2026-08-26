# macOS interaction and HIG compliance

## Information architecture

The main window is a resizable `NavigationSplitView`:

- the sidebar selects a subject and exam board;
- the content column owns the paper-creation task;
- the optional inspector exposes release evidence without obstructing the task.

The creation form uses native grouped `Form`, `Section`, `Picker`,
`LabeledContent`, `Toggle`, `ProgressView`, `Table`, `ContentUnavailableView`,
`SettingsLink`, and toolbar APIs. It does not simulate macOS controls with
custom cards or web-style navigation.

## Commands and state

- `⌘N`: start a new paper.
- `⌘↩`: create when the current configuration is valid.
- `⌘.`: cancel the active operation.
- `⌘,`: open the standard Settings scene.
- `⇧⌘H`: open Paper creator Help without colliding with macOS Help search.
- Sidebar and quality-inspector visibility are standard toolbar commands.
- The primary action occupies the primary toolbar position.
- Task blockers appear beside the affected controls and state the recovery
  action; disabled controls also expose accessibility help.

Progress is determinate whenever the backend provides a fraction, includes a
time estimate when available, and can be cancelled. A spinner is used only when
progress is genuinely indeterminate. VoiceOver receives one concise, frequently
updated progress element containing the stage, percentage, and remaining-time
estimate instead of reading the visual row piecemeal.

Apple MLX setup always starts from an explicit confirmation. Before downloading,
the backend checks Apple-silicon compatibility, its managed Python version, and
at least 8 GB of free model storage; failures use recovery copy rather than
package-manager instructions. Cancelling terminates the installer process group,
and a later retry starts from clean recovery state.

## Geometry and visual language

- System typography, semantic colours, SF Symbols, materials, separators, and
  native focus/hover states are preserved.
- Content uses standard form insets and table geometry rather than arbitrary
  radii or branded cards.
- The window has a practical 720 × 560 minimum and remains resizable; the
  system split view collapses navigation before document content is clipped.
- The sidebar defaults to 220 points and remains user-adjustable.
- The inspector is constrained to a readable 250–360-point range.
- Status never relies on colour alone; each state includes a symbol and text.
- Unavailable catalogue choices show the visible “Coming soon” status in
  addition to the clock symbol.
- Controls use native macOS hit regions, meeting the platform's recommended
  target sizes without invisible custom overlays.

## Settings

Settings use the app's `Settings` scene and a stable toolbar-style `TabView`.
Changes apply immediately, the selected pane persists, and the fixed-size
settings window disables inappropriate minimise/zoom controls. Task-local paper
and destination choices remain in the main creation flow.

AI Settings detects unified memory and presents one explicit Ollama
recommendation, its download/context footprint, and a direct use or download
action before the model picker. Selecting another model shows a symbol-and-text
warning that results may vary; colour is supplementary. The main creation form
repeats a compact recommendation state at the point of use.

## Onboarding and help

First-run onboarding remains short, optional, and available again from Help.
The detailed guide uses a native two-column `NavigationSplitView` with stable
topics for model choice, creation, quality review, privacy, troubleshooting, and
keyboard use. Instructions remain selectable, scrollable, keyboard accessible,
and paired with real app screenshots where a visual reference is useful.

The guide distinguishes layout preview from release output, local from hosted
AI, automated second-pass review from independent human review, and intended
demand from psychometrically established difficulty.

## File workflow

Generated artifacts appear in a native table with document title, timestamp,
and path. They can be opened, revealed in Finder, removed from Recents, or
dragged to Finder. The selected output folder remains visible in the task.

The Documents destination uses PDFKit with selectable text and native zoom,
plus Quick Look, Print, Export, and Reveal actions. History is stored as
versioned atomic JSON records and distinguishes completed, failed, cancelled,
interrupted, and missing-file jobs. Duplicate Configuration preserves a seed;
Create Again with New Questions deliberately chooses a different seed.

The selected board, paper, library destination, provider/model configuration,
output bookmark, split-view visibility, settings pane, and inspector visibility
survive relaunch. macOS owns window-frame restoration; interrupted jobs are made
explicit in History and can be safely recreated without silently resuming a
partially consumed model stream.

## Accessibility verification

The source uses semantic labels, combined status rows, non-colour state labels,
and accessibility hints. Before distribution, the built app still requires
manual verification in:

- VoiceOver and Full Keyboard Access;
- Increase Contrast and Reduce Transparency;
- light and dark appearance;
- enlarged text and long localisation;
- minimum and large window sizes;
- generation, cancellation, failure, and completed-package states.

The current screenshot and accessibility-tree audit is recorded in
`docs/project-analysis/UI_AUDIT.md`; fresh captures are retained in
`docs/project-analysis/ui-audit-2026-08/` and the accepted workspace/settings
captures are bundled into the in-app tutorial.
